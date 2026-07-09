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

variable "kubernetes_version" {
  description = "EKS Kubernetes control plane version."
  type        = string
  default     = "1.33"
}

variable "node_instance_types" {
  description = "EC2 instance types allowed for the EKS managed node group."
  type        = list(string)
  default     = ["t3.small"]
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 1
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 3
}
