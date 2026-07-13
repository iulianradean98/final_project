variable "aws_region" {
  description = "AWS region where the EKS cluster will be created."
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Short project name used in AWS resource names and tags."
  type        = string
  default     = "recipe-rescue"
}

variable "environment" {
  description = "Infrastructure environment name. This is the shared AWS platform environment, not the app staging/release Git branches."
  type        = string
  default     = "shared"
}

variable "owner" {
  description = "Owner tag for AWS cost tracking."
  type        = string
  default     = "iulian"
}

variable "vpc_cidr" {
  description = "CIDR block for the project VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use for public/private subnets."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "Use 2 or 3 availability zones for this project."
  }
}

variable "single_nat_gateway" {
  description = "Use one NAT Gateway for all private subnets. This keeps the project cheaper than one NAT Gateway per AZ."
  type        = bool
  default     = true
}

variable "enable_nat_gateway" {
  description = "Create a NAT Gateway for private subnet internet access. Disable for the lowest-cost student demo profile."
  type        = bool
  default     = true
}

variable "use_private_nodes" {
  description = "Place worker nodes in private subnets. Requires enable_nat_gateway=true so nodes can pull container images."
  type        = bool
  default     = true
}

variable "kubernetes_version" {
  description = "EKS Kubernetes control plane version."
  type        = string
  default     = "1.36"
}

variable "eks_admin_principal_arns" {
  description = "IAM principal ARNs that should receive cluster-admin access to the EKS cluster, such as the local developer IAM user."
  type        = list(string)
  default     = []
}

variable "node_instance_types" {
  description = "EC2 instance types allowed for the EKS managed node group."
  type        = list(string)
  default     = ["t3.small"]
}

variable "node_capacity_type" {
  description = "EKS node capacity type. Use ON_DEMAND for stability or SPOT for lower cost with interruption risk."
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "node_capacity_type must be either ON_DEMAND or SPOT."
  }
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 6
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 7
}

variable "argocd_chart_version" {
  description = "Version of the argo-cd Helm chart to install."
  type        = string
  default     = "10.1.3"
}

variable "argo_rollouts_chart_version" {
  description = "Version of the argo-rollouts Helm chart to install."
  type        = string
  default     = "2.41.0"
}

variable "external_secrets_chart_version" {
  description = "Version of the external-secrets Helm chart to install."
  type        = string
  default     = "2.7.0"
}

variable "argocd_github_repo_secret_name" {
  description = "AWS Secrets Manager secret containing ArgoCD Git repository credentials."
  type        = string
  default     = "recipe-rescue/argocd/github-repo"
}

variable "github_repo_url" {
  description = "Git repository URL watched by ArgoCD."
  type        = string
  default     = "https://github.com/iulianradean98/final_project.git"
}

variable "argocd_root_target_revision" {
  description = "Git revision used by the ArgoCD root application."
  type        = string
  default     = "main"
}

variable "secrets_manager_prefix" {
  description = "Secrets Manager path prefix that External Secrets Operator is allowed to read."
  type        = string
  default     = "recipe-rescue/"
}

variable "db_backup_s3_bucket_name" {
  description = "Existing S3 bucket used for PostgreSQL disaster-recovery backups. The bucket is intentionally created outside this destroyable EKS stack."
  type        = string
  default     = "recipe-rescue-db-backups-iulian-2026"
}

variable "db_backup_s3_prefix" {
  description = "S3 key prefix used for PostgreSQL backups inside db_backup_s3_bucket_name."
  type        = string
  default     = "recipe-rescue"
}
