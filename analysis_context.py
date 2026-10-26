"""Lossless context reduction; no token estimates or arbitrary truncation."""

import json


def encode(value) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def compact_metrics(metrics: list[dict]) -> dict:
    """Store repeated operands once, retaining null operands and every metric field."""
    operands = []
    indexes = {}
    compact = []
    for metric in metrics:
        refs = []
        for operand in metric["inputs"]:
            if operand is None:
                refs.append(None)
                continue
            key = encode(operand)
            if key not in indexes:
                indexes[key] = len(operands)
                operands.append(operand)
            refs.append(indexes[key])
        compact.append({**{k: v for k, v in metric.items() if k != "inputs"},
                        "input_refs": refs})
    return {"operands": operands, "metrics": compact}
