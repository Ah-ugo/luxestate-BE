import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html: str) -> bool:
    """Send email via SMTP"""
    message = MIMEMultipart()
    message["From"] = f"LuxEstate <{settings.FROM_EMAIL}>"
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent to {to}")
        return True
    except aiosmtplib.SMTPException as e:
        logger.error(f"SMTP Email error: {e.code} {e.message}")
        return False
    except Exception as e:
        logger.error(f"Generic Email error: {e}")
        return False


async def send_booking_confirmation(booking, pdf_url: str) -> bool:
    """Send tour booking confirmation with PDF download link"""
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
        .ref-badge {{ background: #c9a84c; color: #0a0a0a; padding: 8px 20px; border-radius: 4px; font-size: 18px; font-weight: 700; letter-spacing: 3px; display: inline-block; margin: 20px 0; }}
        .cta-btn {{ display: block; background: linear-gradient(135deg, #c9a84c, #a08830); color: #0a0a0a; text-decoration: none; text-align: center; padding: 16px 32px; border-radius: 6px; font-size: 16px; font-weight: 700; letter-spacing: 2px; margin: 24px 0; }}
        .footer {{ padding: 24px 40px; text-align: center; color: #4a4a4a; font-size: 12px; border-top: 1px solid #2a2a2a; }}
        .gold {{ color: #c9a84c; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">LUXESTATE</div>
          <div class="tagline">PREMIUM PROPERTY INVESTMENT</div>
        </div>
        <div class="body">
          <div class="title">Tour Booking Confirmed ✓</div>
          <div class="subtitle">Your tour has been successfully scheduled</div>
          
          <div style="text-align:center">
            <div class="ref-badge">{booking.booking_ref}</div>
          </div>

          <div class="detail-card">
            <div class="detail-row">
              <span class="label">Property</span>
              <span class="value">{booking.listing_title}</span>
            </div>
            <div class="detail-row">
              <span class="label">Address</span>
              <span class="value">{booking.listing_address}</span>
            </div>
            <div class="detail-row">
              <span class="label">Tour Date</span>
              <span class="value">{booking.tour_slot.date}</span>
            </div>
            <div class="detail-row">
              <span class="label">Tour Time</span>
              <span class="value">{booking.tour_slot.time}</span>
            </div>
            <div class="detail-row">
              <span class="label">Guest Name</span>
              <span class="value">{booking.first_name} {booking.last_name}</span>
            </div>
            <div class="detail-row">
              <span class="label">Guests</span>
              <span class="value">{booking.num_guests}</span>
            </div>
            <div class="detail-row">
              <span class="label">Amount Paid</span>
              <span class="value gold">${booking.amount_paid / 100:,.2f}</span>
            </div>
          </div>

          <p style="color: #8a7a5a; font-size: 14px; line-height: 1.8;">
            Your tour registration form has been generated. Please download it below, 
            complete any required fields, and bring it to your tour appointment. 
            Our agent will meet you at the property.
          </p>

          <a href="{pdf_url}" class="cta-btn">⬇ DOWNLOAD TOUR FORM</a>

          <p style="color: #4a4a4a; font-size: 13px; line-height: 1.8;">
            Need to reschedule? Contact us at least 48 hours before your tour.<br>
            📞 +1 (212) 555-0199 &nbsp;|&nbsp; 📧 concierge@luxestate.us
          </p>
        </div>
        <div class="footer">
          © 2024 LuxEstate Properties Ltd. All rights reserved.<br>
          1 Adeola Odeku Street, Victoria Island, Lagos, Nigeria.
        </div>
      </div>
    </body>
    </html>
    """
    return await send_email(
        to=booking.email,
        subject=f"✓ Tour Confirmed - {booking.booking_ref} | LuxEstate",
        html=html,
    )


async def send_contact_notification(message) -> bool:
    """Notify admin of new contact message"""
    html = f"""
    <h2>New Contact Message</h2>
    <p><strong>From:</strong> {message.name} ({message.email})</p>
    <p><strong>Subject:</strong> {message.subject}</p>
    <p><strong>Message:</strong><br>{message.message}</p>
    """
    return await send_email(
        to=settings.FROM_EMAIL,
        subject=f"New Contact: {message.subject}",
        html=html,
    )
