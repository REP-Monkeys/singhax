"""Email service for sending policy confirmations and copies."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        """Initialize email service."""
        self.smtp_host = getattr(settings, 'smtp_host', None) or 'localhost'
        self.smtp_port = getattr(settings, 'smtp_port', None) or 587
        self.smtp_user = getattr(settings, 'smtp_user', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.smtp_from_email = getattr(settings, 'smtp_from_email', None) or 'noreply@travelinsurance.com'
        self.smtp_use_tls = getattr(settings, 'smtp_use_tls', True)
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            if self.smtp_host == 'localhost' or not self.smtp_user:
                # Local/dev mode - just log
                logger.info(f"[EMAIL SERVICE] Would send email to {to_email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body: {html_body[:200]}...")
                return True
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_use_tls:
                server.starttls()
            
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Successfully sent email to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_policy_confirmation(
        self,
        to_email: str,
        policy_number: str,
        policy_details: Dict[str, Any]
    ) -> bool:
        """
        Send policy confirmation email.
        
        Args:
            to_email: Recipient email address
            policy_number: Policy number
            policy_details: Dictionary containing policy details:
                - effective_date: Policy start date
                - expiry_date: Policy end date
                - coverage: Coverage details
                - selected_tier: Insurance tier (standard/elite/premier)
                - destination: Travel destination
                
        Returns:
            True if email sent successfully, False otherwise
        """
        effective_date = policy_details.get('effective_date', 'N/A')
        expiry_date = policy_details.get('expiry_date', 'N/A')
        coverage = policy_details.get('coverage', {})
        selected_tier = policy_details.get('selected_tier', 'elite').title()
        destination = policy_details.get('destination', 'N/A')
        
        # Format coverage details
        coverage_html = ""
        if isinstance(coverage, dict):
            for key, value in coverage.items():
                if isinstance(value, (int, float)):
                    # Format currency values
                    if 'coverage' in key.lower() or 'limit' in key.lower():
                        formatted_value = f"${value:,.0f}"
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)
                coverage_html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {formatted_value}</li>"
        
        if not coverage_html:
            coverage_html = "<li>Coverage details available in your policy document</li>"
        
        subject = f"Travel Insurance Policy Confirmed - {policy_number}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .policy-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                ul {{ list-style-type: none; padding-left: 0; }}
                li {{ margin: 8px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Travel Insurance Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Dear Traveler,</p>
                    <p>Your travel insurance policy has been successfully confirmed and is now active.</p>
                    
                    <div class="policy-box">
                        <h2>Policy Details</h2>
                        <p><strong>Policy Number:</strong> {policy_number}</p>
                        <p><strong>Tier:</strong> {selected_tier}</p>
                        <p><strong>Destination:</strong> {destination}</p>
                        <p><strong>Coverage Period:</strong> {effective_date} to {expiry_date}</p>
                    </div>
                    
                    <h3>Coverage Summary</h3>
                    <ul>
                        {coverage_html}
                    </ul>
                    
                    <p>Your policy document is attached for your records. Please keep this email and policy number for your reference.</p>
                    
                    <p>Safe travels!</p>
                    <p>Travel Insurance Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated confirmation email. Please do not reply.</p>
                    <p>If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Travel Insurance Policy Confirmed!

Dear Traveler,

Your travel insurance policy has been successfully confirmed and is now active.

Policy Details:
- Policy Number: {policy_number}
- Tier: {selected_tier}
- Destination: {destination}
- Coverage Period: {effective_date} to {expiry_date}

Your policy document is attached for your records. Please keep this email and policy number for your reference.

Safe travels!
Travel Insurance Team

---
This is an automated confirmation email. Please do not reply.
If you have any questions, please contact our support team.
        """
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_policy_copy(
        self,
        to_email: str,
        policy_number: str,
        policy_details: Dict[str, Any]
    ) -> bool:
        """
        Send policy copy email on user request.
        
        Args:
            to_email: Recipient email address
            policy_number: Policy number
            policy_details: Dictionary containing policy details
            
        Returns:
            True if email sent successfully, False otherwise
        """
        effective_date = policy_details.get('effective_date', 'N/A')
        expiry_date = policy_details.get('expiry_date', 'N/A')
        selected_tier = policy_details.get('selected_tier', 'elite').title()
        destination = policy_details.get('destination', 'N/A')
        
        subject = f"Your Travel Insurance Policy - {policy_number}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .policy-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #0066cc; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Travel Insurance Policy</h1>
                </div>
                <div class="content">
                    <p>Dear Traveler,</p>
                    <p>As requested, please find your travel insurance policy details below.</p>
                    
                    <div class="policy-box">
                        <h2>Policy Information</h2>
                        <p><strong>Policy Number:</strong> {policy_number}</p>
                        <p><strong>Tier:</strong> {selected_tier}</p>
                        <p><strong>Destination:</strong> {destination}</p>
                        <p><strong>Coverage Period:</strong> {effective_date} to {expiry_date}</p>
                    </div>
                    
                    <p>Please keep this email for your records. You can also access your policy anytime through your account.</p>
                    
                    <p>If you have any questions about your policy, please don't hesitate to contact our support team.</p>
                    
                    <p>Safe travels!</p>
                    <p>Travel Insurance Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent upon your request.</p>
                    <p>If you have any questions, please contact our support team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Your Travel Insurance Policy

Dear Traveler,

As requested, please find your travel insurance policy details below.

Policy Information:
- Policy Number: {policy_number}
- Tier: {selected_tier}
- Destination: {destination}
- Coverage Period: {effective_date} to {expiry_date}

Please keep this email for your records. You can also access your policy anytime through your account.

If you have any questions about your policy, please don't hesitate to contact our support team.

Safe travels!
Travel Insurance Team

---
This email was sent upon your request.
If you have any questions, please contact our support team.
        """
        
        return self._send_email(to_email, subject, html_body, text_body)

