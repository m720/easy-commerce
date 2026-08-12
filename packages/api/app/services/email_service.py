import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("app.email")


def send_email(to: str, subject: str, body: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        # Email not configured — skip silently in dev
        logger.debug("email skipped: SMTP not configured", extra={"email_subject": subject})
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg.attach(MIMEText(body, "html"))

    try:
        # The timeout is not optional. smtplib defaults to the global socket
        # timeout (usually None), so an unreachable SMTP host blocks the
        # background-task thread indefinitely — and since order confirmations
        # are sent per checkout, a broken mail provider quietly exhausts the
        # thread pool and takes the API down with it.
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to, msg.as_string())
        logger.info("email sent", extra={"email_subject": subject})
    except Exception as exc:  # noqa: BLE001
        # Never crash the request — but never fail silently either. This line
        # carries the request_id of the checkout that triggered it.
        logger.error(
            "email delivery failed",
            extra={"email_subject": subject, "smtp_host": settings.SMTP_HOST, "error": str(exc)},
        )
