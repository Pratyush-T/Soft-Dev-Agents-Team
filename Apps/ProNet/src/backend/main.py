"""Root ASGI gateway export for ProNet backend.

Allows running uvicorn main:app directly from the backend root.
"""
from app.main import app

__all__ = ["app"]
