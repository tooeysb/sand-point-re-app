"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import router as api_router
from app.api.admin.users import router as admin_users_router
from app.api.auth import router as auth_router
from app.config import get_settings
from app.core.errors import register_error_handlers
from app.db.database import init_db
from app.middleware.correlation import CorrelationIDMiddleware
from app.middleware.sso import SSOMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Real estate financial modeling and underwriting platform",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Register standardized error handlers
register_error_handlers(app)

# Mount static files
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/ui/templates")

# Correlation ID middleware (always enabled — outermost middleware runs first)
app.add_middleware(CorrelationIDMiddleware)

# SSO middleware (always enabled — rejects requests if SSO_JWT_SECRET is missing)
app.add_middleware(SSOMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api")
app.include_router(auth_router)  # /api/auth/* (prefix defined in router)
app.include_router(admin_users_router)  # /api/admin/users/* (prefix defined in router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": settings.app_name},
    )


@app.get("/model/{model_id}", response_class=HTMLResponse)
async def model_view(request: Request, model_id: str, property_id: str | None = None):
    """Render the financial model editor."""
    return templates.TemplateResponse(
        request=request,
        name="model.html",
        context={"model_id": model_id, "property_id": property_id or ""},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "0.1.0"}


# === Auth Page Routes ===


@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse(request=request, name="auth/login.html")


@app.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse(request=request, name="auth/register.html")


@app.get("/auth/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Render the forgot password page."""
    return templates.TemplateResponse(request=request, name="auth/forgot-password.html")


@app.get("/auth/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Render the reset password page."""
    return templates.TemplateResponse(request=request, name="auth/reset-password.html")


# === Admin Page Routes ===


@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    """Render the admin users management page."""
    return templates.TemplateResponse(request=request, name="admin/users.html")
