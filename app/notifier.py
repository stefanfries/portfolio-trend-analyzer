import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException

from app.settings import SendMailSettings


def send_mail(subject: str, message: str, to_email: str) -> None:

    send_mail_settings = SendMailSettings()

    msg = MIMEMultipart("alternative")
    msg["From"] = send_mail_settings.smtp_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Plain text version (for mail clients without HTML support)
    text = "This is a HTML email. Please enable HTML support in your email client."

    # HTML-Version
    html = message  # Here the HTML code will be inserted

    # add both parts to the MIMEMultipart message
    msg.attach(MIMEText(text, "plain"))  # if HTML i not supported
    msg.attach(MIMEText(html, "html"))  # HTML version

    # establish a secure session with GMX´s outgoring SMTP server using your GMX account
    try:
        with smtplib.SMTP(
            send_mail_settings.smtp_host, send_mail_settings.smtp_port
        ) as server:
            server.starttls()  # secure the connection
            server.login(
                send_mail_settings.smtp_username, send_mail_settings.smtp_password
            )
            text = msg.as_string()
            print(f"📬 Sending '{subject}' report to {to_email}")
            server.sendmail(send_mail_settings.smtp_username, to_email, text)
            print("📬 Email successfully sent.")
    except SMTPException as e:
        print(f"❌ Error: unable to send email. {e}")
        server.sendmail(send_mail_settings.smtp_username, to_email, text)
