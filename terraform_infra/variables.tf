variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "Subnet CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "AZ for subnet"
  type        = string
  default     = "ap-south-1a"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 1
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "c5a.xlarge"
}

variable "ami_id" {
  description = "AMI ID"
  type        = string
  default     = "ami-05d2d839d4f73aafb"
}

variable "key_name" {
  description = "SSH key name"
  type        = string
  default     = "srusti_203"
}

variable "volume_size" {
  description = "Root volume size"
  type        = number
  default     = 30
}

variable "project_name" {
  description = "Project tag name"
  type        = string
  default     = "default"
}