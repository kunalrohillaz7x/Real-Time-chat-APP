import os
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Switch driver from psycopg2 to pg8000 (pure Python, no DLLs)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

# Strip params pg8000 doesn't understand (sslmode, channel_binding)
parsed = urlparse(DATABASE_URL)
qs = parse_qs(parsed.query)
qs.pop("sslmode", None)
qs.pop("channel_binding", None)
clean_query = urlencode(qs, doseq=True)
DATABASE_URL = urlunparse(parsed._replace(query=clean_query))

# Create SSL context for Neon's TLS requirement
ssl_context = ssl.create_default_context()

engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl_context": ssl_context},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()