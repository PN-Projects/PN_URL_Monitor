#!/usr/bin/env python3

import json
import logging
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigValidator:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and scheme."""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['https']
        except Exception:
            return False

    @staticmethod
    def validate_config(config: Dict) -> bool:
        """Validate configuration structure and values."""
        try:
            monitoring = config.get('monitoring', {})
            security = config.get('security', {})

            # Validate monitoring settings
            if not isinstance(monitoring.get('interval_minutes'), (int, float)) or \
               not isinstance(monitoring.get('timeout_seconds'), (int, float)) or \
               not isinstance(monitoring.get('max_retries'), int) or \
               not isinstance(monitoring.get('retry_delay_seconds'), (int, float)):
                return False

            # Validate security settings
            if not isinstance(security.get('max_urls'), int) or \
               not isinstance(security.get('allowed_schemes'), list) or \
               not isinstance(security.get('max_timeout_seconds'), (int, float)) or \
               not isinstance(security.get('max_interval_minutes'), (int, float)):
                return False

            # Validate URLs
            urls = monitoring.get('urls', [])
            if not isinstance(urls, list) or len(urls) > security['max_urls']:
                return False

            for url_config in urls:
                if not all(k in url_config for k in ['name', 'url', 'expected_status']):
                    return False
                if not ConfigValidator.validate_url(url_config['url']):
                    return False

            return True
        except Exception:
            return False

class URLMonitor:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.session = self._create_session()

    def _load_config(self) -> Dict:
        """Load and validate configuration file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            with open(self.config_path, 'r') as f:
                config = json.load(f)

            if not ConfigValidator.validate_config(config):
                raise ValueError("Invalid configuration format or values")

            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise

    def _create_session(self) -> requests.Session:
        """Create a secure requests session."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Secure-Monitoring-Agent/1.0'
        })
        return session

    def check_url(self, url_config: Dict) -> Dict:
        """Check a single URL with retries and error handling."""
        url = url_config['url']
        expected_status = url_config['expected_status']
        max_retries = self.config['monitoring']['max_retries']
        retry_delay = self.config['monitoring']['retry_delay_seconds']
        timeout = self.config['monitoring']['timeout_seconds']

        result = {
            'url': url,
            'name': url_config['name'],
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'DOWN',
            'response_time': None,
            'status_code': None,
            'error': None
        }

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.session.get(
                    url,
                    timeout=timeout,
                    verify=True,
                    headers=url_config.get('headers', {})
                )
                response_time = time.time() - start_time

                result.update({
                    'status': 'UP' if response.status_code == expected_status else 'DOWN',
                    'response_time': round(response_time * 1000, 2),  # Convert to milliseconds
                    'status_code': response.status_code
                })

                if result['status'] == 'UP':
                    break

            except RequestException as e:
                result['error'] = str(e)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue

        return result

    def monitor_urls(self) -> List[Dict]:
        """Monitor all configured URLs."""
        results = []
        for url_config in self.config['monitoring']['urls']:
            try:
                result = self.check_url(url_config)
                results.append(result)
                logger.info(f"Checked {url_config['name']}: {result['status']}")
            except Exception as e:
                logger.error(f"Error monitoring {url_config['name']}: {str(e)}")
                results.append({
                    'url': url_config['url'],
                    'name': url_config['name'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'ERROR',
                    'error': str(e)
                })

        return results

    def run(self):
        """Main monitoring loop."""
        interval = self.config['monitoring']['interval_minutes'] * 60

        while True:
            try:
                results = self.monitor_urls()
                # TODO: Send results to backend API (will be implemented in Phase 2)
                logger.info(f"Monitoring cycle completed. Checked {len(results)} URLs.")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {str(e)}")
                time.sleep(interval)

if __name__ == "__main__":
    try:
        monitor = URLMonitor("config.json")
        monitor.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        exit(1) 