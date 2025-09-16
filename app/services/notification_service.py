"""Email notification service for rate limit alerts and system notifications."""

import smtplib
import structlog
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = structlog.get_logger()


class NotificationService:
    """Service for sending email notifications about system events."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.notification_email = settings.NOTIFICATION_EMAIL
        self._email_sent_this_session = False  # Track if email was already sent this session
    
    def send_rate_limit_alert(
        self, 
        primary_model: str, 
        fallback_model: str, 
        error_message: str,
        conversation_id: Optional[str] = None
    ) -> bool:
        """Send email alert when rate limits are hit and fallback is used (once per session)."""
        
        # Skip if email was already sent this session
        if self._email_sent_this_session:
            logger.info(
                "Rate limit email skipped - already sent this session",
                primary_model=primary_model,
                fallback_model=fallback_model,
                conversation_id=conversation_id
            )
            return True  # Return True since this is intentional behavior
        
        subject = f"🚨 PLC-Copilot: Rate Limit Hit - Fallback to {fallback_model}"
        
        body = f"""
Hello,

The PLC-Copilot system has hit rate limits and automatically switched to a fallback model.

⚠️ NOTE: This is a ONE-TIME notification per server session to avoid email spam.
Subsequent rate limit events this session will use fallback models silently.

🔧 INCIDENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
🤖 Primary Model: {primary_model}
🔄 Fallback Model: {fallback_model}
💬 Conversation ID: {conversation_id or 'N/A'}

📋 ERROR MESSAGE:
{error_message}

🎯 ACTION TAKEN:
✅ Automatically switched to {fallback_model} to maintain service availability
✅ User experience should remain uninterrupted
✅ System continues to function normally
✅ Further rate limit events will use fallback silently (no more emails this session)

💡 RECOMMENDATION:
Consider adding a payment method to your OpenAI account to increase rate limits:
https://platform.openai.com/account/billing

📊 MONITORING:
Check usage at: https://platform.openai.com/account/usage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated notification from PLC-Copilot.
System continues to operate normally with fallback model.

Best regards,
PLC-Copilot System
        """
        
        success = self._send_email(subject, body)
        
        # Mark email as sent this session if successful
        if success:
            self._email_sent_this_session = True
            
        return success
    
    def _send_email(self, subject: str, body: str) -> bool:
        """Send email using SMTP."""
        
        # Skip email if SMTP not configured
        if not self.smtp_user or not self.smtp_password:
            logger.warning(
                "Email notification skipped - SMTP not configured",
                subject=subject,
                recipient=self.notification_email
            )
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.notification_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.notification_email, msg.as_string())
            
            logger.info(
                "Rate limit notification sent successfully",
                recipient=self.notification_email,
                subject=subject
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send email notification",
                error=str(e),
                recipient=self.notification_email,
                subject=subject
            )
            return False