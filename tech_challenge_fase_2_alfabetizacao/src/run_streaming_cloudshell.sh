#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
project="${1:?Informe o ID do projeto Google Cloud}"
export GOOGLE_CLOUD_PROJECT="$project"
export CLOUDSDK_CORE_PROJECT="$project"
mkdir -p data/console
log="data/console/streaming_$(date -u +%Y%m%dT%H%M%SZ).log"
.venv/bin/python -u src/stream_demo.py --project "$project" 2>&1 | tee "$log"
