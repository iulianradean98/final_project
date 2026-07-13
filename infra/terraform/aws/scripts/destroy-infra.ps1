param(
    [string]$WorkingDirectory = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PlanFile = "destroy.tfplan",
    [string]$AwsRegion = "eu-central-1",
    [string]$ClusterName = "recipe-rescue-shared-eks",
    [string[]]$ApplicationNamespaces = @(
        "recipe-rescue-staging",
        "recipe-rescue-production",
        "recipe-rescue-blue",
        "recipe-rescue-green",
        "recipe-rescue-production-data"
    ),
    [string[]]$ArgoApplications = @(
        "recipe-rescue-root",
        "recipe-rescue-staging",
        "recipe-rescue-production-data",
        "recipe-rescue-production",
        "recipe-rescue-production-blue",
        "recipe-rescue-production-green"
    ),
    [int]$CleanupWaitSeconds = 600,
    [switch]$SkipKubernetesCleanup,
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"

function Assert-CommandExists {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found on PATH. Open a new terminal after installation or add it to PATH."
    }
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
    }
}

function Get-TerraformOutput {
    param([string]$Name)

    $value = & terraform output -raw $Name 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($value)) {
        return $value.Trim()
    }

    return $null
}

function Wait-ForCondition {
    param(
        [string]$Description,
        [int]$TimeoutSeconds,
        [scriptblock]$Condition
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        if (& $Condition) {
            Write-Host "OK: $Description"
            return
        }

        Write-Host "Waiting: $Description"
        Start-Sleep -Seconds 15
    }

    throw "Timed out waiting for: $Description"
}

function Test-EksClusterExists {
    param(
        [string]$Name,
        [string]$Region
    )

    & aws eks describe-cluster --name $Name --region $Region --query "cluster.status" --output text 1>$null 2>$null
    return $LASTEXITCODE -eq 0
}

function Test-KubectlReady {
    & kubectl get namespace default 1>$null 2>$null
    return $LASTEXITCODE -eq 0
}

function Remove-RecipeRescueKubernetesResources {
    param(
        [string]$Name,
        [string]$Region,
        [string[]]$Namespaces,
        [string[]]$Applications,
        [int]$WaitSeconds
    )

    if (-not (Test-EksClusterExists -Name $Name -Region $Region)) {
        Write-Host "EKS cluster $Name was not found. Skipping Kubernetes cleanup."
        return
    }

    Write-Host "Updating kubeconfig for $Name in $Region..."
    Invoke-Checked "aws" @("eks", "update-kubeconfig", "--region", $Region, "--name", $Name)

    if (-not (Test-KubectlReady)) {
        throw "kubectl cannot access the cluster. Check AWS credentials, kubeconfig, and EKS permissions."
    }

    Write-Host "Deleting ArgoCD Applications so ArgoCD does not recreate app namespaces..."
    & kubectl delete application -n argocd @Applications --ignore-not-found=true --timeout=60s
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ArgoCD Application cleanup was skipped or partially failed. Continuing with namespace cleanup."
    }

    foreach ($namespace in $Namespaces) {
        & kubectl get namespace $namespace 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) {
            continue
        }

        Write-Host "Deleting LoadBalancer services in namespace $namespace..."
        $servicesJson = & kubectl get service -n $namespace -o json 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($servicesJson)) {
            $services = ($servicesJson | ConvertFrom-Json).items | Where-Object { $_.spec.type -eq "LoadBalancer" }
            foreach ($service in $services) {
                & kubectl delete service -n $namespace $service.metadata.name --ignore-not-found=true --timeout=60s
                if ($LASTEXITCODE -ne 0) {
                    throw "Failed to delete LoadBalancer service $namespace/$($service.metadata.name)."
                }
            }
        }
    }

    Wait-ForCondition "Kubernetes LoadBalancer services are removed" $WaitSeconds {
        $serviceJson = & kubectl get service -A -o json 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($serviceJson)) {
            return $true
        }

        $loadBalancers = ($serviceJson | ConvertFrom-Json).items | Where-Object { $_.spec.type -eq "LoadBalancer" }
        return @($loadBalancers).Count -eq 0
    }

    Write-Host "Deleting application namespaces..."
    & kubectl delete namespace @Namespaces --ignore-not-found=true --timeout=120s
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Namespace deletion is still in progress. Terraform can continue once LoadBalancer services are gone."
    }
}

function Wait-ForAwsVpcCleanup {
    param(
        [string]$VpcId,
        [string]$Region,
        [int]$WaitSeconds
    )

    if ([string]::IsNullOrWhiteSpace($VpcId)) {
        Write-Host "No VPC ID found in Terraform output. Skipping AWS VPC pre-destroy wait."
        return
    }

    Write-Host "Waiting for AWS load balancers and public mappings in VPC $VpcId to disappear..."

    Wait-ForCondition "AWS load balancers in $VpcId are removed" $WaitSeconds {
        $classic = & aws elb describe-load-balancers --region $Region --query "LoadBalancerDescriptions[?VPCId=='$VpcId'].LoadBalancerName" --output text 2>$null
        $v2 = & aws elbv2 describe-load-balancers --region $Region --query "LoadBalancers[?VpcId=='$VpcId'].LoadBalancerArn" --output text 2>$null

        return [string]::IsNullOrWhiteSpace($classic) -and [string]::IsNullOrWhiteSpace($v2)
    }

    Wait-ForCondition "non-NAT public IP mappings in $VpcId are removed" $WaitSeconds {
        $publicMappings = & aws ec2 describe-network-interfaces `
            --region $Region `
            --filters "Name=vpc-id,Values=$VpcId" `
            --query "NetworkInterfaces[?Association.PublicIp!=null && InterfaceType!='nat_gateway'].NetworkInterfaceId" `
            --output text 2>$null

        return [string]::IsNullOrWhiteSpace($publicMappings)
    }
}

Assert-CommandExists "terraform"
Assert-CommandExists "aws"

if (-not $SkipKubernetesCleanup) {
    Assert-CommandExists "kubectl"
}

Push-Location $WorkingDirectory
try {
    Write-Host "Recipe Rescue AWS destroy helper"
    Write-Host "Working directory: $WorkingDirectory"
    Write-Host "AWS region: $AwsRegion"
    Write-Host "EKS cluster: $ClusterName"
    Write-Host ""

    Write-Host "Checking AWS identity..."
    Invoke-Checked "aws" @("sts", "get-caller-identity", "--output", "table")

    Write-Host "Initializing Terraform..."
    Invoke-Checked "terraform" @("init")

    $vpcId = Get-TerraformOutput "vpc_id"
    $terraformClusterName = Get-TerraformOutput "cluster_name"
    if (-not [string]::IsNullOrWhiteSpace($terraformClusterName)) {
        $ClusterName = $terraformClusterName
    }

    if (-not $SkipKubernetesCleanup) {
        Remove-RecipeRescueKubernetesResources `
            -Name $ClusterName `
            -Region $AwsRegion `
            -Namespaces $ApplicationNamespaces `
            -Applications $ArgoApplications `
            -WaitSeconds $CleanupWaitSeconds

        Wait-ForAwsVpcCleanup -VpcId $vpcId -Region $AwsRegion -WaitSeconds $CleanupWaitSeconds
    }

    if (Test-Path $PlanFile) {
        Remove-Item $PlanFile -Force
    }

    Write-Host ""
    Write-Host "Creating Terraform destroy plan..."
    Invoke-Checked "terraform" @("plan", "-destroy", "-out=$PlanFile")

    if (-not $AutoApprove) {
        Write-Host ""
        Write-Host "Review the destroy plan above carefully."
        $confirmation = Read-Host "Type DESTROY to delete the Terraform-managed AWS infrastructure"

        if ($confirmation -ne "DESTROY") {
            Write-Host "Destroy cancelled. The plan file can be removed manually: $PlanFile"
            exit 0
        }
    }

    Write-Host "Applying Terraform destroy plan..."
    Invoke-Checked "terraform" @("apply", $PlanFile)

    Write-Host ""
    Write-Host "Destroy completed. Remaining Terraform state resources:"
    & terraform state list
}
finally {
    Pop-Location
}
