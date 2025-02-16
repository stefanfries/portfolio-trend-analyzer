import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException

from pydantic_settings import BaseSettings, SettingsConfigDict

class SendMailSettings(BaseSettings):
    smtp_host: str
    smtp_port: str
    smtp_username: str
    smtp_password: str
    smtp_email: str # the 'From' email address

    model_config = SettingsConfigDict(
        env_prefix = "SMTP_",  # Prefix for environment variables
        env_file = ".env",
        env_file_encoding = "utf-8",
    )

def send_mail(subject: str, message: str, to_email: str):

    settings = SendMailSettings()

    print(f"Sending email to {to_email} with subject {subject}")
    print(settings)
    
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    # attach the message to the MIMEMultipart object
    msg.attach(MIMEText(message, "plain"))

    # establish a secure session with GMX´s outgoring SMTP server using your GMX account
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()   # secure the connection
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.SMTP_USERNAME, to_email, text)
    except SMTPException as e:
        print(f"Error: unable to send email. {e}")
        server.sendmail(settings.SMTP_USERNAME, to_email, text)
    
