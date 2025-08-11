# services/pdf_generator.py
# Create a simple, clean PDF containing meeting metadata, transcript, summary, and tasks.
# Uses reportlab.

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from datetime import datetime
import textwrap
import os

def create_meeting_pdf(transcript: str, summary: str, tasks: str, output_path: str,
                       title: str = "Meeting Summary", metadata: dict = None):
    """
    Generate a PDF with a header, transcript, summary and tasks.
    :param transcript: full transcript text
    :param summary: summary text
    :param tasks: bullet list or newline-separated tasks
    :param output_path: where to save the PDF
    :param title: title shown on PDF
    :param metadata: optional dict (e.g., {"date": "...", "language": "en"})
    """
    if metadata is None:
        metadata = {}

    page_width, page_height = A4
    margin = 20 * mm
    max_width = page_width - 2 * margin
    cursor_y = page_height - margin

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(title)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, cursor_y, title)
    cursor_y -= 10 * mm

    c.setFont("Helvetica", 9)
    meta_lines = [
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]
    for k, v in metadata.items():
        meta_lines.append(f"{k.capitalize()}: {v}")

    for line in meta_lines:
        c.drawString(margin, cursor_y, line)
        cursor_y -= 6 * mm

    # Helper to draw wrapped paragraphs
    def draw_paragraph(text, fontsize=10, leading=12):
        nonlocal cursor_y
        wrapper = textwrap.TextWrapper(width=100)
        lines = []
        # use whitespace break to avoid losing words
        for raw_line in text.split("\n"):
            wrapped = textwrap.wrap(raw_line, width=85)
            if not wrapped:
                lines.append("")
            else:
                lines.extend(wrapped)
        c.setFont("Helvetica", fontsize)
        for ln in lines:
            if cursor_y < margin + 40:  # start new page
                c.showPage()
                cursor_y = page_height - margin
                c.setFont("Helvetica", fontsize)
            c.drawString(margin, cursor_y, ln)
            cursor_y -= (leading * 0.9) * mm  # adjust spacing

    # Summary section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, cursor_y, "Summary")
    cursor_y -= 8 * mm
    draw_paragraph(summary, fontsize=10, leading=6)

    cursor_y -= 4 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, cursor_y, "Tasks / Action Items")
    cursor_y -= 8 * mm
    draw_paragraph(tasks, fontsize=10, leading=6)

    cursor_y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, cursor_y, "Full Transcript (truncated)")
    cursor_y -= 8 * mm
    # For the transcript, include a truncated version to avoid huge PDFs.
    transcript_to_draw = transcript if len(transcript) < 15000 else transcript[:15000] + "\n\n[Transcript truncated]"
    draw_paragraph(transcript_to_draw, fontsize=9, leading=5)

    c.save()
    return os.path.abspath(output_path)
