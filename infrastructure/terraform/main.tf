terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC y Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "ai-assistants-vpc"
    Project = "ai-assistants"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "ai-assistants-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "ai-assistants-public-subnet"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "ai-assistants-public-subnet-b"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "ai-assistants-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Security Group para EC2
resource "aws_security_group" "ec2" {
  name        = "ai-assistants-ec2-sg"
  description = "Security group for AI Assistants EC2 instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "WhatsApp Service"
    from_port   = 60007
    to_port     = 60007
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restringir a tu IP en producción
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ai-assistants-ec2-sg"
  }
}

# Security Group for RDS removed. Access should be managed on the existing RDS instance.

# The RDS instance creation has been removed to reuse an existing RDS instance.
# New databases should be created manually or via script in the existing RDS.

# Security Group para ElastiCache
resource "aws_security_group" "redis" {
  name        = "ai-assistants-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ai-assistants-redis-sg"
  }
}

# RDS resources removed to reuse existing instance.

# ElastiCache Redis (Free Tier: cache.t2.micro)
resource "aws_elasticache_subnet_group" "main" {
  name       = "ai-assistants-redis-subnet"
  subnet_ids = [aws_subnet.public.id]
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "ai-assistants-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro" # Updated from t2.micro
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Name = "ai-assistants-redis"
  }
}

# EFS para WhatsApp auth_info
resource "aws_efs_file_system" "whatsapp_auth" {
  creation_token = "ai-assistants-whatsapp-auth"
  encrypted       = true

  tags = {
    Name = "ai-assistants-whatsapp-auth"
  }
}

resource "aws_efs_mount_target" "whatsapp_auth" {
  file_system_id  = aws_efs_file_system.whatsapp_auth.id
  subnet_id       = aws_subnet.public.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_security_group" "efs" {
  name        = "ai-assistants-efs-sg"
  description = "Security group for EFS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "NFS"
    from_port      = 2049
    to_port        = 2049
    protocol       = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ai-assistants-efs-sg"
  }
}

# EC2 Instance (Free Tier: t2.micro)
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro" # Updated from t2.micro
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  subnet_id              = aws_subnet.public.id

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker git
              systemctl start docker
              systemctl enable docker
              usermod -a -G docker ec2-user
              
              # Instalar Docker Compose
              curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              
              # Instalar EFS utils
              yum install -y amazon-efs-utils
              
              # Crear directorio para EFS
              mkdir -p /mnt/efs/whatsapp-auth
              
              # Montar EFS (se montará manualmente después de crear el sistema de archivos)
              # mount -t efs ${aws_efs_file_system.whatsapp_auth.id}:/ /mnt/efs/whatsapp-auth
              EOF

  tags = {
    Name = "ai-assistants-server"
  }
}

# Outputs
output "ec2_public_ip" {
  value       = aws_instance.main.public_ip
  description = "Public IP of the EC2 instance"
}

output "ec2_ssh_command" {
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ec2-user@${aws_instance.main.public_ip}"
  description = "SSH command to connect to the instance"
}

output "rds_info" {
  value       = "Using existing RDS instance in VPC vpc-094d2ec2cace1d492. Ensure Security Group allows traffic from this EC2."
  description = "Status of RDS deployment"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
  description = "ElastiCache Redis endpoint"
}

output "efs_id" {
  value       = aws_efs_file_system.whatsapp_auth.id
  description = "EFS file system ID for WhatsApp auth"
}
