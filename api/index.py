"""Vercel Python entrypoint. Vercel's @vercel/python builder looks for an ASGI
app named `app` in this module and wraps it; everything else lives in app/server.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.server import app  # noqa: E402,F401
