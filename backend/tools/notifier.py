import os
import requests
from crewai.tools import tool

@tool("Notification Sender")
def send_alert(message: str) -> str:
    """Sends high-priority alerts to the team webhook channel (Slack/Teams)."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        return "Notification skipped: SLACK_WEBHOOK_URL is not configured in .env."
    
    payload = {"text": f"🚨 *Autonomous Agent Insight Alert*\n{message}"}
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            return "Alert sent successfully!"
        else:
            return f"Failed to send alert. Status: {response.status_code}"
    except Exception as e:
        return f"Error sending alert: {str(e)}"