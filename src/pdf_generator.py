"""PDF report generation for Market Intelligence App."""

from datetime import datetime
from io import BytesIO
from typing import List, Dict, Optional
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib import colors


def _clean_text_for_pdf(text: str) -> str:
    """
    Clean and format text for PDF rendering.

    Handles markdown-style formatting and special characters.
    """
    if not text:
        return ""

    # Escape XML special characters first
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # Convert markdown bold to PDF bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Convert markdown headers to bold
    text = re.sub(r"^##\s+(.+?)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"^#\s+(.+?)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Convert bullet points
    text = re.sub(r"^[•\-\*]\s+", r"  • ", text, flags=re.MULTILINE)

    # Convert numbered lists
    text = re.sub(r"^\d+\.\s+", lambda m: f"  {m.group(0)}", text, flags=re.MULTILINE)

    # Convert line breaks to HTML breaks
    text = text.replace("\n\n", "<br/><br/>")
    text = text.replace("\n", "<br/>")

    # Handle tables - convert to simpler format
    text = re.sub(r"\|(.+?)\|", r"\1", text)
    text = re.sub(r"\-{3,}", "", text)

    return text


def create_pdf_report(
    title: str,
    conversation_id: Optional[int],
    trace_id: Optional[str],
    messages: List[Dict],
    user_name: Optional[str] = None,
    logo_path: str = "Ontario_Securities_Commission_logo.svg.png",
    report_type: str = "full",
) -> BytesIO:
    """
    Create a PDF report for conversation messages.

    Args:
        title: Report title
        conversation_id: Conversation ID
        trace_id: MLflow trace ID
        messages: List of message dictionaries with 'question' and 'answer' keys
        user_name: Name of the user generating the report
        logo_path: Path to OSC logo image
        report_type: 'full' for all messages, 'latest' for last message only

    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#2e6378"),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "CustomSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#666666"),
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2e6378"),
        spaceAfter=6,
        spaceBefore=12,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6,
        leading=16,
        leftIndent=0,
        rightIndent=0,
        alignment=TA_LEFT,
    )

    # Add logo (maintain aspect ratio with max dimensions)
    try:
        from reportlab.lib.utils import ImageReader
        import os

        # Check if logo file exists and get dimensions
        if os.path.exists(logo_path):
            img_reader = ImageReader(logo_path)
            img_width, img_height = img_reader.getSize()

            # Calculate aspect ratio
            aspect = img_height / float(img_width)

            # Set max width and calculate height maintaining aspect ratio
            max_width = 2.5 * inch
            max_height = 0.8 * inch

            # Scale to fit within max dimensions
            if aspect * max_width > max_height:
                # Height is the limiting factor
                logo_height = max_height
                logo_width = logo_height / aspect
            else:
                # Width is the limiting factor
                logo_width = max_width
                logo_height = logo_width * aspect

            logo = Image(logo_path, width=logo_width, height=logo_height)
            logo.hAlign = "CENTER"
            elements.append(logo)
            elements.append(Spacer(1, 0.3 * inch))
        else:
            print(f"⚠️ Logo file not found: {logo_path}")
    except Exception as e:
        print(f"⚠️ Could not load logo: {e}")

    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.1 * inch))

    # Add metadata
    date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    elements.append(Paragraph(f"Generated: {date_str}", subtitle_style))

    # Add conversation/trace ID and user
    metadata_data = []
    if user_name:
        metadata_data.append(["User:", user_name])
    if conversation_id:
        metadata_data.append(["Conversation ID:", str(conversation_id)])
    if trace_id:
        metadata_data.append(["Trace ID:", trace_id])

    if metadata_data:
        metadata_table = Table(metadata_data, colWidths=[1.5 * inch, 4.5 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2e6378")),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#666666")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3 * inch))

    # Add horizontal line
    elements.append(
        Table(
            [[""]],
            colWidths=[6.5 * inch],
            style=TableStyle([("LINEABOVE", (0, 0), (-1, 0), 2, colors.HexColor("#2e6378"))]),
        )
    )
    elements.append(Spacer(1, 0.2 * inch))

    # Filter messages based on report type
    if report_type == "latest" and messages:
        messages_to_include = [messages[-1]]
    else:
        messages_to_include = messages

    # Add messages
    for idx, msg in enumerate(messages_to_include, 1):
        # Question
        if report_type == "full":
            elements.append(Paragraph(f"Question {idx}", heading_style))
        else:
            elements.append(Paragraph("Question", heading_style))

        question_text = _clean_text_for_pdf(msg.get("question", ""))
        elements.append(Paragraph(question_text, body_style))
        elements.append(Spacer(1, 0.15 * inch))

        # Answer
        if report_type == "full":
            elements.append(Paragraph(f"Answer {idx}", heading_style))
        else:
            elements.append(Paragraph("Answer", heading_style))

        answer_text = _clean_text_for_pdf(msg.get("answer", "No answer available"))

        # Split answer into paragraphs to preserve formatting
        answer_paragraphs = answer_text.split("<br/><br/>")
        for para_text in answer_paragraphs:
            if para_text.strip():
                elements.append(Paragraph(para_text, body_style))
                elements.append(Spacer(1, 0.08 * inch))

        # Add separator between messages (except for last one)
        if idx < len(messages_to_include):
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(
                Table(
                    [[""]],
                    colWidths=[6.5 * inch],
                    style=TableStyle(
                        [("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor("#CCCCCC"))]
                    ),
                )
            )
            elements.append(Spacer(1, 0.2 * inch))

    # Add footer
    elements.append(Spacer(1, 0.5 * inch))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )
    elements.append(
        Paragraph(
            "Ontario Securities Commission - Market Surveillance Analyst<br/>Confidential Report",
            footer_style,
        )
    )

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer
    buffer.seek(0)
    return buffer
