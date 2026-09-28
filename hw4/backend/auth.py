"""Accounts and sign-in for Campus Customs.

Passwords
    Stored only as salted PBKDF2-SHA256 hashes:
        pbkdf2_sha256$<iterations>$<salt hex>$<digest hex>
    600,000 iterations and a random 16-byte salt per user. Older accounts use
    the original format pbkdf2_sha256$<salt>$<digest> (120,000 iterations);
    they still verify, and are re-hashed to the current format on the next
    successful login.

Sessions
    Logging in creates a random 256-bit token, sent to the browser in an
    HttpOnly, SameSite=Lax cookie. The database stores only the SHA-256 of the
    token (sessions table), so a leaked database can't be used to log in.

Brute-force protection
    Repeated failures for the same email or from the same client are locked out
    for a while, and failures return one generic message so attackers can't tell
    whether an email has an account.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from pydantic import BaseModel

from db import connect

router = APIRouter(prefix="/api/auth", tags=["auth"])

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
LEGACY_ITERATIONS = 120_000  # accounts created before this module
SALT_BYTES = 16

SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
SECURE_COOKIES = os.getenv("COOKIE_SECURE", "0") == "1"  # set to 1 when served over HTTPS

MIN_PASSWORD, MAX_PASSWORD = 8, 128  # the max stops huge inputs from tying up the hasher
COMMON_PASSWORDS = {"password", "password1", "12345678", "123456789", "qwerty123", "iloveyou", "yale1701", "letmein1"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_FAILURES = 5  # per email
MAX_CLIENT_FAILURES = 20  # per client address, across all emails
LOCKOUT_SECONDS = 15 * 60
MAX_SIGNUPS_PER_HOUR = 10

GENERIC_LOGIN_ERROR = "Incorrect email or password."


# ---- password hashing ----------------------------------------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:
        algorithm, iterations, salt, digest = parts
    elif len(parts) == 3:  # legacy format without an iteration count
        algorithm, salt, digest = parts
        iterations = str(LEGACY_ITERATIONS)
    else:
        return False
    if algorithm != ALGORITHM:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(candidate, digest)  # constant-time comparison


def needs_rehash(stored: str) -> bool:
    parts = stored.split("$")
    return len(parts) != 4 or int(parts[1]) < ITERATIONS


# Used when an email has no account, so the response takes as long as a real check.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---- rate limiting (in memory; resets when the server restarts) -----------------------

_failures: dict[str, deque[float]] = defaultdict(deque)
_signups: dict[str, deque[float]] = defaultdict(deque)


def _recent(events: deque[float], window: float) -> deque[float]:
    cutoff = time.time() - window
    while events and events[0] < cutoff:
        events.popleft()
    return events


def _client(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_lockout(email_key: str, client_key: str) -> None:
    if (
        len(_recent(_failures[email_key], LOCKOUT_SECONDS)) >= MAX_FAILURES
        or len(_recent(_failures[client_key], LOCKOUT_SECONDS)) >= MAX_CLIENT_FAILURES
    ):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Please wait 15 minutes and try again.",
        )


# ---- sessions --------------------------------------------------------------------------


def ensure_sessions_table() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _start_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 24 * 3600,
        httponly=True,  # page scripts (and injected ones) can't read it
        samesite="lax",  # not sent on cross-site form posts
        secure=SECURE_COOKIES,
        path="/",
    )


def current_user(token: str | None) -> dict[str, Any] | None:
    """The signed-in user for a session cookie, or None."""
    if not token:
        return None
    with connect() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.name, u.first_name, u.last_name, u.email
            FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > datetime('now')
            """,
            (_token_hash(token),),
        ).fetchone()
    return _public_user(row) if row else None


def _public_user(row: sqlite3.Row) -> dict[str, Any]:
    """User fields safe to send to the browser. Never includes the password hash."""
    first = row["first_name"] or (row["name"] or "").split(" ")[0]
    return {"id": row["id"], "name": row["name"], "first_name": first, "last_name": row["last_name"], "email": row["email"]}


# ---- endpoints -------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, response: Response) -> dict[str, Any]:
    client = _client(request)
    if len(_recent(_signups[client], 3600)) >= MAX_SIGNUPS_PER_HOUR:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many new accounts from here. Please try later.")

    first, last = body.first_name.strip(), body.last_name.strip()
    email = _normalize_email(body.email)
    if not first or not last or len(first) > 60 or len(last) > 60:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please enter your first and last name.")
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please enter a valid email address.")
    if not MIN_PASSWORD <= len(body.password) <= MAX_PASSWORD:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Password must be {MIN_PASSWORD}-{MAX_PASSWORD} characters.")
    if body.password.lower() in COMMON_PASSWORDS or body.password.lower() == email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That password is too easy to guess. Please choose another.")

    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", first, last, email, hash_password(body.password)),
            )
            user_id = cur.lastrowid
            row = conn.execute("SELECT id, name, first_name, last_name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists. Try logging in.")

    _signups[client].append(time.time())
    _start_session(response, user_id)
    return {"user": _public_user(row)}


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response) -> dict[str, Any]:
    email = _normalize_email(body.email)
    client = _client(request)
    _check_lockout(f"email:{email}", f"client:{client}")

    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, first_name, last_name, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    password = body.password[:MAX_PASSWORD]
    ok = verify_password(password, row["password_hash"] if row else _DUMMY_HASH) and row is not None
    if not ok:
        _failures[f"email:{email}"].append(time.time())
        _failures[f"client:{client}"].append(time.time())
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, GENERIC_LOGIN_ERROR)

    _failures.pop(f"email:{email}", None)
    if needs_rehash(row["password_hash"]):  # upgrade older, weaker hashes
        with connect() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), row["id"]))
    _start_session(response, row["id"])
    return {"user": _public_user(row)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, cc_session: str | None = Cookie(default=None)) -> Response:
    if cc_session:
        with connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(cc_session),))
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    user = current_user(cc_session)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in.")
    return {"user": user}
