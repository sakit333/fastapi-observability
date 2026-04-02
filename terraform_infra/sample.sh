#!/bin/bash
# Update and install nginx
sudo apt update -y
sudo apt install -y nginx

# Ensure nginx is running
sudo systemctl enable nginx
sudo systemctl restart nginx

#  Install Docker and Docker-compose
sudo apt install docker.io -y
sudo apt install docker-compose -y


