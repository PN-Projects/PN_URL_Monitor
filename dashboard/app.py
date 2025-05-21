from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configuration
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8080/api/logs')

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/monitoring-data')
def get_monitoring_data():
    """Fetch monitoring data from the backend API."""
    try:
        response = requests.get(BACKEND_API_URL)
        response.raise_for_status()
        logs = response.json()
        
        # Process logs for chart display
        processed_data = process_logs(logs)
        return jsonify(processed_data)
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

def process_logs(logs):
    """Process logs for chart display."""
    # Group logs by URL
    url_data = {}
    
    for log in logs:
        url = log['url']
        if url not in url_data:
            url_data[url] = {
                'name': log['name'],
                'timestamps': [],
                'response_times': [],
                'status': []
            }
        
        url_data[url]['timestamps'].append(log['timestamp'])
        url_data[url]['response_times'].append(log['responseTime'])
        url_data[url]['status'].append(log['status'])
    
    return {
        'urls': list(url_data.keys()),
        'data': url_data
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 