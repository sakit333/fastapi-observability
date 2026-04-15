output "vpc_id" {
  value = aws_vpc.this.id
}

output "subnet_id" {
  value = aws_subnet.this.id
}

output "route_table_id" {
  value = aws_route_table.this.id
}

output "internet_gateway_id" {
  value = aws_internet_gateway.this.id
}

output "public_ips" {
  value = [for i in aws_instance.this : i.public_ip]
}

output "private_ips" {
  value = [for i in aws_instance.this : i.private_ip]
}