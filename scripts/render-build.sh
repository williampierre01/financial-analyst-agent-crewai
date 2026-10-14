#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install -r requirements-tooling.txt
uv sync --locked --no-dev
test "$(node --version)" = "v22.17.1"
test "$(npm --version)" = "10.9.2"
npm ci --prefix frontend --include=dev
npm run build --prefix frontend
