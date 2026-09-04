"""Shared pytest fixtures.

Environment variables are set *before* the app is imported, because
``config.py`` reads them at import time (SECRET_KEY, DATABASE_URL). We point the
app at a throwaway SQLite file so tests never touch the real database.
"""
import os
import tempfile

import pytest

# Must be set before `app`/`config` is imported.
os.environ.setdefault("secret_key", "test-secret-key")

# Use a temporary SQLite file (a file, not :memory:, so the connection pool
# shares the same database across requests).
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from app import app as flask_app  # noqa: E402
from extensions import db  # noqa: E402


@pytest.fixture()
def app():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
