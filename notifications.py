"""
Notification service: sends status updates via email and WhatsApp.

For WhatsApp integration, this uses the Twilio API (free trial or paid account required).
Set environment variables:
  - TWILIO_ACCOUNT_SID
  - TWILIO_AUTH_TOKEN
  - TWILIO_PHONE_FROM (e.g., +1234567890)

For email, uses standard Flask app.config SMTP settings.
"""
import os
from flask import current_app


def send_email(to_addr: str, subject: str, body: str):
    """Send email notification (best-effort).

    Uses SMTP if configured in app.config, otherwise logs to app logger.
    """
    import smtplib
    from email.message import EmailMessage

    mail_server = current_app.config.get('MAIL_SERVER')
    if not mail_server:
        current_app.logger.info(
            'EMAIL (console) -> To: %s Subject: %s\n%s', to_addr, subject, body
        )
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = current_app.config.get('MAIL_FROM', 'noreply@riseuplink.local')
    msg['To'] = to_addr
    msg.set_content(body)

    try:
        port = current_app.config.get('MAIL_PORT', 587)
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        username = current_app.config.get('MAIL_USERNAME')
        password = current_app.config.get('MAIL_PASSWORD')

        if use_tls:
            server = smtplib.SMTP(mail_server, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, port, timeout=10)

        if username and password:
            server.login(username, password)

        server.send_message(msg)
        server.quit()
        current_app.logger.info('Email sent to %s', to_addr)
    except Exception as exc:
        current_app.logger.warning('Failed to send email to %s: %s', to_addr, exc)


def send_whatsapp(phone_number: str, message: str):
    """Send WhatsApp message via Twilio.

    Requires:
      - TWILIO_ACCOUNT_SID env var
      - TWILIO_AUTH_TOKEN env var
      - TWILIO_PHONE_FROM env var (Twilio phone number, e.g., +1234567890)

    phone_number should be in international format (e.g., +256701234567)
    """
    try:
        from twilio.rest import Client
    except ImportError:
        current_app.logger.warning('Twilio not installed. Install with: pip install twilio')
        return

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE_FROM')

    if not (account_sid and auth_token and from_phone):
        current_app.logger.warning(
            'WhatsApp not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_FROM'
        )
        return

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            from_=f'whatsapp:{from_phone}',
            body=message,
            to=f'whatsapp:{phone_number}'
        )
        current_app.logger.info('WhatsApp sent to %s (SID: %s)', phone_number, msg.sid)
    except Exception as exc:
        current_app.logger.warning('Failed to send WhatsApp to %s: %s', phone_number, exc)


def notify_applicant(youth_user, opportunity_title: str, status: str):
    """Send application status notification via email and/or WhatsApp.
    
    Respects youth's preferred_feedback method (email or whatsapp).

    Args:
        youth_user: User object (youth)
        opportunity_title: Title of the opportunity
        status: Application status (e.g., 'Offered', 'UnderReview', 'NotSelected')
    """
    subject = f'Application Status Update: {opportunity_title}'
    body = f"""Hello {youth_user.full_name},

Your application for '{opportunity_title}' has been updated to: {status}.

Please log in to your RiseUp Link account to view more details.

Regards,
RiseUp Link Team"""

    # Determine preferred contact method from YouthProfile or User
    preferred_method = 'email'  # default
    if hasattr(youth_user, 'youth_profile') and youth_user.youth_profile:
        preferred_method = youth_user.youth_profile.preferred_feedback
    elif hasattr(youth_user, 'preferred_contact'):
        preferred_method = youth_user.preferred_contact

    # Send via preferred method
    if preferred_method == 'whatsapp':
        # Send WhatsApp if phone number available
        whatsapp_number = None
        if hasattr(youth_user, 'youth_profile') and youth_user.youth_profile:
            whatsapp_number = youth_user.youth_profile.whatsapp_number or youth_user.youth_profile.phone_number
        else:
            whatsapp_number = youth_user.whatsapp_number or youth_user.phone_number
            
        if whatsapp_number:
            whatsapp_msg = f"Hello {youth_user.full_name}, your application for '{opportunity_title}' is now: {status}. Check RiseUp Link for details."
            send_whatsapp(whatsapp_number, whatsapp_msg)
        else:
            # Fallback to email if no WhatsApp number
            if youth_user.email:
                send_email(youth_user.email, subject, body)
    else:
        # Send email if available (default preference)
        if youth_user.email:
            send_email(youth_user.email, subject, body)


def create_in_app_notification(user_id: int, title: str, message: str, link: str = None):
    """Create a notification record in the database for in-app delivery.

    Avoids importing models at module import time to prevent circular imports.
    """
    try:
        from models import db, Notification, User
        # Ensure user exists
        u = User.query.get(user_id)
        if not u:
            current_app.logger.warning('Tried to create notification for missing user %s', user_id)
            return
        n = Notification(user_id=user_id, title=title, message=message, link=link)
        db.session.add(n)
        db.session.commit()
        current_app.logger.info('In-app notification created for user %s: %s', user_id, title)
    except Exception as exc:
        current_app.logger.warning('Failed to create in-app notification: %s', exc)
