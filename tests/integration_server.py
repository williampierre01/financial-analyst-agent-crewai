"""Offline browser harness; never used by the deployed application."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis_models import AnalysisResult
from backend.web import create_web_app
from auth_fakes import service


def runner(ticker, on_update):
    snapshot = json.loads((ROOT / "frontend/tests/fixture.json").read_text(encoding="utf-8"))["data"]
    snapshot.update(ticker=ticker, display_ticker=ticker.removesuffix(".SA"))
    on_update(AnalysisResult(ticker, data=snapshot, interpretation_status="running"))
    time.sleep(8 if ticker == "ITUB4.SA" else 3)
    if ticker == "VALE3.SA":
        raise RuntimeError("private-provider-error")
    return AnalysisResult(ticker, status="completed", stage="done", data=snapshot,
                          interpretation_status="completed", interpretation="Interpretação do teste integrado.")


app = create_web_app(runner=runner, auth_service=service("http://127.0.0.1:8012"),
                     max_concurrent=1, timeout_seconds=6)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8012)
