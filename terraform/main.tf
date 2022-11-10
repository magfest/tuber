terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.38.0"
    }
  }
}


# -------------------------------------------------------------------
# Import Data block for AWS information
# -------------------------------------------------------------------

data "external" "git_hash" {
  program = [
    "git",
    "log",
    "--pretty=format:{ \"sha\": \"%H\" }",
    "-1",
    "HEAD"
  ]
}

data "aws_caller_identity" "current" {}

# -------------------------------------------------------------------
# VPC Resources
# -------------------------------------------------------------------

resource "aws_security_group" "tuber_internal" {
  name        = "tuber_internal"
  description = "Allow ALB to reach Tuber"
  vpc_id      = aws_vpc.tuber.id

  ingress {
    description      = "HTTP to Tuber Frontend"
    from_port        = 8081
    to_port          = 8081
    protocol         = "tcp"
    cidr_blocks      = [aws_subnet.primary.cidr_block]
  }

  ingress {
    description      = "HTTP to Tuber Backend"
    from_port        = 8080
    to_port          = 8080
    protocol         = "tcp"
    cidr_blocks      = [aws_subnet.primary.cidr_block]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "tuber_internal"
  }
}

resource "aws_security_group" "tuber_redis" {
  name        = "tuber_redis"
  description = "Allow Tuber to reach Redis"
  vpc_id      = aws_vpc.tuber.id

  ingress {
    description      = "Tuber Redis"
    from_port        = 6379
    to_port          = 6379
    protocol         = "tcp"
    cidr_blocks      = [aws_subnet.primary.cidr_block]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "tuber_redis"
  }
}

resource "aws_security_group" "tuber_rds" {
  name        = "tuber_rds"
  description = "Allow Tuber to reach RDS"
  vpc_id      = aws_vpc.tuber.id

  ingress {
    description      = "Tuber RDS"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    cidr_blocks      = [aws_subnet.primary.cidr_block]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "tuber_rds"
  }
}

resource "aws_security_group" "tuber_external" {
  name        = "tuber_external"
  description = "Allow the Internet to reach Tuber"
  vpc_id      = aws_vpc.tuber.id

  ingress {
    description      = "Tuber HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Tuber HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "tuber_external"
  }
}

resource "aws_subnet" "primary" {
  vpc_id                  = aws_vpc.tuber.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = "us-east-1c"
  map_public_ip_on_launch = true

  tags = {
    Name = "Tuber Primary"
  }
}

resource "aws_subnet" "secondary" {
  vpc_id                  = aws_vpc.tuber.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "Tuber Secondary"
  }
}

resource "aws_db_subnet_group" "tuber" {
  name       = "tuber"
  subnet_ids = [
    aws_subnet.primary.id,
    aws_subnet.secondary.id
  ]

  tags = {
    Name = "Tuber"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.tuber.id

  tags = {
    Name = "Tuber"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.tuber.id

  route {
      cidr_block = "0.0.0.0/0"
      gateway_id = "${aws_internet_gateway.igw.id}"
  }
}

resource "aws_route_table_association" "primary_route" {
  subnet_id      = aws_subnet.primary.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "secondary_route" {
  subnet_id      = aws_subnet.secondary.id
  route_table_id = aws_route_table.public.id
}

resource "aws_vpc" "tuber" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "Tuber"
  }
}

# -------------------------------------------------------------------
# ECS Cluster
# -------------------------------------------------------------------

resource "aws_ecs_cluster" "tuber" {
  name = "Tuber"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# -------------------------------------------------------------------
# Tuber Load Balancer
# -------------------------------------------------------------------

resource "aws_lb" "tuber" {
  name_prefix        = "tuber"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [
    aws_security_group.tuber_external.id
  ]
  subnets            = aws_db_subnet_group.tuber.subnet_ids

  enable_deletion_protection = false
}

resource "aws_lb_target_group" "tuber_frontend" {
  name_prefix   = "tuber"
  port          = 80
  protocol      = "HTTP"
  target_type   = "ip"
  vpc_id        = aws_subnet.primary.vpc_id

  health_check {
    healthy_threshold   = 2
    interval            = 30
    unhealthy_threshold = 10
    timeout             = 5
    path                = "/"
    matcher             = "200"
  }
}

resource "aws_lb_target_group" "tuber_backend" {
  name_prefix   = "tuber"
  port          = 80
  protocol      = "HTTP"
  target_type   = "ip"
  vpc_id        = aws_subnet.primary.vpc_id

  health_check {
    healthy_threshold   = 2
    interval            = 30
    unhealthy_threshold = 10
    timeout             = 5
    path                = "/_health"
    matcher             = "200"
  }
}

resource "aws_lb_listener" "tuber_http" {
  load_balancer_arn = aws_lb.tuber.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "tuber_https" {
  load_balancer_arn = aws_lb.tuber.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.cert_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tuber_frontend.arn
  }
}

resource "aws_lb_listener_rule" "backend" {
  listener_arn = aws_lb_listener.tuber_https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tuber_backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# -------------------------------------------------------------------
# Tuber Containers
# -------------------------------------------------------------------

resource "aws_ecs_service" "tuber" {
  name            = "tuber"
  cluster         = aws_ecs_cluster.tuber.id
  task_definition = aws_ecs_task_definition.tuber.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  service_registries {
    registry_arn = aws_service_discovery_service.tuber.arn
  }

  network_configuration {
    subnets           = aws_db_subnet_group.tuber.subnet_ids
    security_groups   = [
      aws_security_group.tuber_internal.id
    ]
    assign_public_ip  = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tuber_frontend.arn
    container_name   = "frontend"
    container_port   = 8081
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tuber_backend.arn
    container_name   = "backend"
    container_port   = 8080
  }
}

resource "aws_ecs_task_definition" "tuber" {
  family                    = "tuber"
  container_definitions     = <<TASK_DEFINITION
[
  {
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/tuber/frontend",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "portMappings": [
      {
        "hostPort": 8081,
        "protocol": "tcp",
        "containerPort": 8081
      }
    ],
    "image": "${var.frontend_container}:${data.external.git_hash}",
    "essential": true,
    "name": "frontend"
  },
  {
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/tuber/backend",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "portMappings": [
      {
        "hostPort": 8080,
        "protocol": "tcp",
        "containerPort": 8080
      }
    ],
    "environment": [
      {
        "name": "REDIS_URL",
        "value": "redis://redis.tuber.local:6379/0"
      },
      {
        "name": "VERBOSE",
        "value": "true"
      },
      {
        "name": "FLASK_DEBUG",
        "value": "1"
      },
      {
        "name": "WORKERS",
        "value": "4"
      },
      {
        "name": "ENABLE_CIRCUITBREAKER",
        "value": "false"
      },
      {
        "name": "DATABASE_URL",
        "value": "postgresql://tuber:${random_password.tuber_db.result}@${aws_db_instance.tuber.endpoint}/tuber"
      }
    ],
    "image": "${var.backend_container}:${data.external.git_hash}",
    "essential": true,
    "name": "backend"
  }
]
TASK_DEFINITION

  cpu                       = 256
  memory                    = 512
  requires_compatibilities  = ["FARGATE"]
  network_mode              = "awsvpc"
  execution_role_arn        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecsTaskExecutionRole"

  depends_on = [
    aws_lb_listener.tuber_http,
    aws_lb_listener.tuber_https
  ]

  task_role_arn = aws_iam_role.task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}


# -------------------------------------------------------------------
# Redis Container
# -------------------------------------------------------------------

resource "aws_ecs_service" "redis" {
  name            = "redis"
  cluster         = aws_ecs_cluster.tuber.id
  task_definition = aws_ecs_task_definition.redis.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  service_registries {
    registry_arn = aws_service_discovery_service.redis.arn
  }

  network_configuration {
    subnets           = aws_db_subnet_group.tuber.subnet_ids
    security_groups   = [
      aws_security_group.tuber_redis.id
    ]
    assign_public_ip  = true
  }
}

resource "aws_ecs_task_definition" "redis" {
  family                    = "redis"
  container_definitions     = <<TASK_DEFINITION
[
  {
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/tuber/redis",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "portMappings": [
      {
        "hostPort": 6379,
        "protocol": "tcp",
        "containerPort": 6379
      }
    ],
    "image": "redis:alpine",
    "essential": true,
    "name": "redis"
  }
]
TASK_DEFINITION

  cpu                       = 256
  memory                    = 512
  requires_compatibilities  = ["FARGATE"]
  network_mode              = "awsvpc"
  execution_role_arn        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/ecsTaskExecutionRole"

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}


# -------------------------------------------------------------------
# Tuber Task Role
# -------------------------------------------------------------------

resource "aws_iam_role" "task_role" {
  name_prefix = "tuber"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      },
    ]
  })
}

# -------------------------------------------------------------------
# DNS Service Discovery
# -------------------------------------------------------------------

resource "aws_service_discovery_private_dns_namespace" "tuber" {
  name        = "tuber.local"
  description = "Tuber Services"
  vpc         = aws_subnet.primary.vpc_id
}

resource "aws_service_discovery_service" "redis" {
  name = "redis"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.tuber.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_service_discovery_service" "tuber" {
  name = "tuber"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.tuber.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# -------------------------------------------------------------------
# Postgres Database
# -------------------------------------------------------------------

resource "random_password" "tuber_db" {
  length            = 40
  special           = false
  keepers           = {
    pass_version  = 2
  }
}

resource "aws_db_instance" "tuber" {
  allocated_storage      = 10
  db_name                = "tuber"
  engine                 = "postgres"
  instance_class         = "db.t3.micro"
  username               = "tuber"
  password               = random_password.tuber_db.result
  skip_final_snapshot    = true
  multi_az               = false
  vpc_security_group_ids = [
    aws_security_group.tuber_rds.id
  ]
  db_subnet_group_name   = aws_db_subnet_group.tuber.name
}

resource "aws_secretsmanager_secret" "tuber_db_password" {
  name = "tuber_db_password"
}

resource "aws_secretsmanager_secret_version" "tuber_db_password" {
  secret_id     = aws_secretsmanager_secret.tuber_db_password.id
  secret_string = random_password.tuber_db.result
}