"""Bounded, single-process job store. No network work in HTTP handlers."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import logging
from threading import RLock, Timer
import time
from uuid import uuid4

from analysis_models import AnalysisResult
from financial_data import normalize_ticker


def run_analysis(ticker, on_update):
    # Import only on a job, so health/docs don't load CrewAI or probe credentials.
    from agents import run_analysis_result
    return run_analysis_result(ticker, on_update=on_update)


class CapacityExceeded(Exception):
    pass


class StoreClosed(Exception):
    pass


class AnalysisStore:
    def __init__(self, runner=run_analysis, *, max_concurrent=2, max_records=100,
                 retention_seconds=3600, timeout_seconds=600, clock=time.monotonic):
        if min(max_concurrent, max_records, retention_seconds, timeout_seconds) < 1:
            raise ValueError("Limits must be positive")
        self.runner = runner
        self.max_concurrent = max_concurrent
        self.max_records = max_records
        self.retention_seconds = retention_seconds
        self.timeout_seconds = timeout_seconds
        self.clock = clock
        self._lock = RLock()
        self._records = {}
        self._deadlines = {}
        self._active = 0
        self._closed = False
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent, thread_name_prefix="analysis")

    def _purge(self):
        for job_id, deadline in list(self._deadlines.items()):
            if self.clock() >= deadline:
                self._records.pop(job_id, None)
                del self._deadlines[job_id]

    def create(self, ticker):
        ticker = normalize_ticker(ticker)
        with self._lock:
            if self._closed:
                raise StoreClosed
            self._purge()
            if self._active >= self.max_concurrent or len(self._records) >= self.max_records:
                raise CapacityExceeded
            job_id = str(uuid4())
            now = datetime.now(timezone.utc)
            initial = {"id": job_id, "created_at": now, "updated_at": now,
                       "expires_at": None, **AnalysisResult(ticker).to_dict()}
            self._records[job_id] = initial
            self._active += 1
            try:
                self._executor.submit(self._run, job_id, ticker)
            except Exception:
                del self._records[job_id]
                self._active -= 1
                raise StoreClosed from None
            return deepcopy(initial)

    def _update(self, job_id, result):
        with self._lock:
            if self._records[job_id]["status"] != "running":
                return
            self._records[job_id].update(result.to_dict())
            self._records[job_id]["updated_at"] = datetime.now(timezone.utc)

    def _timeout(self, job_id):
        with self._lock:
            record = self._records[job_id]
            if record["status"] != "running":
                return
            record.update(status="failed", stage="done", updated_at=datetime.now(timezone.utc))
            if record["interpretation_status"] in ("pending", "running"):
                record["interpretation_status"] = "failed"
            record["errors"].append({"code": "analysis_timeout", "message":
                "A análise excedeu o tempo limite. Os dados já recebidos foram preservados."})
            # Do not release the slot: a Python thread may still be doing work.
            # Retention only starts once the worker actually exits.

    def _run(self, job_id, ticker):
        timer = Timer(self.timeout_seconds, self._timeout, args=(job_id,))
        timer.daemon = True
        timer.start()
        try:
            result = self.runner(ticker, on_update=lambda update: self._update(job_id, update))
            if result.status not in ("completed", "failed"):
                raise ValueError("Runner returned a non-terminal result")
            self._update(job_id, result)
        except Exception as exc:
            logging.getLogger(__name__).warning("Analysis failed (%s)", type(exc).__name__)
            with self._lock:
                record = self._records[job_id]
                if record["status"] == "running":
                    record.update(status="failed", stage="done", updated_at=datetime.now(timezone.utc))
                    if record["interpretation_status"] in ("pending", "running"):
                        record["interpretation_status"] = "failed"
                    record["errors"].append({"code": "analysis_failed", "message": "A análise foi interrompida. Tente novamente."})
        finally:
            timer.cancel()
            with self._lock:
                self._records[job_id]["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=self.retention_seconds)
                self._deadlines[job_id] = self.clock() + self.retention_seconds
                self._active -= 1

    def get(self, job_id):
        with self._lock:
            self._purge()
            record = self._records.get(job_id)
            return deepcopy(record) if record is not None else None

    def close(self):
        with self._lock:
            self._closed = True
        # Running Python threads cannot be forcibly cancelled safely.
        self._executor.shutdown(wait=True)
