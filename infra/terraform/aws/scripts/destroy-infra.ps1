param(
    [string]$WorkingDirectory = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$PlanFile = "destroy.tfplan"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    throw "Terraform was not found on PATH. Open a new terminal after installation or add terraform.exe to PATH."
}

Push-Location $WorkingDirectory
try {
    Write-Host "Terraform destroy helper for Recipe Rescue AWS infrastructure"
    Write-Host "Working directory: $WorkingDirectory"
    Write-Host ""
    Write-Host "This will create a destroy plan first. Nothing is deleted until you confirm and apply the plan."
    Write-Host ""

    terraform init
    terraform plan -destroy -out="$PlanFile"

    Write-Host ""
    Write-Host "Review the destroy plan above carefully."
    $confirmation = Read-Host "Type DESTROY to delete the Terraform-managed AWS infrastructure"

    if ($confirmation -ne "DESTROY") {
        Write-Host "Destroy cancelled. The plan file can be removed manually: $PlanFile"
        exit 0
    }

    terraform apply "$PlanFile"
}
finally {
    Pop-Location
}
