"""Shared Flask extension instances.

These live in their own module so both ``app.py`` and ``models.py`` (and the
Alembic migration env) can import them without creating a circular import.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "login"
