# FastAPI Observability

## Overview
This project provides comprehensive observability solutions for FastAPI applications, including logging, metrics, and distributed tracing capabilities.

## Features
- Structured logging integration
- Application performance monitoring
- Distributed tracing support
- Metrics collection and visualization
- Health checks and diagnostics

## Getting Started
See the documentation for installation and usage instructions.
---

### To Host locally using Docker Desktop
1. Install Docker Desktop from [docker.com](https://docker.com)
2. Navigate to the project directory
3. Run `docker-compose up -d --build` to start all services
4. Access the application at `http://localhost:8000`
5. Run `docker-compose down` to stop and remove containers

For more details, see the [Docker Compose documentation](https://docs.docker.com/compose/).
---

### To Host through Docker Desktop kubernetes
1. Enable Kubernetes in Docker Desktop settings
2. Build the Docker image: `docker build -t fastapi-observability .`
3. Create a namespace: `kubectl create namespace observability`
4. Apply the Kubernetes manifests: `kubectl apply -f k8s/ -n observability`
5. Access the application at `http://localhost:8000`
6. Monitor with `kubectl get pods -n observability`
7. Clean up with `kubectl delete namespace observability`

For more details, see the [Kubernetes documentation](https://kubernetes.io/docs/).
---

### To Deploy in aws ec2 remote host
1. Ensure AWS CLI is configured with your credentials
2. Update the `deploy.sh` script with your EC2 instance details (IP, key pair, security group)
3. Run `./deploy.sh` to automate the deployment process
4. The script will handle SSH connection, dependency installation, and service startup
5. Access the application at `http://<your-ec2-public-ip>:8000`
6. Monitor logs with `ssh -i <key-pair> ec2-user@<instance-ip> tail -f /var/log/fastapi-observability.log`

For more details, see the [AWS EC2 documentation](https://docs.aws.amazon.com/ec2/).
---
*Script Done by sak_shetty*