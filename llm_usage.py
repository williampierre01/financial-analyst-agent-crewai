"""Per-analysis counters. Never store prompts, responses, keys or user identities."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import json
import logging
from time import monotonic
from uuid import uuid4

logger = logging.getLogger("llm_usage")
# Uvicorn does not configure the application's root logger. Make these compact
# operational records visible without enabling verbose SDK/agent logging.
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.propagate = False
job_id = ContextVar("llm_job_id", default=None)
analysis_deadline = ContextVar("llm_analysis_deadline", default=None)
current_usage = ContextVar("llm_usage", default=None)


@dataclass
class UsageMeter:
    deadline: float | None = field(default_factory=analysis_deadline.get)
    analysis_id: str = field(default_factory=lambda: job_id.get() or str(uuid4()))
    stage: str = "gathering"
    logical_calls: int = 0
    attempts: list = field(default_factory=list)
    started: float = field(default_factory=monotonic)

    def record(self, attempt):
        self.attempts.append(attempt)
        logger.info("llm_attempt %s", json.dumps(
            {"analysis_id": self.analysis_id, **attempt}, ensure_ascii=False))

    def summary(self):
        groups = {}
        for attempt in self.attempts:
            key = (attempt["provider"], attempt["model"])
            group = groups.setdefault(key, dict(provider=key[0], model=key[1],
                attempts=0, successes=0, failures=0, usage_reported=0,
                input_tokens_reported=0, output_tokens_reported=0))
            group["attempts"] += 1
            group["successes" if attempt["outcome"] == "success" else "failures"] += 1
            if attempt["input_tokens"] is not None and attempt["output_tokens"] is not None:
                group["usage_reported"] += 1
            for source, target in [("input_tokens", "input_tokens_reported"),
                                   ("output_tokens", "output_tokens_reported")]:
                if attempt[source] is not None:
                    group[target] += attempt[source]
        return dict(analysis_id=self.analysis_id, logical_calls=self.logical_calls,
                    attempts=len(self.attempts), providers=list(groups.values()),
                    duration_ms=round((monotonic() - self.started) * 1000))


@contextmanager
def analysis_usage(ticker):
    meter = UsageMeter()
    token = current_usage.set(meter)
    try:
        yield meter
    finally:
        logger.info("llm_analysis %s", json.dumps(
            {"ticker": ticker, **meter.summary()}, ensure_ascii=False))
        current_usage.reset(token)
