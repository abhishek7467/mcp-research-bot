"""Notifier - Send notifications via Slack/Email"""

from typing import Dict, Any
import logging
import requests


class Notifier:
    """Sends notifications about newspaper generation"""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize notifier
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.enabled = config.get('notifications', {}).get('enabled', False)
    
    def send_notification(
        self, 
        title: str, 
        message: str, 
        newspaper_path: str = None,
        is_error: bool = False
    ):
        """Send notification"""
        if not self.enabled:
            return
        
        # Slack notification
        slack_config = self.config.get('notifications', {}).get('slack', {})
        if slack_config.get('webhook_url'):
            self._send_slack(title, message, newspaper_path, is_error, slack_config)
        
        # Email notification
        email_config = self.config.get('notifications', {}).get('email', {})
        if email_config.get('smtp_host'):
            self._send_email(title, message, newspaper_path, is_error, email_config)
    
    def _send_slack(
        self, 
        title: str, 
        message: str, 
        newspaper_path: str,
        is_error: bool,
        config: Dict[str, Any]
    ):
        """Send Slack notification"""
        try:
            color = '#FF0000' if is_error else '#36a64f'
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': title,
                    'text': message,
                    'footer': 'MCP Research Bot',
                    'ts': int(time.time())
                }]
            }
            
            if newspaper_path:
                payload['attachments'][0]['fields'] = [{
                    'title': 'Newspaper Path',
                    'value': newspaper_path,
                    'short': False
                }]
            
            response = requests.post(
                config['webhook_url'],
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info("Slack notification sent")
            
        except Exception as e:
            self.logger.error(f"Slack notification failed: {str(e)}")
    
    def _send_email(
        self, 
        title: str, 
        message: str, 
        newspaper_path: str,
        is_error: bool,
        config: Dict[str, Any]
    ):
        """Send email notification"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = config.get('from_address', '')
            msg['To'] = ', '.join(config.get('to_addresses', []))
            msg['Subject'] = title
            
            body = f"{message}\n\n"
            if newspaper_path:
                body += f"Newspaper: {newspaper_path}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(config['smtp_host'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['username'], config['password'])
                server.send_message(msg)
            
            self.logger.info("Email notification sent")
            
        except Exception as e:
            self.logger.error(f"Email notification failed: {str(e)}")


import time
