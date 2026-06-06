"""Clerk JWT Authentication — Verifies frontend auth tokens on the backend.

Extracts Bearer token from Authorization header, verifies against Clerk's
JWKS endpoint using RS256, returns user_id (sub claim).

Usage:
    @app.post("/api/launch")
    async def launch(user_id: str = Depends(get_current_user)):
        ...
"""

import os
import time
import httpx
import jwt as pyjwt
from fastapi import Depends, HTTPException, Request
from functools import lru_cache

# Clerk JWKS URL — derived from publishable key domain
CLERK_JWKS_URL = os.getenv(
    "CLERK_JWKS_URL",
    "https://pleasant-mammoth-50.clerk.accounts.dev/.well-known/jwks.json",
)

# Cache for JWKS keys (refreshed every 6 hours)
_jwks_cache: dict = {"keys": [], "fetched_at": 0}
_JWKS_CACHE_TTL = 6 * 3600  # 6 hours


async def _get_jwks() -> list:
    """Fetch and cache Clerk's JWKS keys."""
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < _JWKS_CACHE_TTL:
        return _jwks_cache["keys"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(CLERK_JWKS_URL)
            resp.raise_for_status()
            data = resp.json()
            _jwks_cache["keys"] = data.get("keys", [])
            _jwks_cache["fetched_at"] = now
            return _jwks_cache["keys"]
    except Exception as e:
        print(f"[Auth] JWKS fetch failed: {e}")
        # Return cached keys even if stale
        if _jwks_cache["keys"]:
            return _jwks_cache["keys"]
        raise HTTPException(status_code=503, detail="Authentication service unavailable")


def _extract_token(request: Request) -> str | None:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def get_current_user(request: Request) -> str:
    """FastAPI dependency — verifies JWT and returns user_id.

    Raises 401 if token is missing or invalid.
    """
    from services.logger import security_logger

    token = _extract_token(request)
    if not token:
        security_logger.auth_failure(
            ip=request.client.host if request.client else "unknown",
            reason="Missing Authorization header",
            endpoint=str(request.url.path),
        )
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get JWKS keys
        jwks_keys = await _get_jwks()
        if not jwks_keys:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

        # Decode JWT header to find the right key
        unverified_header = pyjwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching key
        matching_key = None
        for key in jwks_keys:
            if key.get("kid") == kid:
                matching_key = key
                break

        if not matching_key:
            raise HTTPException(status_code=401, detail="Invalid token key")

        # Build public key from JWKS
        public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(matching_key)

        # Verify and decode the token
        payload = pyjwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                "verify_aud": False,  # Clerk tokens don't always have aud
                "verify_iss": True,
            },
            issuer=CLERK_JWKS_URL.replace("/.well-known/jwks.json", ""),
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")

        security_logger.auth_success(
            user_id=user_id,
            ip=request.client.host if request.client else "unknown",
            endpoint=str(request.url.path),
        )

        return user_id

    except pyjwt.ExpiredSignatureError:
        security_logger.auth_failure(
            ip=request.client.host if request.client else "unknown",
            reason="Token expired",
            endpoint=str(request.url.path),
        )
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError as e:
        security_logger.auth_failure(
            ip=request.client.host if request.client else "unknown",
            reason=f"Invalid token: {str(e)}",
            endpoint=str(request.url.path),
        )
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Auth] Unexpected error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_optional_user(request: Request) -> str | None:
    """FastAPI dependency — returns user_id if authenticated, None if not.

    Use for public endpoints that optionally benefit from auth
    (e.g., /api/session/{id} for the pay page).
    """
    token = _extract_token(request)
    if not token:
        return None

    try:
        return await get_current_user(request)
    except HTTPException:
        return None
