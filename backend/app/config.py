from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "calvio-dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = "sqlite:///./calvio.db"
    frontend_url: str = "http://localhost:5173"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "Calvio <noreply@calvio.local>"
    # Stripe (Option A: business pays $19/mo). Leave blank until configured.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
