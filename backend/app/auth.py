import hashlib
import hmac
import time

from fastapi import Cookie, HTTPException, status

from app.config import get_settings


COOKIE_NAME = "datamart_admin_session"


def create_admin_session(username: str) -> str:
    settings = get_settings()

    if not settings.admin_session_secret:
        raise RuntimeError(
            "ADMIN_SESSION_SECRET is not configured."
        )

    expires_at = int(
        time.time()
        + settings.admin_session_hours * 3600
    )

    payload = f"{username}:{expires_at}"

    signature = hmac.new(
        settings.admin_session_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload}:{signature}"


def verify_admin_session(
    token: str | None,
) -> bool:
    if not token:
        return False

    settings = get_settings()

    if not settings.admin_session_secret:
        return False

    try:
        username, expires_at, signature = token.split(
            ":",
            2,
        )

        expires_at_int = int(expires_at)

        if expires_at_int < int(time.time()):
            return False

        if username != settings.admin_username:
            return False

        payload = f"{username}:{expires_at}"

        expected_signature = hmac.new(
            settings.admin_session_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            signature,
            expected_signature,
        )

    except (ValueError, TypeError):
        return False


def require_admin(
    datamart_admin_session: str | None = Cookie(
        default=None,
        alias=COOKIE_NAME,
    ),
):
    if not verify_admin_session(
        datamart_admin_session
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required.",
        )

    return True