"""Serve React and the authenticated API on the same HTTPS origin."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.main import create_app


def create_web_app(*, frontend_dir=None, runner=None, auth_service=None, **store_options):
    directory = Path(frontend_dir) if frontend_dir is not None else (
        Path(__file__).resolve().parents[1] / "frontend" / "dist"
    )
    api = create_app(**({"runner": runner} if runner is not None else {}),
                     auth_service=auth_service, **store_options)

    @asynccontextmanager
    async def lifespan(app):
        if not (directory / "index.html").is_file():
            raise RuntimeError("Frontend build missing. Run npm ci and npm run build in frontend.")
        async with api.router.lifespan_context(api):
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers.update({"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "max-age=31536000",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()"})
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    app.mount("/api", api)
    app.mount("/", StaticFiles(directory=directory, html=True, check_dir=False))
    return app


app = create_web_app()
