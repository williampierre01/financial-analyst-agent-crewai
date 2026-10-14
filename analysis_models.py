"""Transport-neutral analysis state; no UI or provider dependencies."""
from dataclasses import asdict, dataclass, field
from typing import Literal


@dataclass
class AnalysisResult:
    ticker: str
    status: Literal["running", "completed", "failed"] = "running"
    stage: Literal["gathering", "quant", "cio", "done"] = "gathering"
    data: dict | None = None
    interpretation_status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    interpretation: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Independent snapshot suitable for a future JSON API."""
        return asdict(self)
