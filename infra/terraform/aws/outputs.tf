output "aws_region" {
  description = "AWS region where the infrastructure is deployed."
  value       = var.aws_region
}

output "db_backup_s3_bucket_name" {
  description = "Existing S3 bucket expected to contain PostgreSQL disaster-recovery backups."
  value       = var.db_backup_s3_bucket_name
}

output "cluster_name" {
  description = "EKS cluster name."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS Kubernetes API endpoint."
  value       = module.eks.cluster_endpoint
}

output "vpc_id" {
  description = "VPC ID used by the EKS cluster."
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs used by EKS worker nodes."
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs used by internet-facing load balancers."
  value       = module.vpc.public_subnets
}

output "configure_kubectl_command" {
  description = "Command used to configure local kubectl access after terraform apply succeeds."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "grafana_port_forward_command" {
  description = "Command used to open Grafana locally through kubectl port-forward."
  value       = "kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80"
}

output "prometheus_port_forward_command" {
  description = "Command used to open Prometheus locally through kubectl port-forward."
  value       = "kubectl port-forward svc/monitoring-prometheus -n monitoring 9090:9090"
}
