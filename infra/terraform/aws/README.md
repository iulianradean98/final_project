# AWS EKS Terraform Infrastructure

This directory contains the first AWS infrastructure layer for Recipe Rescue.

It creates:

- one VPC dedicated to the project
- public subnets for internet-facing load balancers
- private subnets for EKS worker nodes
- one NAT Gateway by default, to keep the project cost lower
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

## Important Cost Note

EKS has a paid control plane, and NAT Gateways plus EC2 worker nodes also create cost. Keep your AWS budget alerts enabled, and destroy the environment when you no longer need it:

```bash
terraform destroy
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

## What Comes Next

After EKS exists, the next phase is:

1. Install ArgoCD into the cluster.
2. Apply the ArgoCD bootstrap manifests.
3. Create Kubernetes Secrets for PostgreSQL and backend settings.
4. Let ArgoCD sync staging from the `staging` branch.
