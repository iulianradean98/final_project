# AWS EKS Terraform Infrastructure

This directory contains the first AWS infrastructure layer for Recipe Rescue.

It creates:

- one VPC dedicated to the project
- public subnets for internet-facing load balancers
- private subnets for EKS worker nodes
- optional NAT Gateway for private worker node internet access
- one Amazon EKS cluster
- one EKS managed node group for running ArgoCD, frontend, backend, and PostgreSQL

## Why Terraform

Terraform lets us describe infrastructure in files instead of creating it manually in the AWS Console. That gives the project the same DevOps discipline as application code: reviewable changes, repeatable environments, and a clear destroy path when the demo is finished.

## File Roles

- `versions.tf`: declares the Terraform and AWS provider versions.
- `providers.tf`: configures the AWS provider and default resource tags.
- `variables.tf`: defines configurable inputs such as region, VPC CIDR, Kubernetes version, and node sizes.
- `locals.tf`: computes shared names, selected availability zones, and common tags.
- `main.tf`: creates the VPC and EKS cluster using official community Terraform modules.
- `outputs.tf`: prints useful values after deployment, including the `aws eks update-kubeconfig` command.
- `terraform.tfvars.example`: safe example values. Copy it to `terraform.tfvars` locally and adjust if needed.
- `scripts/destroy-infra.ps1`: guided cleanup script that creates a destroy plan and asks for confirmation before deleting infrastructure.

## Important Cost Note

This is a real AWS EKS environment, not a free-tier-only environment. EKS has a paid control plane, EC2 worker nodes create compute cost, NAT Gateways create hourly and data-processing cost if enabled, and persistent volumes/load balancers can also create cost later.

The default variables are intentionally cost-aware for a student demo:

- one `t3.small` worker node by default
- NAT Gateway disabled by default
- worker nodes placed in public subnets by default, protected by AWS security groups
- maximum node count limited to `2`

For a more production-like setup, set:

```hcl
enable_nat_gateway = true
use_private_nodes  = true
```

That places worker nodes in private subnets, but it also increases cost because the NAT Gateway becomes necessary for internet egress.

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

## Self-Recovery Strategy

This project uses several layers of recovery:

- Terraform stores the desired AWS infrastructure shape in code. If infrastructure is deleted or changed manually, `terraform plan` shows the drift and `terraform apply` can recreate the missing pieces.
- EKS managed node groups replace unhealthy worker nodes automatically.
- Kubernetes Deployments, StatefulSets, liveness probes, and readiness probes restart unhealthy application containers.
- ArgoCD automated sync with self-heal restores Kubernetes resources back to the Git-defined state if somebody changes them manually in the cluster.
- GitHub branch protections and PR checks protect the source of truth before it reaches ArgoCD.

This is not a full enterprise security platform yet. Later hardening can add AWS WAF, private-only nodes, network policies, external secrets, CloudWatch alarms, Prometheus/Grafana alerts, and automated rollback workflows.

## What Comes Next

After EKS exists, the next phase is:

1. Install ArgoCD into the cluster.
2. Apply the ArgoCD bootstrap manifests.
3. Create Kubernetes Secrets for PostgreSQL and backend settings.
4. Let ArgoCD sync staging from the `staging` branch.
