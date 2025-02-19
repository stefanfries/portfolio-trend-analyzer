from pydantic_settings import BaseSettings, SettingsConfigDict


class SendMailSettings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_email: str # the 'From' email address

    model_config = SettingsConfigDict(
        env_prefix = "SMTP_",  # Prefix for environment variables
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra="ignore", # Ignore extra fields
    )

class APISettings(BaseSettings):
    api_url: str
    api_wakeup_retries: int
    api_wakeup_retries_delay_seconds: int

    model_config = SettingsConfigDict(
        env_prefix = "API_",  # Prefix for environment variables
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra="ignore", # Ignore extra fields
    )
