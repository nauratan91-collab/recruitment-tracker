#!/bin/bash
# ==============================================================================
# Automated Setup Script for GoDaddy VPS (Ubuntu / Debian / CentOS / AlmaLinux)
# ==============================================================================

set -e

echo "=== Starting GoDaddy VPS Setup for Recruitment Tracker ==="

APP_DIR="/var/www/recruitment-tracker"
REPO_URL="https://github.com/nauratan91-collab/recruitment-tracker.git"

# Detect Package Manager & Install System Packages
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git nginx mysql-client
elif command -v dnf &> /dev/null; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip git nginx mysql
fi

# Create Application Directory
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Clone or pull codebase
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Cloning repository..."
    git clone $REPO_URL $APP_DIR
else
    echo "Updating repository..."
    cd $APP_DIR && git pull origin main
fi

cd $APP_DIR

# Set up Python Virtual Environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Ensure required directories exist with correct permissions
mkdir -p uploads/resumes uploads/compliance_docs
chmod -R 775 uploads

# Install Systemd Service
sudo cp recruitment-tracker.service /etc/systemd/system/recruitment-tracker.service
sudo systemctl daemon-reload
sudo systemctl enable recruitment-tracker
sudo systemctl restart recruitment-tracker

# Check status
sudo systemctl status recruitment-tracker --no-pager

echo "=== GoDaddy VPS Setup Completed Successfully! ==="
echo "Make sure to configure your domain in /etc/nginx/sites-available/ and reload Nginx."
