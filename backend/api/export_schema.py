"""Export/check the API contract consumed by the TypeScript client."""
import argparse
import json
from pathlib import Path

from backend.api.main import app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"
    content = json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            raise SystemExit("Contrato desatualizado: execute python -m backend.api.export_schema")
    else:
        target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
