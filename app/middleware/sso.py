"""
SSO authentication middleware.

Requires visitors to authenticate at the HTH Corp Portal before accessing the app.
Validates an `access_token` cookie on each request. If missing or invalid,
redirects to the Portal's silent SSO endpoint.
"""

import os
from urllib.parse import quote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.auth.jwt import decode_token

PUBLIC_PREFIXES = (
    "/api/auth/sso",
    "/auth/sso",
    "/health",
    "/static",
    "/favicon.ico",
)


class SSOMiddleware(BaseHTTPMiddleware):
    """Redirect unauthenticated visitors to the HTH Corp Portal for silent SSO."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return await call_next(request)

        # Check for valid access_token cookie
        token = request.cookies.get("access_token")
        if token:
            payload = decode_token(token)
            if payload is not None:
                return await call_next(request)

        # No valid session — redirect to Portal for silent SSO
        current_url = str(request.url)
        portal_sso_url = os.environ.get(
            "PORTAL_SSO_URL", "https://www.hth-corp.com/auth/sso-silent"
        )
        return RedirectResponse(
            url=f"{portal_sso_url}?return_to={quote(current_url)}", status_code=302
        )
