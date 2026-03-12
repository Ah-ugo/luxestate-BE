from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

GOLD = colors.HexColor("#C9A84C")
DARK = colors.HexColor("#1A1A1A")
LIGHT_GOLD = colors.HexColor("#F5E8C0")
WHITE = colors.white
GRAY = colors.HexColor("#8A8A8A")


def generate_tour_form_pdf(booking) -> bytes:
    """Generate a luxury tour registration form as PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontSize=28,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica-Bold",
        letterSpacing=8,
    )
    sub_header_style = ParagraphStyle(
        "SubHeader",
        parent=styles["Normal"],
        fontSize=9,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica",
        letterSpacing=3,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=GOLD,
        spaceAfter=8,
        spaceBefore=16,
        fontName="Helvetica-Bold",
        letterSpacing=2,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK,
        spaceAfter=6,
        fontName="Helvetica",
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GRAY,
        spaceAfter=4,
        fontName="Helvetica",
    )

    story = []

    # Header block
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("LUXESTATE", header_style))
    story.append(Paragraph("PREMIUM PROPERTY INVESTMENT", sub_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4 * mm))
    story.append(Paragraph("PROPERTY TOUR REGISTRATION FORM", ParagraphStyle(
        "FormTitle", parent=styles["Normal"], fontSize=13, textColor=DARK,
        alignment=TA_CENTER, fontName="Helvetica-Bold", letterSpacing=2, spaceAfter=2
    )))
    story.append(Paragraph("Please bring this completed form to your tour appointment", small_style.__class__(
        "SmallCenter", parent=small_style, alignment=TA_CENTER
    )))
    story.append(Spacer(1, 6 * mm))

    # Booking Reference Box
    ref_data = [
        [
            Paragraph("BOOKING REFERENCE", ParagraphStyle("", parent=small_style, textColor=GRAY, letterSpacing=2)),
            Paragraph("STATUS"),
            Paragraph("PAYMENT"),
        ],
        [
            Paragraph(booking.booking_ref, ParagraphStyle("", fontSize=18, textColor=GOLD, fontName="Helvetica-Bold")),
            Paragraph("✓ CONFIRMED", ParagraphStyle("", fontSize=10, textColor=colors.HexColor("#2ECC71"), fontName="Helvetica-Bold")),
            Paragraph(f"₦{booking.amount_paid:,.0f}", ParagraphStyle("", fontSize=12, textColor=DARK, fontName="Helvetica-Bold")),
        ],
    ]
    ref_table = Table(ref_data, colWidths=[70 * mm, 50 * mm, 50 * mm])
    ref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F4E8")),
        ("BOX", (0, 0), (-1, -1), 1, GOLD),
        ("LINEAFTER", (0, 0), (1, -1), 0.5, GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 6 * mm))

    # Section: Property Details
    story.append(Paragraph("1. PROPERTY INFORMATION", section_title_style))
    prop_data = [
        ["Property Name:", booking.listing_title, "Tour Date:", booking.tour_slot.date],
        ["Address:", booking.listing_address[:40] + "..." if len(booking.listing_address) > 40 else booking.listing_address,
         "Tour Time:", booking.tour_slot.time],
    ]
    prop_table = Table(prop_data, colWidths=[40 * mm, 70 * mm, 30 * mm, 30 * mm])
    prop_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TEXTCOLOR", (2, 0), (2, -1), GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
    ]))
    story.append(prop_table)

    # Section: Guest Details
    story.append(Paragraph("2. GUEST INFORMATION", section_title_style))
    guest_data = [
        ["Full Name:", f"{booking.first_name} {booking.last_name}", "Number of Guests:", str(booking.num_guests)],
        ["Email:", booking.email, "Phone:", booking.phone],
    ]
    guest_table = Table(guest_data, colWidths=[40 * mm, 70 * mm, 40 * mm, 20 * mm])
    guest_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("TEXTCOLOR", (2, 0), (2, -1), GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
    ]))
    story.append(guest_table)

    # Message
    if booking.message:
        story.append(Paragraph("Notes/Special Requests:", section_title_style))
        story.append(Paragraph(booking.message, body_style))

    # Section: Checklist
    story.append(Paragraph("3. PRE-TOUR CHECKLIST", section_title_style))
    checklist_items = [
        "□  Bring a valid government-issued ID (National ID, International Passport, or Driver's License)",
        "□  Bring this completed form to the tour appointment",
        "□  Arrive 10 minutes before the scheduled time",
        "□  Wear comfortable shoes suitable for property inspection",
        "□  Prepare any questions you have about the property or terms",
        "□  Proof of income or financial statement may be requested",
        "□  Photography is allowed for personal reference only",
    ]
    for item in checklist_items:
        story.append(Paragraph(item, ParagraphStyle("Check", parent=body_style, fontSize=10, spaceAfter=5)))

    # Section: Terms
    story.append(Paragraph("4. TERMS & CONDITIONS", section_title_style))
    terms = """
    By completing this form and attending the tour, you agree to the following:
    (a) The tour fee of ₦160,000 is non-refundable but may be applied toward the purchase or rental deposit if a transaction is completed within 30 days.
    (b) All information provided must be accurate. LuxEstate reserves the right to cancel tours based on inaccurate information.
    (c) Photography and videography is permitted for personal reference only. Commercial use is prohibited without written consent.
    (d) LuxEstate agents reserve the right to terminate a tour if the guest violates property rules.
    (e) This form does not constitute a purchase agreement or tenancy agreement.
    """
    story.append(Paragraph(terms.strip(), ParagraphStyle("Terms", parent=body_style, fontSize=8.5, textColor=GRAY, leading=14)))

    # Signature Block
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DDDDDD"), spaceAfter=6 * mm))

    sig_data = [
        [
            Paragraph("Guest Signature:", ParagraphStyle("", parent=small_style, textColor=GRAY)),
            Paragraph("Date:", ParagraphStyle("", parent=small_style, textColor=GRAY)),
            Paragraph("Agent Signature:", ParagraphStyle("", parent=small_style, textColor=GRAY)),
        ],
        [
            Paragraph("_" * 30, ParagraphStyle("", fontSize=10, textColor=DARK)),
            Paragraph("_" * 15, ParagraphStyle("", fontSize=10, textColor=DARK)),
            Paragraph("_" * 30, ParagraphStyle("", fontSize=10, textColor=DARK)),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[65 * mm, 35 * mm, 70 * mm])
    sig_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    story.append(sig_table)

    # Footer
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4 * mm))
    story.append(Paragraph(
        "LuxEstate Properties Ltd. | 1 Adeola Odeku Street, Victoria Island, Lagos, Nigeria | +234 800 589 7837 | hello@luxestate.ng",
        ParagraphStyle("Footer", parent=small_style, alignment=TA_CENTER, textColor=GRAY)
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
