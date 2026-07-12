# AWS EKS Terraform Infrastructure

This directory contains the first AWS infrastructure layer for Recipe Rescue.

It creates:

- one VPC dedicated to the project
- public subnets for internet-facing load balancers
- private subnets for EKS worker nodes
- one NAT Gateway for private worker node internet access
- one Amazon EKS cluster
- one EKS managed node group for running ArgoCD, frontend, backend, and PostgreSQL
- AWS EBS CSI Driver for dynamic Kubernetes persistent volumes
- encrypted default `gp3` Kubernetes StorageClass
- ArgoCD installed with Helm
- External Secrets Operator installed with Helm
- EKS Pod Identity for External Secrets Operator
- an ArgoCD repository credential synced from AWS Secrets Manager

## Why Terraform

Terraform lets us describe infrastructure in files instead of creating it manually in the AWS Console. That gives the project the same DevOps discipline as application code: reviewable changes, repeatable environments, and a clear destroy path when the demo is finished.

## File Roles

- `backend.tf`: configures the shared S3 Terraform backend used by local Terraform and GitHub Actions.
- `versions.tf`: declares the Terraform and AWS provider versions.
- `providers.tf`: configures the AWS provider and default resource tags.
- `variables.tf`: defines configurable inputs such as region, VPC CIDR, Kubernetes version, and node sizes.
- `locals.tf`: computes shared names, selected availability zones, and common tags.
- `main.tf`: creates the VPC and EKS cluster using official community Terraform modules.
- `helm.tf`: installs ArgoCD, External Secrets Operator, and the small Recipe Rescue platform bootstrap chart.
- `external-secrets.tf`: creates the IAM role and EKS Pod Identity association that allow External Secrets Operator to read `recipe-rescue/*` secrets from AWS Secrets Manager.
- `ebs-csi.tf`: installs the AWS EBS CSI Driver and default encrypted `gp3` StorageClass used by PostgreSQL PVCs.
- `outputs.tf`: prints useful values after deployment, including the `aws eks update-kubeconfig` command.
- `terraform.tfvars.example`: safe example values. Copy it to `terraform.tfvars` locally and adjust if needed.
- `charts/recipe-rescue-platform`: local Helm chart for cluster bootstrap resources that depend on ArgoCD and External Secrets CRDs.
- `scripts/destroy-infra.ps1`: guided cleanup script that creates a destroy plan and asks for confirmation before deleting infrastructure.

## Important Cost Note

This is a real AWS EKS environment, not a free-tier-only environment. EKS has a paid control plane, EC2 worker nodes create compute cost, NAT Gateways create hourly and data-processing cost, and persistent volumes/load balancers can also create cost later.

The default variables are intentionally professional for a final DevOps presentation:

- four `t3.small` worker nodes by default, with a minimum of two
- worker nodes placed in private subnets
- one shared NAT Gateway for private subnet internet egress
- maximum node count limited to `4`

This is more expensive than the lowest-cost demo mode, but it is easier to justify architecturally because application workloads are not placed directly in public subnets.

For a temporary lower-cost experiment, set:

```hcl
enable_nat_gateway = false
use_private_nodes  = false
node_desired_size   = 1
node_max_size       = 2
```

That removes the NAT Gateway and places worker nodes in public subnets. AWS security groups still control access, but the architecture is less production-like.

Keep your AWS budget alerts enabled, and destroy the environment when you no longer need it:

```bash
terraform destroy
```

On Windows, you can also use the guided cleanup script:

```powershell
.\scripts\destroy-infra.ps1
```

## First-Time Setup

Install these tools locally:

- Terraform
- AWS CLI
- kubectl

Then authenticate AWS CLI with an IAM user/role that can create VPC, EC2, IAM, and EKS resources.

```bash
aws configure
```

Create your local variables file:

```bash
cd infra/terraform/aws
copy terraform.tfvars.example terraform.tfvars
```

Initialize Terraform:

```bash
terraform init
```

Preview what Terraform wants to create:

```bash
terraform plan
```

Create the infrastructure:

```bash
terraform apply
```

If ArgoCD was previously installed manually with `kubectl apply`, remove only the manual bootstrap before applying the Terraform-managed platform services:

```bash
kubectl delete namespace argocd
kubectl delete namespace recipe-rescue-staging
```

Do not destroy the whole EKS cluster for this. The namespace deletion removes the temporary manual ArgoCD install and temporary staging secrets so Terraform and External Secrets Operator can recreate them cleanly.

After the apply succeeds, configure kubectl using the output command:

```bash
aws eks update-kubeconfig --region eu-central-1 --name recipe-rescue-shared-eks
```

Verify cluster access:

```bash
kubectl get nodes
```

## Cleanup

Terraform cleanup is the official recovery/deletion path for everything created by this directory.

From `infra/terraform/aws`:

```bash
terraform plan -destroy
terraform destroy
```

Or use the guarded PowerShell helper:

```powershell
.\scripts\destroy-infra.ps1
```

The script runs `terraform plan -destroy` first, then asks you to type `DESTROY` before it applies the deletion plan.

For this project, the recommended operating habit is:

1. Run `terraform apply` when you need the environment.
2. Test the CI/CD, ArgoCD, and application deployment.
3. Capture screenshots/evidence for the final documentation.
4. Run the destroy helper at the end of the session.

Do not leave the EKS cluster running indefinitely.

## Self-Recovery Strategy

This project uses several layers of recovery:

- Terraform stores the desired AWS infrastructure shape in code. If infrastructure is deleted or changed manually, `terraform plan` shows the drift and `terraform apply` can recreate the missing pieces.
- EKS managed node groups replace unhealthy worker nodes automatically.
- Kubernetes Deployments, StatefulSets, liveness probes, and readiness probes restart unhealthy application containers.
- ArgoCD automated sync with self-heal restores Kubernetes resources back to the Git-defined state if somebody changes them manually in the cluster.
- GitHub branch protections and PR checks protect the source of truth before it reaches ArgoCD.

The `Infrastructure Recovery` GitHub Actions workflow adds a controlled recovery layer for the AWS platform. It runs Terraform plan against remote state and supports three modes:

- `plan-only`: detects drift but never recreates infrastructure.
- `approval`: detects drift, then waits for approval through the `aws-infrastructure-recovery` GitHub environment before running Terraform apply.
- `auto`: detects drift and runs Terraform apply automatically. Use this only for a short trainer demo because it can recreate paid AWS resources after you intentionally destroy them.

For normal cost control, keep the repository variable below set to:

```text
INFRA_RECOVERY_MODE=approval
```

For a temporary self-healing demonstration, change it to:

```text
INFRA_RECOVERY_MODE=auto
```

After the demo, change it back to `approval` or `plan-only`, then destroy the infrastructure to avoid ongoing cost.

### GitHub Actions Recovery Setup

The recovery workflow needs shared Terraform state. Local laptop state is not enough because GitHub Actions must know what AWS resources already exist.

Create one S3 bucket for Terraform state and locking:

```powershell
aws s3api create-bucket `
  --bucket recipe-rescue-terraform-state-<unique-suffix> `
  --region eu-central-1 `
  --create-bucket-configuration LocationConstraint=eu-central-1

aws s3api put-bucket-versioning `
  --bucket recipe-rescue-terraform-state-<unique-suffix> `
  --versioning-configuration Status=Enabled
```

Terraform uses this bucket for both the state file and the native S3 lockfile. Older Terraform setups used DynamoDB for locking; this project uses `use_lockfile = true`, which avoids the DynamoDB deprecation warning in current Terraform versions.

Then add these GitHub repository variables:

```text
AWS_REGION=eu-central-1
INFRA_RECOVERY_MODE=approval
```

Add this GitHub repository secret:

```text
AWS_ROLE_TO_ASSUME=<arn-of-github-actions-aws-iam-role>
```

The AWS role should trust GitHub Actions OIDC for this repository and have enough permissions to run this Terraform project. For a student demo, an administrator-style role is simplest to operate, but a real production setup should narrow permissions to EKS, EC2/VPC, IAM roles used by EKS, KMS, CloudWatch Logs, Secrets Manager read access for the configured prefix, and S3 state access.

Finally, create a GitHub environment named:

```text
aws-infrastructure-recovery
```

Add yourself as a required reviewer. This is what makes `approval` mode safe: the workflow can detect drift automatically, but it cannot recreate infrastructure until you approve the environment deployment.

This is still not a full enterprise security platform. Later hardening can add AWS WAF, private-only nodes, network policies, CloudWatch alarms, Prometheus/Grafana alerts, backup/restore testing, and automated rollback workflows.

The shared Terraform backend is committed in `backend.tf` because this capstone has one official AWS backend. It does not contain passwords or tokens. Anyone who clones the repository and has AWS permissions can run:

```powershell
terraform init
```

and use the same S3 state file.

## What Comes Next

After EKS exists, the next phase is:

1. Let ArgoCD sync staging from the `staging` branch.
2. Promote to `release` when production blue/green is ready.

ArgoCD and External Secrets Operator are installed by Terraform, not manually.
