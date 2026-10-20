"""Same-origin session endpoints. Never trust a user ID supplied by the client."""
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from backend.security.auth import COOKIE, denied

router = APIRouter(prefix="/auth", include_in_schema=False)


class SessionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_token: str = Field(min_length=1, max_length=16384)


def install_security(app):
    @app.middleware("http")
    async def guard(request, call_next):
        service = request.app.state.auth
        path = request.scope.get("path", "").removeprefix(request.scope.get("root_path", ""))
        public = (request.method == "GET" and path == "/auth/config") or (
            request.method == "POST" and path in ("/auth/session", "/auth/logout"))
        try:
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                if (request.headers.get("origin") != service.origin
                    or request.headers.get("x-requested-with") != "analista"
                    or request.headers.get("sec-fetch-site") == "cross-site"):
                    raise denied("invalid_origin", 403)
            if path in ("/auth/session", "/auth/logout"):
                host = request.client.host if request.client else "unknown"
                service.limits.check("auth:" + host, 20, 60)
            if not public:
                request.state.user = await run_in_threadpool(service.authenticate, request.cookies.get(COOKIE))
                if request.method == "POST" and path == "/analyses":
                    service.limits.check("analysis:" + request.state.user["uid"], 10, 3600)
            response = await call_next(request)
        except HTTPException as exc:
            response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
        except Exception:
            response = JSONResponse({"detail": {"code": "auth_unavailable", "message": "Acesso temporariamente indisponível. Tente novamente mais tarde."}}, status_code=503)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.include_router(router)


@router.get("/config")
def config(request: Request):
    return request.app.state.auth.config


@router.post("/session")
def login(body: SessionInput, request: Request, response: Response):
    service = request.app.state.auth
    token, user = service.login(body.id_token)
    service.logout(request.cookies.get(COOKIE))
    response.set_cookie(COOKIE, token, max_age=8 * 3600, secure=True, httponly=True,
                        samesite="strict", path="/")
    return user


@router.get("/me")
def me(request: Request):
    return request.state.user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response):
    request.app.state.auth.logout(request.cookies.get(COOKIE))
    response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="strict")
