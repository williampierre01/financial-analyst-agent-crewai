"""Local API: uvicorn backend.api.main:app --host 127.0.0.1 --port 8000."""
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response

from backend.api.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from backend.services.analyses import AnalysisStore, CapacityExceeded, StoreClosed, run_analysis


def create_app(runner=run_analysis, **store_options):
    @asynccontextmanager
    async def lifespan(app):
        app.state.analyses = AnalysisStore(runner, **store_options)
        try:
            yield
        finally:
            app.state.analyses.close()

    app = FastAPI(title="Análise de ações brasileiras", version="0.1.0", lifespan=lifespan)

    @app.get("/health", response_model=HealthResponse)
    def health():
        store = app.state.analyses
        return HealthResponse(max_concurrent=store.max_concurrent, max_records=store.max_records,
                              retention_seconds=store.retention_seconds)

    @app.post("/analyses", response_model=AnalysisResponse, status_code=202)
    def start_analysis(body: AnalysisRequest, response: Response, request: Request):
        try:
            record = app.state.analyses.create(body.ticker)
        except CapacityExceeded:
            raise HTTPException(429, detail={"code": "capacity_exceeded", "message": "Limite de análises atingido. Tente novamente mais tarde."}) from None
        except StoreClosed:
            raise HTTPException(503, detail={"code": "service_unavailable", "message": "Serviço temporariamente indisponível."}) from None
        response.headers["Location"] = f"{request.scope.get('root_path', '')}/analyses/{record['id']}"
        response.headers["Cache-Control"] = "no-store"
        return record

    @app.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
    def get_analysis(analysis_id: UUID, response: Response):
        record = app.state.analyses.get(str(analysis_id))
        if record is None:
            raise HTTPException(404, detail={"code": "analysis_not_found", "message": "Análise não encontrada ou expirada."})
        response.headers["Cache-Control"] = "no-store"
        return record

    return app


app = create_app()
