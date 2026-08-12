from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


def sqlalchemy_url(raw_url: str) -> str:
    """Railway gives postgres://; SQLAlchemy 2 wants postgresql+psycopg://."""
    url = (raw_url or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = sqlalchemy_url(settings.database_url)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if IS_SQLITE else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=not IS_SQLITE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _existing_columns(table: str) -> set[str]:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def migrate_schema() -> None:
    """Add new columns on existing DBs (create_all does not alter tables)."""
    timestamp_type = "DATETIME" if IS_SQLITE else "TIMESTAMP"
    needed = {
        "stripe_customer_id": "VARCHAR(255)",
        "stripe_subscription_id": "VARCHAR(255)",
        "plan_status": "VARCHAR(32) DEFAULT 'free'",
        "reset_token_hash": "VARCHAR(64)",
        "reset_token_expires": timestamp_type,
    }
    existing = _existing_columns("users")
    with engine.begin() as conn:
        for name, col_type in needed.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {col_type}"))
