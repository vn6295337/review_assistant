#!/usr/bin/env python3
"""auth.py ─ Authentication helpers (JWT + password)
----------------------------------------------------
• Uses environment variable `RAG_SECRET_KEY` for signing (falls back to a dev key).
• All timestamps are generated in Asia/Kolkata (UTC+5:30).
• Provides `authenticate_user`, `create_jwt`, `decode_jwt`, and `token_required` decorator.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable, Any, Dict, Optional, TypeVar

import jwt
from flask import request, jsonify
from werkzeug.security import check_password_hash

from .models import User  # local app import

# ───────────────────────────────────────────────────────────
# 1. Configuration
# ───────────────────────────────────────────────────────────

IST = timezone(timedelta(hours=5, minutes=30))  # UTC+5:30
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret")  # fallback only for dev
TOKEN_TTL_DAYS = int(os.getenv("RAG_TOKEN_TTL", "1"))  # default 1 day

# ───────────────────────────────────────────────────────────
# 2. Core helpers
# ───────────────────────────────────────────────────────────

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Return a `User` if username/password match, else `None`."""
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def create_jwt(user_id: int) -> str:
    """Generate a signed JWT for `user_id`."""
    now = datetime.now(tz=IST)
    payload: Dict[str, Any] = {
        "exp": now + timedelta(days=TOKEN_TTL_DAYS),
        "iat": now,
        "sub": user_id,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Return JWT payload if valid, otherwise `None`."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None  # token expired
    except jwt.InvalidTokenError:
        return None  # bad token

# ───────────────────────────────────────────────────────────
# 3. Decorator for protected routes
# ───────────────────────────────────────────────────────────

F = TypeVar("F", bound=Callable[..., Any])

def token_required(func: F) -> F:  # type: ignore[override]
    """Flask route decorator enforcing JWT auth.

    The wrapped view will receive the authenticated `User` instance as its
    first positional argument.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[override]
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else None

        if not token:
            return jsonify({"error": "Authorization token missing"}), 401

        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        user = User.query.get(payload.get("sub"))
        if not user:
            return jsonify({"error": "User not found"}), 401

        return func(user, *args, **kwargs)  # Pass user to the view

    return wrapper  # type: ignore[return-value]
