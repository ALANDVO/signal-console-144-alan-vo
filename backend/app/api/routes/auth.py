from fastapi import APIRouter, Depends, Request, Response, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import secrets
import urllib.parse

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.auth import (
    create_access_token,
    decode_token,
    set_session_cookie,
    clear_session_cookie,
    get_current_user_id,
    log_audit,
)
from app.api.schemas import HealthResponse


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.get("/login")
async def login(
    request: Request,
    redirect_uri: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if not settings.oidc_issuer_url or not settings.oidc_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC not configured",
        )
    
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    
    request.session = getattr(request, "session", {})
    request.session["oidc_state"] = state
    request.session["oidc_nonce"] = nonce
    if redirect_uri:
        request.session["post_login_redirect"] = redirect_uri
    
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": settings.oidc_scopes,
        "redirect_uri": settings.oidc_redirect_uri,
        "state": state,
        "nonce": nonce,
    }
    
    auth_url = f"{settings.oidc_issuer_url}/protocol/openid-connect/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC error: {error} - {error_description}",
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter",
        )
    
    session_state = getattr(request, "session", {}).get("oidc_state")
    if not session_state or session_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )
    
    nonce = getattr(request, "session", {}).get("oidc_nonce")
    
    import httpx
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            f"{settings.oidc_issuer_url}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.oidc_redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
        token_response.raise_for_status()
        tokens = token_response.json()
    
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")
    
    if not access_token or not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tokens in response",
        )
    
    try:
        claims = decode_token(id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID token: {str(e)}",
        )
    
    if claims.get("nonce") != nonce:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nonce mismatch",
        )
    
    user_id = claims.get("sub") or claims.get("preferred_username")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing user identifier in token",
        )
    
    roles = claims.get("realm_access", {}).get("roles", [])
    if "viewer" not in roles:
        roles.append("viewer")
    
    session_token = create_access_token(
        {"sub": user_id, "roles": roles},
        expires_delta=None,
    )
    
    redirect_url = getattr(request, "session", {}).get("post_login_redirect", "/")
    response = RedirectResponse(url=redirect_url)
    set_session_cookie(response, session_token)
    
    await log_audit(db, user_id, "login", "session", None, {"roles": roles}, request)
    
    return response


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = await get_current_user_id(request)
    if user_id:
        await log_audit(db, user_id, "logout", "session", None, {}, request)
    clear_session_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = await get_current_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    token = request.cookies.get("session")
    claims = decode_token(token)
    
    return {
        "user_id": user_id,
        "roles": claims.get("roles", []),
        "email": claims.get("email"),
        "name": claims.get("name"),
    }


@router.get("/demo-login")
async def demo_login(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode disabled",
        )
    
    user_id = "demo-user"
    roles = ["viewer", "analyst", "operator"]
    
    session_token = create_access_token(
        {"sub": user_id, "roles": roles},
        expires_delta=None,
    )
    
    set_session_cookie(response, session_token)
    await log_audit(db, user_id, "demo_login", "session", None, {"roles": roles}, request)
    
    return {
        "user_id": user_id,
        "roles": roles,
        "message": "Demo login successful",
    }