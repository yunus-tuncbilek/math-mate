"""Application configuration.

Values are read from the environment (see ``.env.example``). The database URL
defaults to a local SQLite file so `python app.py` works out of the box, but
setting ``DATABASE_URL`` (e.g. a Supabase/Postgres connection string) is a
one-line swap with no code changes.
"""
import os

from dotenv import load_dotenv

# Load .env before any config values are read, so every entry point
# (python app.py, flask CLI, seed.py) honours it consistently.
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

_DEFAULT_SQLITE = "sqlite:///" + os.path.join(DATA_DIR, "mathmate.db")


class Config:
    SECRET_KEY = os.getenv("secret_key")

    # DATABASE_URL takes precedence; falls back to a local SQLite file.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _DEFAULT_SQLITE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings (unchanged from the file-based app).
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXT = {".pdf"}
