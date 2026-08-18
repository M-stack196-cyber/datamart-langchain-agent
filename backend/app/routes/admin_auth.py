from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, Field
from pwdlib import PasswordHash

from app.auth import (
    COOKIE_NAME,
    create_admin_session,
    verify_admin_session,
)
from app.config import get_settings


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-auth"],
)

password_hash = PasswordHash.recommended()


class AdminLoginRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=150,
    )
    password: str = Field(
        min_length=1,
        max_length=500,
    )


@router.post("/login")
def admin_login(
    payload: AdminLoginRequest,
    response: Response,
):
    settings = get_settings()

    if not settings.admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication is not configured.",
        )

    username_valid = (
        payload.username == settings.admin_username
    )

    try:
        password_valid = password_hash.verify(
            payload.password,
            settings.admin_password_hash,
        )
    except Exception:
        password_valid = False

    if not username_valid or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    session_token = create_admin_session(
        settings.admin_username
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=settings.admin_cookie_secure,
        samesite="lax",
        max_age=settings.admin_session_hours * 3600,
        path="/",
    )

    return {
        "authenticated": True,
        "username": settings.admin_username,
    }


@router.post("/logout")
def admin_logout(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )

    return {
        "authenticated": False,
    }


@router.get("/session")
def admin_session(request: Request):
    token = request.cookies.get(COOKIE_NAME)

    if not verify_admin_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid admin session.",
        )

    settings = get_settings()

    return {
        "authenticated": True,
        "username": settings.admin_username,
    }