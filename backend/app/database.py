from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_schema() -> None:
    """Add new columns on existing DBs (create_all does not alter tables)."""
    statements = [
        "ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN plan_status VARCHAR(32) DEFAULT 'free'",
        "ALTER TABLE users ADD COLUMN reset_token_hash VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN reset_token_expires DATETIME",
    ]
    with engine.begin() as conn:
        for sql in statements:
            try:
                conn.execute(text(sql))
            except Exception:
                # Column already exists
                pass
