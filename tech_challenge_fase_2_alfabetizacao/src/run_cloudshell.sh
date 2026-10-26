#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
project="${1:?Informe o ID do projeto Google Cloud}"
export GOOGLE_CLOUD_PROJECT="$project"
export CLOUDSDK_CORE_PROJECT="$project"
python3 -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.txt
mkdir -p data/console
log="data/console/batch_$(date -u +%Y%m%dT%H%M%SZ).log"
.venv/bin/python -u src/cloud_batch.py --project "$project" 2>&1 | tee "$log"
