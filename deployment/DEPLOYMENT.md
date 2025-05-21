# URL Monitor Deployment Guide

This guide covers the deployment of all components of the URL Monitoring System.

## Prerequisites

1. Azure Account with:
   - Azure VM (Ubuntu 20.04 LTS)
   - Azure SQL Database
   - Azure Function App
   - Discord Webhook URL (for alerts)

2. Required Tools:
   - Azure CLI
   - Maven
   - Python 3.8+
   - Git

## Deployment Steps

### 1. Azure VM Setup

1. Create an Azure VM:
   ```bash
   az vm create \
     --resource-group your-resource-group \
     --name url-monitor-vm \
     --image Ubuntu2204 \
     --size Standard_B2s \
     --admin-username azureuser \
     --generate-ssh-keys
   ```

2. Open required ports:
   ```bash
   az vm open-port \
     --resource-group your-resource-group \
     --name url-monitor-vm \
     --port 80
   ```

3. SSH into the VM:
   ```bash
   ssh azureuser@your-vm-ip
   ```

### 2. Application Deployment

1. Clone the repository:
   ```bash
   git clone your-repo-url /opt/url-monitor
   ```

2. Run the setup script:
   ```bash
   cd /opt/url-monitor/deployment
   chmod +x setup-vm.sh
   ./setup-vm.sh
   ```

3. Update environment variables:
   ```bash
   sudo nano /etc/environment
   ```
   Update the following variables:
   - AZURE_SQL_SERVER
   - AZURE_SQL_DATABASE
   - AZURE_SQL_USERNAME
   - AZURE_SQL_PASSWORD
   - DISCORD_WEBHOOK_URL

### 3. Azure Function Deployment

1. Install Azure Functions Core Tools:
   ```bash
   npm install -g azure-functions-core-tools@4
   ```

2. Deploy the function:
   ```bash
   cd azure-function
   func azure functionapp publish your-function-app-name
   ```

3. Configure function settings in Azure Portal:
   - CONSECUTIVE_FAILURES_THRESHOLD
   - BACKEND_API_URL
   - DISCORD_WEBHOOK_URL

### 4. Verify Deployment

1. Check service status:
   ```bash
   sudo supervisorctl status
   ```

2. Check logs:
   ```bash
   tail -f /opt/url-monitor/*/logs/*.log
   ```

3. Test the dashboard:
   - Open http://your-vm-ip in a browser
   - Verify monitoring data is displayed
   - Check alert functionality

## Monitoring and Maintenance

### Logs
- Backend logs: `/opt/url-monitor/backend/logs/`
- Dashboard logs: `/opt/url-monitor/dashboard/logs/`
- Monitor logs: `/opt/url-monitor/monitor/logs/`

### Common Commands
```bash
# Restart all services
sudo supervisorctl restart all

# View service status
sudo supervisorctl status

# View logs
tail -f /opt/url-monitor/*/logs/*.log

# Update application
cd /opt/url-monitor
git pull
sudo supervisorctl restart all
```

## Security Considerations

1. Keep the system updated:
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   ```

2. Use strong passwords and keep them secure

3. Regularly check logs for suspicious activity

4. Keep environment variables secure

5. Use HTTPS in production (configure SSL certificates)

## Troubleshooting

1. Service not starting:
   - Check logs in `/opt/url-monitor/*/logs/`
   - Verify environment variables
   - Check service status: `sudo supervisorctl status`

2. Database connection issues:
   - Verify Azure SQL firewall rules
   - Check connection string
   - Verify credentials

3. Alert system not working:
   - Check Discord webhook URL
   - Verify Azure Function logs
   - Check function configuration 