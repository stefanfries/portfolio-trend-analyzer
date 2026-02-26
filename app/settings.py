from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SendMailSettings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_username: SecretStr
    smtp_password: SecretStr
    smtp_email: EmailStr  # the 'From' email address

    model_config = SettingsConfigDict(
        env_prefix="SMTP_",  # Prefix for environment variables
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields
    )


class APISettings(BaseSettings):
    api_url: str
    api_history_path: str
    api_timeout: float
    api_wakeup_retries: int
    api_wakeup_retries_delay_seconds: int

    model_config = SettingsConfigDict(
        env_prefix="API_",  # Prefix for environment variables
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields
    )


class SignalHistorySettings(BaseSettings):
    """Settings for signal history tracking and confirmation."""

    signal_history_retention_days: int = 30
    signal_history_market_close_hour: int = 22
    signal_history_market_close_minute: int = 0

    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HISTORY_",  # Prefix for environment variables
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields
    )
