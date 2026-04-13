provider "aws" {
  region = "ap-south-1"
}

# 1. Create VPC
resource "aws_vpc" "default_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "default_vpc"
  }
}

# 2. Create Internet Gateway
resource "aws_internet_gateway" "default_igw" {
  vpc_id = aws_vpc.default_vpc.id
  tags = {
    Name = "default_igw"
  }
}

# 3. Create Subnet
resource "aws_subnet" "default_subnet" {
  vpc_id                  = aws_vpc.default_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-south-1a"
  map_public_ip_on_launch = true
  tags = {
    Name = "default_subnet"
  }
}

# 4. Create Route Table
resource "aws_route_table" "default_rt" {
  vpc_id = aws_vpc.default_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.default_igw.id
  }

  tags = {
    Name = "default_rt"
  }
}

# 5. Associate Route Table to Subnet
resource "aws_route_table_association" "default_rta" {
  subnet_id      = aws_subnet.default_subnet.id
  route_table_id = aws_route_table.default_rt.id
}

# 6. Security Group
resource "aws_security_group" "app_sg" {
  name        = "default_sg"
  description = "Allow SSH and all inbound/outbound"
  vpc_id      = aws_vpc.default_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "default_sg"
  }
}

# 7. EC2 Instances
resource "aws_instance" "app_server" {
  ami             = "ami-05d2d839d4f73aafb"
  instance_type   = "m7i-flex.large"
  key_name        = "default"
  count           = 1
  subnet_id       = aws_subnet.default_subnet.id
  security_groups = [aws_security_group.app_sg.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name = "default_server"
  }

  user_data = file("setup.sh")
}

# 8. Outputs
output "vpc_id" {
  value = aws_vpc.default_vpc.id
}

output "subnet_id" {
  value = aws_subnet.default_subnet.id
}

output "route_table_id" {
  value = aws_route_table.default_rt.id
}

output "internet_gateway_id" {
  value = aws_internet_gateway.default_igw.id
}

output "public_ips" {
  value = [for instance in aws_instance.app_server : instance.public_ip]
}

output "private_ips" {
  value = [for instance in aws_instance.app_server : instance.private_ip]
}
