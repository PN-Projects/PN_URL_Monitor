#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    openjdk-17-jdk \
    python3-pip \
    python3-venv \
    nginx \
    supervisor

# Create application directories
sudo mkdir -p /opt/url-monitor/{backend,dashboard,monitor}
sudo chown -R $USER:$USER /opt/url-monitor

# Setup Java Backend
cd /opt/url-monitor/backend
sudo mkdir -p logs
sudo chown -R $USER:$USER logs

# Setup Python Dashboard
cd /opt/url-monitor/dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Monitoring Agent
cd /opt/url-monitor/monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Nginx
sudo tee /etc/nginx/sites-available/url-monitor << EOF
server {
    listen 80;
    server_name _;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Dashboard
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/url-monitor /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Configure Supervisor
sudo tee /etc/supervisor/conf.d/url-monitor.conf << EOF
[program:backend]
command=java -jar /opt/url-monitor/backend/url-monitor-api.jar
directory=/opt/url-monitor/backend
user=$USER
autostart=true
autorestart=true
stderr_logfile=/opt/url-monitor/backend/logs/backend.err.log
stdout_logfile=/opt/url-monitor/backend/logs/backend.out.log

[program:dashboard]
command=/opt/url-monitor/dashboard/venv/bin/python app.py
directory=/opt/url-monitor/dashboard
user=$USER
autostart=true
autorestart=true
stderr_logfile=/opt/url-monitor/dashboard/logs/dashboard.err.log
stdout_logfile=/opt/url-monitor/dashboard/logs/dashboard.out.log

[program:monitor]
command=/opt/url-monitor/monitor/venv/bin/python monitor.py
directory=/opt/url-monitor/monitor
user=$USER
autostart=true
autorestart=true
stderr_logfile=/opt/url-monitor/monitor/logs/monitor.err.log
stdout_logfile=/opt/url-monitor/monitor/logs/monitor.out.log
EOF

sudo mkdir -p /opt/url-monitor/{backend,dashboard,monitor}/logs
sudo chown -R $USER:$USER /opt/url-monitor/*/logs
sudo supervisorctl reread
sudo supervisorctl update

# Setup environment variables
sudo tee /etc/environment << EOF
# Backend Configuration
AZURE_SQL_SERVER=your-sql-server
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password

# Dashboard Configuration
BACKEND_API_URL=http://localhost:8080/api/logs

# Monitor Configuration
BACKEND_API_URL=http://localhost:8080/api/logs
EOF

# Reload environment variables
source /etc/environment

echo "Setup completed. Please update the environment variables in /etc/environment" 