
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


def build_database_url():
    """
    Prefer DATABASE_URL for hosted PostgreSQL.

    Fall back to individual DB_* variables
    for local development.
    """

    configured_url = os.getenv("DATABASE_URL")

    if configured_url:
        # Normalize common PostgreSQL URL schemes.
        if configured_url.startswith("postgres://"):
            configured_url = (
                "postgresql+psycopg://"
                + configured_url[len("postgres://"):]
            )
        elif configured_url.startswith("postgresql://"):
            configured_url = (
                "postgresql+psycopg://"
                + configured_url[len("postgresql://"):]
            )

        if not configured_url.startswith(
            "postgresql+psycopg://"
        ):
            raise RuntimeError(
                "DATABASE_URL must use PostgreSQL with psycopg."
            )

        return configured_url

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "machinedoctor")

    if not db_user or not db_password:
        raise RuntimeError(
            "DB_USER and DB_PASSWORD must be configured."
        )

    return URL.create(
        drivername="postgresql+psycopg",
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name,
    )


database_url = build_database_url()

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def check_database_connection():
    with engine.connect() as connection:
        return (
            connection.execute(text("SELECT 1")).scalar_one()
            == 1
        )
