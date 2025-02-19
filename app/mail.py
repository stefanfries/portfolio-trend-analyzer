import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException
from app.settings import SendMailSettings

def send_mail(subject: str, message: str, to_email: str):

    send_mail_settings = SendMailSettings()

    print(f"Sending email to {to_email} with subject {subject}")
    
    msg = MIMEMultipart()
    msg["From"] = send_mail_settings.smtp_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # attach the message to the MIMEMultipart object
    msg.attach(MIMEText(message, "plain"))

    # establish a secure session with GMX´s outgoring SMTP server using your GMX account
    try:
        with smtplib.SMTP(send_mail_settings.smtp_host, send_mail_settings.smtp_port) as server:
            server.starttls()   # secure the connection
            server.login(send_mail_settings.smtp_username, send_mail_settings.smtp_password)
            text = msg.as_string()
            server.sendmail(send_mail_settings.smtp_username, to_email, text)
    except SMTPException as e:
        print(f"Error: unable to send email. {e}")
        server.sendmail(send_mail_settings.smtp_username, to_email, text)
    
