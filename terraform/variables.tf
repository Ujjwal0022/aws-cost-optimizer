variable "aws_region"   { default = "us-east-1" }
variable "cluster_name" { default = "finops-eks" }
variable "environment"  { default = "prod" }
variable "aws_access_key_id"     { sensitive = true }
variable "aws_secret_access_key" { sensitive = true }
variable "aws_account_id"        {}
