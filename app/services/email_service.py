import asyncio
import resend
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


def send_email_sync(to: str, subject: str, html: str, from_email: str):
    """Synchronous email sending function for Resend."""
    return resend.Emails.send({
        "from": from_email,
        "to": [to],
        "subject": subject,
        "html": html,
    })


async def send_email(to: str, subject: str, html: str) -> bool:
    """Send email via Resend in an async-friendly way."""
    from_email = f"LuxEstate <{settings.FROM_EMAIL}>"
    try:
        loop = asyncio.get_running_loop()
        email = await loop.run_in_executor(
            None, send_email_sync, to, subject, html, from_email
        )
        logger.info(f"Email sent to {to} via Resend. ID: {email['id']}")
        return True
    except Exception as e:
        logger.error(f"Resend Email error: {e}")
        return False


async def send_tour_request_acknowledgement(booking_details) -> bool:
    """Send tour request acknowledgement to the user."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: Georgia, serif; background: #0a0a0a; color: #e8d5a3; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #111111; }}
        .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%); padding: 40px; text-align: center; border-bottom: 1px solid #c9a84c; }}
        .logo {{ font-size: 28px; font-weight: 300; letter-spacing: 6px; color: #c9a84c; }}
        .tagline {{ font-size: 11px; letter-spacing: 3px; color: #8a7a5a; margin-top: 8px; }}
        .body {{ padding: 40px; }}
        .title {{ font-size: 24px; font-weight: 300; color: #e8d5a3; margin-bottom: 8px; }}
        .subtitle {{ color: #8a7a5a; font-size: 14px; margin-bottom: 32px; }}
        .detail-card {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 24px; margin-bottom: 24px; }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #2a2a2a; font-size: 14px; }}
        .detail-row:last-child {{ border-bottom: none; }}
        .label {{ color: #8a7a5a; }}
        .value {{ color: #e8d5a3; font-weight: 500; }}
        .footer {{ padding: 24px 40px; text-align: center; color: #4a4a4a; font-size: 12px; border-top: 1px solid #2a2a2a; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">LUXESTATE</div>
          <div class="tagline">PREMIUM PROPERTY INVESTMENT</div>
        </div>
        <div class="body">
          <div class="title">Tour Request Received</div>
          <div class="subtitle">We have received your tour request and will be in touch shortly.</div>

          <div class="detail-card">
            <div class="detail-row">
              <span class="label">Property</span>
              <span class="value">{booking_details.get("listing_title", "N/A")}</span>
            </div>
            <div class="detail-row">
              <span class="label">Guest Name</span>
              <span class="value">{booking_details.get("name", "N/A")}</span>
            </div>
          </div>

          <p style="color: #8a7a5a; font-size: 14px; line-height: 1.8;">
            Thank you for your interest. One of our luxury real estate experts will contact you within 24 hours to confirm your tour details and answer any questions you may have.
          </p>

          <p style="color: #4a4a4a; font-size: 13px; line-height: 1.8;">
            If you have any immediate questions, feel free to contact us.<br>
            📞 +1 (212) 555-0199 &nbsp;|&nbsp; 📧 concierge@luxestate.us
          </p>
        </div>
        <div class="footer">
          © 2026 LuxEstate Properties Ltd. All rights reserved.<br>
          152 West 57th St, New York, NY 10019.
        </div>
      </div>
    </body>
    </html>
    """
    return await send_email(
        to=booking_details['email'],
        subject=f"Tour Request Received | LuxEstate",
        html=html,
    )


async def send_password_reset_email(to: str, reset_link: str) -> bool:
    """Send password reset link to the user."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: Georgia, serif; background: #0a0a0a; color: #e8d5a3; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #111111; }}
        .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%); padding: 40px; text-align: center; border-bottom: 1px solid #c9a84c; }}
        .logo {{ font-size: 28px; font-weight: 300; letter-spacing: 6px; color: #c9a84c; }}
        .body {{ padding: 40px; }}
        .title {{ font-size: 24px; font-weight: 300; color: #e8d5a3; margin-bottom: 8px; }}
        .subtitle {{ color: #8a7a5a; font-size: 14px; margin-bottom: 32px; }}
        .cta-btn {{ display: block; background: linear-gradient(135deg, #c9a84c, #a08830); color: #0a0a0a; text-decoration: none; text-align: center; padding: 16px 32px; border-radius: 6px; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 24px 0; }}
        .footer {{ padding: 24px 40px; text-align: center; color: #4a4a4a; font-size: 12px; border-top: 1px solid #2a2a2a; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">LUXESTATE</div>
        </div>
        <div class="body">
          <div class="title">Reset Your Password</div>
          <div class="subtitle">A password reset was requested for your account.</div>
          <p style="color: #8a7a5a; font-size: 14px; line-height: 1.8;">
            Please click the button below to set a new password. This link is valid for one hour.
            If you did not request a password reset, please ignore this email.
          </p>
          <a href="{reset_link}" class="cta-btn">RESET PASSWORD</a>
          <p style="color: #4a4a4a; font-size: 12px; line-height: 1.8; text-align: center;">
            If you're having trouble, copy and paste this URL into your browser:<br>
            <span style="color: #666;">{reset_link}</span>
          </p>
        </div>
        <div class="footer">
          © 2026 LuxEstate Properties Ltd. All rights reserved.
        </div>
      </div>
    </body>
    </html>
    """
    return await send_email(to=to, subject="Reset Your LuxEstate Password", html=html)


async def send_contact_notification(message) -> bool:
    """Notify admin of new contact message"""
    phone_str = f"<p><strong>Phone:</strong> {message.phone}</p>" if message.phone else ""
    html = f"""
    <h2>New Contact Message</h2>
    <p><strong>From:</strong> {message.name} ({message.email})</p>
    {phone_str}
    <p><strong>Subject:</strong> {message.subject}</p>
    <p><strong>Message:</strong><br>{message.message}</p>
    """
    return await send_email(
        to=settings.FROM_EMAIL,
        subject=f"New Contact: {message.subject}",
        html=html,
    )
