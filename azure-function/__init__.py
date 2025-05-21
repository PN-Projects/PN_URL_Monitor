import datetime
import logging
import os
import json
import requests
from typing import List, Dict
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import time

# Configuration
CONSECUTIVE_FAILURES_THRESHOLD = int(os.getenv('CONSECUTIVE_FAILURES_THRESHOLD', '3'))
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8080/api/logs')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
STORAGE_CONNECTION_STRING = os.getenv('AzureWebJobsStorage', '')
ALERT_COOLDOWN_MINUTES = int(os.getenv('ALERT_COOLDOWN_MINUTES', '30'))

# Initialize blob service client for alert cooldown
blob_service_client = None
if STORAGE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client('alert-cooldown')

def main(mytimer: func.TimerRequest) -> None:
    """Azure Function triggered by timer to check URL status and send alerts."""
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
    
    try:
        # Fetch recent logs from backend API with timeout
        logs = fetch_recent_logs()
        
        if not logs:
            logging.warning("No logs fetched from backend API")
            return
        
        # Analyze logs for consecutive failures
        alerts = analyze_logs(logs)
        
        # Send alerts if any
        if alerts:
            send_alerts(alerts)
            
    except Exception as e:
        logging.error(f"Error in alert function: {str(e)}")
        # Don't raise the exception to prevent function retries
        return

def fetch_recent_logs() -> List[Dict]:
    """Fetch recent logs from the backend API with timeout."""
    try:
        # Set a reasonable timeout to prevent long-running executions
        response = requests.get(BACKEND_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching logs: {str(e)}")
        return []

def analyze_logs(logs: List[Dict]) -> List[Dict]:
    """Analyze logs for consecutive failures and generate alerts."""
    alerts = []
    
    # Group logs by URL
    url_logs = {}
    for log in logs:
        url = log['url']
        if url not in url_logs:
            url_logs[url] = []
        url_logs[url].append(log)
    
    # Check each URL for consecutive failures
    for url, url_log_list in url_logs.items():
        # Sort logs by timestamp
        url_log_list.sort(key=lambda x: x['timestamp'])
        
        # Count consecutive failures
        consecutive_failures = 0
        for log in reversed(url_log_list):  # Check most recent logs first
            if log['status'] == 'DOWN':
                consecutive_failures += 1
            else:
                break
        
        # Check if we should send an alert (considering cooldown)
        if (consecutive_failures >= CONSECUTIVE_FAILURES_THRESHOLD and 
            not is_in_cooldown(url)):
            alerts.append({
                'url': url,
                'name': url_log_list[0]['name'],
                'consecutive_failures': consecutive_failures,
                'last_status': url_log_list[-1]['status'],
                'last_check': url_log_list[-1]['timestamp']
            })
            # Set cooldown for this URL
            set_cooldown(url)
    
    return alerts

def is_in_cooldown(url: str) -> bool:
    """Check if a URL is in alert cooldown period."""
    if not blob_service_client:
        return False
    
    try:
        blob_name = f"cooldown_{url.replace('://', '_').replace('/', '_')}"
        blob_client = container_client.get_blob_client(blob_name)
        
        # Check if blob exists and is not expired
        if blob_client.exists():
            properties = blob_client.get_blob_properties()
            last_modified = properties.last_modified
            cooldown_end = last_modified + datetime.timedelta(minutes=ALERT_COOLDOWN_MINUTES)
            
            if datetime.datetime.now(datetime.timezone.utc) < cooldown_end:
                return True
            
            # Remove expired cooldown
            blob_client.delete_blob()
        return False
    except Exception as e:
        logging.error(f"Error checking cooldown: {str(e)}")
        return False

def set_cooldown(url: str) -> None:
    """Set alert cooldown for a URL."""
    if not blob_service_client:
        return
    
    try:
        blob_name = f"cooldown_{url.replace('://', '_').replace('/', '_')}"
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob("cooldown", overwrite=True)
    except Exception as e:
        logging.error(f"Error setting cooldown: {str(e)}")

def send_alerts(alerts: List[Dict]) -> None:
    """Send alerts via Discord webhook with rate limiting."""
    if not DISCORD_WEBHOOK_URL:
        logging.warning("Discord webhook URL not configured")
        return

    for alert in alerts:
        message = {
            "embeds": [{
                "title": "🚨 URL Monitoring Alert",
                "description": f"URL has been down for {alert['consecutive_failures']} consecutive checks",
                "color": 16711680,  # Red color
                "fields": [
                    {
                        "name": "URL Name",
                        "value": alert['name'],
                        "inline": True
                    },
                    {
                        "name": "URL",
                        "value": alert['url'],
                        "inline": True
                    },
                    {
                        "name": "Last Check",
                        "value": alert['last_check'],
                        "inline": True
                    }
                ]
            }]
        }

        try:
            # Add rate limiting to prevent Discord API throttling
            response = requests.post(
                DISCORD_WEBHOOK_URL,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=5  # Add timeout to prevent long-running executions
            )
            response.raise_for_status()
            logging.info(f"Alert sent for {alert['url']}")
            
            # Add small delay between alerts
            time.sleep(1)
            
        except requests.RequestException as e:
            logging.error(f"Error sending alert: {str(e)}")
            # Don't raise the exception to continue processing other alerts 