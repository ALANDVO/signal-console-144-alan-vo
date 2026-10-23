import pytest
from app.core.auth import create_access_token, decode_token, require_role
from app.core.exceptions import UnauthorizedError, ForbiddenError
from fastapi import Request
from unittest.mock import MagicMock


class TestAuth:
    def test_create_and_decode_token(self):
        token = create_access_token({"sub": "test-user", "roles": ["viewer", "operator"]})
        assert isinstance(token, str)
        assert len(token) > 0
        
        payload = decode_token(token)
        assert payload["sub"] == "test-user"
        assert payload["roles"] == ["viewer", "operator"]

    def test_decode_invalid_token(self):
        with pytest.raises(UnauthorizedError):
            decode_token("invalid-token")

    def test_decode_expired_token(self):
        import time
        from jose import jwt
        from app.core.config import get_settings
        settings = get_settings()
        
        # Create expired token
        payload = {"sub": "test-user", "exp": int(time.time()) - 3600}
        expired_token = jwt.encode(payload, settings.session_secret_key, algorithm="HS256")
        
        with pytest.raises(UnauthorizedError):
            decode_token(expired_token)

    def test_require_role_factory(self):
        # Test that require_role returns a callable
        dependency = require_role(["admin"])
        assert callable(dependency)

    @pytest.mark.asyncio
    async def test_require_user_with_valid_token(self):
        from app.core.auth import require_user
        from unittest.mock import AsyncMock
        
        # Create a mock request with valid cookie
        request = MagicMock(spec=Request)
        token = create_access_token({"sub": "test-user", "roles": ["viewer"]})
        request.cookies = {"session": token}
        
        user_id = await require_user(request)
        assert user_id == "test-user"

    @pytest.mark.asyncio
    async def test_require_user_without_token(self):
        from app.core.auth import require_user
        from unittest.mock import MagicMock
        
        request = MagicMock(spec=Request)
        request.cookies = {}
        
        with pytest.raises(UnauthorizedError):
            await require_user(request)

    @pytest.mark.asyncio
    async def test_require_role_with_sufficient_role(self):
        dependency = require_role(["viewer", "operator"])
        request = MagicMock(spec=Request)
        token = create_access_token({"sub": "test-user", "roles": ["viewer"]})
        request.cookies = {"session": token}
        
        user_id = await dependency(request)
        assert user_id == "test-user"

    @pytest.mark.asyncio
    async def test_require_role_with_insufficient_role(self):
        dependency = require_role(["admin"])
        request = MagicMock(spec=Request)
        token = create_access_token({"sub": "test-user", "roles": ["viewer"]})
        request.cookies = {"session": token}
        
        with pytest.raises(ForbiddenError):
            await dependency(request)