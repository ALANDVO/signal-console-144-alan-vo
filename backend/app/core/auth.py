from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import Request, Response, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.models import AuditLog


settings = get_settings()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.session_secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.session_secret_key, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}")


async def get_current_user_id(request: Request) -> Optional[str]:
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except UnauthorizedError:
        return None


async def require_user(request: Request) -> str:
    user_id = await get_current_user_id(request)
    if not user_id:
        raise UnauthorizedError("Authentication required")
    return user_id


def require_role(allowed_roles: list[str]):
    async def _require_role(request: Request) -> str:
        user_id = await get_current_user_id(request)
        if not user_id:
            raise UnauthorizedError("Authentication required")
        
        token = request.cookies.get("session")
        if not token:
            raise UnauthorizedError("Authentication required")
        
        payload = decode_token(token)
        user_roles = payload.get("roles", [])
        
        if not any(role in user_roles for role in allowed_roles):
            raise ForbiddenError(f"Required role: one of {allowed_roles}")
        
        return user_id
    return _require_role


def set_session_cookie(response: Response, token: str, max_age: int = 1800) -> None:
    response.set_cookie(
        key="session",
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key="session",
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )


async def log_audit(
    session: AsyncSession,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    import json
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    session.add(log)
    await session.flush()