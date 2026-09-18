"""Vercel serverless entry point for the FastAPI application."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))

from app.database import Base, engine  # noqa: E402
import app.models  # noqa: E402,F401 - registers all SQLAlchemy models
from app.seed import main as seed_admin  # noqa: E402
from app.main import app  # noqa: E402

# Vercel has no pre-deploy shell hook on its free demo path.  Creating the
# version-one schema and idempotent administrator here makes a first deploy
# usable. Production deployments must use the Alembic path in Docker Compose.
if os.getenv("VERCEL"):
    Base.metadata.create_all(bind=engine, checkfirst=True)
    seed_admin()
