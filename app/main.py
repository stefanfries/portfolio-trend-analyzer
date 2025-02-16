from app.mail import send_mail
from dotenv import find_dotenv, load_dotenv
import os


def main():
    load_dotenv(find_dotenv())
    print(f"smtp_host: {os.environ['SMTP_HOST']}")
    print(f"smtp_port: {os.environ['SMTP_PORT']}")
    print(f"smtp_username: {os.environ['SMTP_USERNAME']}")
    print(f"smtp_password: {os.environ['SMTP_PASSWORD']}")
    print(f"smtp_email: {os.environ['SMTP_EMAIL']}")

    subject = "Test Email"
    message = "This is a test email sent from Python."
    to_email = "stefan.fries.burgdorf@gmx.de"
    send_mail(subject, message, to_email)


if __name__ == "__main__":
    main()
