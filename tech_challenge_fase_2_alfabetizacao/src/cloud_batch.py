"""Executa no Cloud Shell e publica uma versão no BigQuery sem faturamento."""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import time
from pathlib import Path

import duckdb
import google.auth
from google.auth.transport.requests import AuthorizedSession

from batch import run
from ingest import ROOT, digest, new_run_id, now, write_json

BQ = "https://bigquery.googleapis.com/bigquery/v2/projects"
MAX_NEW_BYTES = 1024 ** 3


def response_json(response):
    if not response.ok:
        raise RuntimeError(f"Google API {response.status_code}: {response.text[:1800]}")
    return response.json()


def require_no_billing(client, project):
    info = response_json(client.get(
        f"https://cloudbilling.googleapis.com/v1/projects/{project}/billingInfo", timeout=30))
    if info.get("billingEnabled") is not False:
        raise ValueError("Execução interrompida: este caminho exige projeto sem faturamento.")
    return {"projectId": info["projectId"], "billingEnabled": False}


def load_parquet(client, project, dataset, table, path, job_id, stage="batch"):
    body = {"jobReference": {"projectId": project, "jobId": job_id, "location": "US"},
            "configuration": {"labels": {"projeto": "postech_fase2", "etapa": stage},
                "load": {"destinationTable": {"projectId": project, "datasetId": dataset, "tableId": table},
                         "sourceFormat": "PARQUET", "writeDisposition": "WRITE_EMPTY",
                         "createDisposition": "CREATE_IF_NEEDED"}}}
    upload = client.post(f"https://bigquery.googleapis.com/upload/bigquery/v2/projects/{project}/jobs",
                         params={"uploadType": "resumable"}, json=body,
                         headers={"X-Upload-Content-Type": "application/octet-stream",
                                  "X-Upload-Content-Length": str(path.stat().st_size)}, timeout=60)
    if not upload.ok:
        response_json(upload)
    with path.open("rb") as stream:
        response_json(client.put(upload.headers["Location"], data=stream,
                                 headers={"Content-Type": "application/octet-stream"}, timeout=(30, 300)))
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        job = response_json(client.get(f"{BQ}/{project}/jobs/{job_id}", params={"location": "US"}, timeout=30))
        if job["status"]["state"] == "DONE":
            if "errorResult" in job["status"]:
                raise RuntimeError(json.dumps(job["status"], ensure_ascii=False))
            return job
        time.sleep(2)
    raise TimeoutError(f"Job sem conclusão após 600 segundos: {job_id}")


def execute(project: str, bronze: Path | None = None, inject_failure: bool = False):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project):
        raise ValueError("ID de projeto inválido")
    if os.environ.get("CLOUD_SHELL") != "true":
        raise ValueError("Execute este comando dentro do Google Cloud Shell.")
    cloud_id = new_run_id().lower()
    evidence_path = ROOT / "data" / "cloud_audit" / f"{cloud_id}.json"
    evidence = {"run_id": cloud_id, "execution": "GOOGLE_CLOUD_SHELL", "hostname": socket.gethostname(),
                "project": project, "started_at": now(), "status": "RUNNING", "jobs": []}
    write_json(evidence_path, evidence)
    started = time.monotonic()
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"], quota_project_id=project)
    try:
        with AuthorizedSession(credentials) as client:
            evidence["billing"] = require_no_billing(client, project)
            print("[cloud] faturamento desativado; execução no Cloud Shell confirmada", flush=True)
            batch = run(bronze, inject_failure)
            evidence["batch_run_id"] = batch["run_id"]
            evidence["batch_audit"] = str(ROOT / "data" / "audit" / f"{batch['run_id']}.json")
            paths = [(f"{layer}_{p.stem}", p) for layer in ("silver", "gold")
                     for p in sorted(Path(batch[layer]).glob("*.parquet"))]
            with duckdb.connect() as con:
                uncompressed = sum(con.execute("SELECT sum(total_uncompressed_size) FROM parquet_metadata(?)", [str(p)]).fetchone()[0] for _, p in paths)
            if uncompressed > MAX_NEW_BYTES:
                raise ValueError("Publicação excede o limite preventivo de 1 GiB por execução.")
            evidence["parquet_bytes"] = sum(p.stat().st_size for _, p in paths)
            evidence["parquet_uncompressed_bytes"] = uncompressed
            require_no_billing(client, project)
            dataset = f"fase2_batch_{cloud_id}"
            evidence["dataset"] = dataset
            # Versão nova: não apaga tabelas anteriores. Só recebe PUBLISHED ao final.
            response_json(client.post(f"{BQ}/{project}/datasets", json={
                "datasetReference": {"projectId": project, "datasetId": dataset}, "location": "US",
                "defaultTableExpirationMs": str(60 * 24 * 60 * 60 * 1000),
                "labels": {"projeto": "postech_fase2", "status": "candidate"},
                "description": "Batch no Cloud Shell. Candidata até concluir todos os jobs e conferir contagens."}, timeout=30))
            for table, path in paths:
                job_id = f"{dataset}_{table}"
                entry = {"table": table, "job_id": job_id, "file_sha256": digest(path), "status": "RUNNING"}
                evidence["jobs"].append(entry)
                write_json(evidence_path, evidence)
                job = load_parquet(client, project, dataset, table, path, job_id)
                meta = response_json(client.get(f"{BQ}/{project}/datasets/{dataset}/tables/{table}", timeout=30))
                expected = batch["counts"][path.stem]
                if int(meta["numRows"]) != expected or int(job["statistics"]["load"]["outputRows"]) != expected:
                    raise ValueError(f"Contagem divergiu na nuvem: {table}")
                entry.update(status="DONE", rows=expected, logical_bytes=int(meta["numBytes"]),
                             expiration_time=meta.get("expirationTime"), statistics=job["statistics"])
                write_json(evidence_path, evidence)
                print(f"[bigquery] {table}: {expected:,} linhas; job={job_id}", flush=True)
            response_json(client.patch(f"{BQ}/{project}/datasets/{dataset}", json={
                "labels": {"projeto": "postech_fase2", "status": "published"},
                "description": f"PUBLISHED: batch {batch['run_id']} executado no Cloud Shell, contagens conciliadas. Evidências: data/cloud_audit/{cloud_id}.json"}, timeout=30))
            evidence.update(status=batch["status"], finished_at=now(),
                            duration_seconds=round(time.monotonic() - started, 3),
                            logical_bytes=sum(j["logical_bytes"] for j in evidence["jobs"]),
                            console_url=f"https://console.cloud.google.com/bigquery?project={project}&p={project}&d={dataset}&page=dataset")
            evidence["billing_after"] = require_no_billing(client, project)
            write_json(evidence_path, evidence)
            write_json(ROOT / "data" / "cloud_latest.json", {"run_id": cloud_id, "project": project,
                       "dataset": dataset, "batch_run_id": batch["run_id"], "evidence": str(evidence_path)})
            print(json.dumps({"status": evidence["status"], "console_url": evidence["console_url"]}, ensure_ascii=False), flush=True)
    except Exception as exc:
        evidence.update(status="FAILED", finished_at=now(), error=f"{type(exc).__name__}: {exc}",
                        duration_seconds=round(time.monotonic() - started, 3))
        write_json(evidence_path, evidence)
        raise
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--bronze", type=Path)
    parser.add_argument("--inject-failure", action="store_true")
    args = parser.parse_args()
    from alerts import run_monitored
    run_monitored("batch_cloud", lambda: execute(args.project, args.bronze, args.inject_failure))
