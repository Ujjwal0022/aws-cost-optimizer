output "cluster_name"        { value = module.eks.cluster_name }
output "cluster_endpoint"    { value = module.eks.cluster_endpoint }
output "ecr_backend_url"     { value = aws_ecr_repository.backend.repository_url }
output "ecr_frontend_url"    { value = aws_ecr_repository.frontend.repository_url }
output "kubeconfig_command"  { value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${var.cluster_name}" }
