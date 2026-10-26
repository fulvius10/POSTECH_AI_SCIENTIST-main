"""Download read-only de tabelas públicas, sem jobs SQL ou recursos de nuvem."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import google.auth
from google.auth.transport.requests import AuthorizedSession
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
TABLES = (
    "dicionario", "meta_alfabetizacao_brasil", "meta_alfabetizacao_uf",
    "meta_alfabetizacao_municipio", "uf", "municipio", "alunos",
)
SOURCE = "https://bigquery.googleapis.com/bigquery/v2/projects/basedosdados/datasets/br_inep_avaliacao_alfabetizacao/tables"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def session() -> AuthorizedSession:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/bigquery.readonly"])
    client = AuthorizedSession(credentials)
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    client.mount("https://", HTTPAdapter(max_retries=retry))
    return client


def get(client: AuthorizedSession, url: str, **params: object) -> dict:
    # Não há método de escrita, jobs.insert, Storage Read API ou ativação de serviço.
    response = client.get(url, params=params, timeout=(15, 120))
    response.raise_for_status()
    return response.json()


def download(tables: tuple[str, ...] = TABLES) -> Path:
    if len(set(tables)) != len(tables) or not set(tables).issubset(TABLES):
        raise ValueError("Seleção de tabelas inválida ou repetida")
    run_id = new_run_id()
    target = ROOT / "data" / "bronze" / run_id
    target.mkdir(parents=True, exist_ok=False)
    manifest = {"run_id": run_id, "started_at": now(), "status": "RUNNING", "source": SOURCE,
                "method": "GET tables.get + tabledata.list; no query jobs", "tables": {}}
    write_json(target / "manifest.json", manifest)
    try:
        with session() as client:
            for table in tables:
                start = time.monotonic()
                url = f"{SOURCE}/{table}"
                metadata = get(client, url)
                fields = metadata["schema"]["fields"]
                if any(f.get("mode") == "REPEATED" or f["type"] == "RECORD" for f in fields):
                    raise ValueError(f"Schema não plano: {table}")
                expected = int(metadata["numRows"])
                write_json(target / f"{table}.metadata.json", metadata)
                path = target / f"{table}.csv.gz"
                partial = path.with_suffix(path.suffix + ".partial")
                count, pages, token = 0, 0, None
                tokens_seen = set()
                print(f"[bronze] {table}: iniciando {expected:,} registros", flush=True)
                with gzip.open(partial, "wt", encoding="utf-8", newline="", compresslevel=3) as f:
                    writer = csv.writer(f)
                    writer.writerow([field["name"] for field in fields])
                    while True:
                        params = {"maxResults": 50000}
                        if token:
                            params["pageToken"] = token
                        page = get(client, f"{url}/data", **params)
                        rows = page.get("rows", [])
                        for row in rows:
                            values = [cell.get("v") for cell in row["f"]]
                            if len(values) != len(fields):
                                raise ValueError(f"Largura inválida em {table}")
                            if any(value == r"\N" for value in values):
                                raise ValueError("Colisão com marcador de nulo CSV")
                            writer.writerow([r"\N" if value is None else value for value in values])
                        count += len(rows)
                        if count > expected:
                            raise ValueError(f"Paginação excedeu a contagem de {table}")
                        pages += 1
                        if pages % 10 == 0:
                            print(f"[bronze] {table}: {count:,}/{expected:,}", flush=True)
                        token = page.get("pageToken")
                        if not token:
                            break
                        if token in tokens_seen:
                            raise ValueError(f"Token de paginação repetido em {table}")
                        tokens_seen.add(token)
                after = get(client, url)
                if count != expected or metadata["lastModifiedTime"] != after["lastModifiedTime"]:
                    raise ValueError(f"Fonte mudou ou extração incompleta em {table}: {count}/{expected}")
                partial.replace(path)
                manifest["tables"][table] = {"file": path.name, "rows": count, "bytes_gzip": path.stat().st_size,
                    "sha256": digest(path), "duration_seconds": round(time.monotonic() - start, 3),
                    "source_last_modified": metadata["lastModifiedTime"]}
                write_json(target / "manifest.json", manifest)
                print(f"[bronze] {table}: concluído {count:,}", flush=True)
        manifest.update(status="SUCCESS", finished_at=now())
    except Exception as exc:
        manifest.update(status="FAILED", finished_at=now(), error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json(target / "manifest.json", manifest)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", nargs="+", choices=TABLES)
    args = parser.parse_args()
    from alerts import run_monitored
    print(run_monitored("ingest", lambda: download(tuple(args.tables) if args.tables else TABLES)), flush=True)
