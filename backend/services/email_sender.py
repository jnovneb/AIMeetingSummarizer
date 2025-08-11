# services/email_sender.py
# Send emails with attachment via SMTP. Configure via environment variables.
# For production prefer a transactional email provider or authenticated SMTP.

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", None)         # sender email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", None) # smtp password or app password
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

SENDER_NAME = os.getenv("SENDER_NAME", "AI Meeting Summarizer")


def send_email_with_attachment(to_email: str, subject: str, body: str, attachment_path: str, attachment_name: str = None):
    """
    Send an email with a PDF attachment.
    Requires SMTP_USER and SMTP_PASSWORD environment variables.
    """
    if SMTP_USER is None or SMTP_PASSWORD is None:
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must be set as environment variables to send email.")

    if attachment_name is None:
        import os
        attachment_name = os.path.basename(attachment_path)

    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    # Plain text body
    msg.attach(MIMEText(body, "plain"))

    # Attachment
    with open(attachment_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=attachment_name)
        msg.attach(part)

    # Send
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    try:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())
    finally:
        server.quit()
