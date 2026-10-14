"""Serve the compiled React app and the API from one origin.

Local: uvicorn backend.web:app --host 127.0.0.1 --port 8000
Build frontend/dist first. Use exactly one worker while jobs live in memory.
"""
from contextlib import asynccontextmanager
from pathlib import Path
import os
import secrets

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles

from backend.api.main import create_app


def create_web_app(*, frontend_dir=None, runner=None, username=None, password=None, **store_options):
    directory = Path(frontend_dir) if frontend_dir is not None else (
        Path(__file__).resolve().parents[1] / "frontend" / "dist"
    )
    api = create_app(**({"runner": runner} if runner is not None else {}), **store_options)
    auth = HTTPBasic(auto_error=False)
    username = username if username is not None else os.environ.get("WEB_USERNAME", "")
    password = password if password is not None else os.environ.get("WEB_PASSWORD", "")

    @asynccontextmanager
    async def lifespan(app):
        if not username or ":" in username or len(password) < 16 or not username.isascii() or not password.isascii():
            raise RuntimeError("Set ASCII WEB_USERNAME (without colon) and WEB_PASSWORD (at least 16 characters).")
        if not (directory / "index.html").is_file():
            raise RuntimeError("Frontend build missing. Run npm ci and npm run build in frontend.")
        # Mounted applications do not automatically receive lifespan events.
        async with api.router.lifespan_context(api):
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def response_headers(request, call_next):
        # Only the minimal platform health probe is public, never the API.
        if request.url.path != "/healthz" or request.method not in ("GET", "HEAD"):
            try:
                credentials = await auth(request)
            except HTTPException:
                credentials = None
            valid_user = secrets.compare_digest(
                (credentials.username if credentials else "").encode(), username.encode()
            )
            valid_password = secrets.compare_digest(
                (credentials.password if credentials else "").encode(), password.encode()
            )
            if not (credentials and valid_user and valid_password):
                return JSONResponse({"detail": "Acesso restrito."}, status_code=401,
                                    headers={"WWW-Authenticate": 'Basic realm="Analista"',
                                             "Cache-Control": "no-store"})
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            # Basic credentials are ambient browser credentials. Do not accept
            # writes from another site, even if a valid password was cached.
            origin = request.headers.get("origin")
            expected = str(request.base_url).rstrip("/")
            if (origin is not None and origin != expected) or request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "Origem não permitida."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        # Avoid stale HTML/API results across updates and rollbacks.
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    app.mount("/api", api)
    app.mount("/", StaticFiles(directory=directory, html=True, check_dir=False))
    return app


app = create_web_app()
