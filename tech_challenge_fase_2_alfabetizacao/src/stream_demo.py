"""Demonstra streaming HTTP com fila durável, microlotes e duas publicações incrementais."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import socket
import time

import google.auth
from google.auth.transport.requests import AuthorizedSession
import requests

from cloud_batch import BQ, load_parquet, require_no_billing, response_json
from ingest import ROOT, digest, new_run_id, now, write_json
from streaming import Consumer, EventStore, Receiver


def event(event_id, municipality, rate):
    return {"event_id": event_id, "schema_version": 1, "event_type": "resultado_municipal_atualizado",
            "origem": "SIMULADO", "produced_at": now(), "ano": 2024,
            "id_municipio": municipality, "serie": "2", "rede": "Municipal", "taxa_alfabetizacao": rate}


def publish(client, project, dataset, checkpoint, tables, audit, audit_path):
    # A fila/consumidor são streaming; a escrita no BigQuery gratuito é carga batch.
    require_no_billing(client, project)
    for name, table in tables.items():
        table_id = f"{name}_{checkpoint}"
        job_id = f"{dataset}_{table_id}"
        entry = {"checkpoint": checkpoint, "table": table_id, "job_id": job_id, "status": "RUNNING"}
        audit["jobs"].append(entry)
        write_json(audit_path, audit)
        job = load_parquet(client, project, dataset, table_id, Path(table["file"]), job_id, stage="streaming")
        metadata = response_json(client.get(f"{BQ}/{project}/datasets/{dataset}/tables/{table_id}", timeout=30))
        if int(metadata["numRows"]) != table["rows"] or int(job["statistics"]["load"]["outputRows"]) != table["rows"]:
            raise ValueError(f"Contagem divergente em {table_id}")
        entry.update(status="DONE", rows=table["rows"], logical_bytes=int(metadata["numBytes"]),
                     sha256=table["sha256"], statistics=job["statistics"])
        write_json(audit_path, audit)
        print(f"[bigquery] {table_id}: {table['rows']} linhas; job={job_id}", flush=True)
    response_json(client.patch(f"{BQ}/{project}/datasets/{dataset}", json={
        "labels": {"projeto": "postech_fase2", "status": "published", "checkpoint": checkpoint},
        "description": f"Streaming SIMULADO via HTTP/SQLite no Cloud Shell. Último checkpoint aprovado: {checkpoint}. Eventos oficiais não são alterados."}, timeout=30))
    write_json(ROOT / "data" / "streaming_latest.json", {"run_id": audit["run_id"], "project": project,
               "dataset": dataset, "checkpoint": checkpoint, "audit": str(audit_path)})


def execute(baseline: Path, project=None, interval=0.5):
    if not 0.05 <= interval <= 60:
        raise ValueError("Intervalo deve ficar entre 0,05 e 60 segundos")
    if project and os.environ.get("CLOUD_SHELL") != "true":
        raise ValueError("A demonstração na GCP deve ser executada dentro do Cloud Shell")
    run_id = new_run_id().lower()
    directory = ROOT / "data" / "streaming" / run_id
    audit_path = directory / "audit.json"
    official_files = [baseline, *(ROOT / "data").glob("latest.json"), *(ROOT / "data").glob("cloud_latest.json")]
    official_hashes = {str(path): digest(path) for path in official_files}
    audit = {"run_id": run_id, "status": "RUNNING", "started_at": now(), "hostname": socket.gethostname(),
             "execution": "GOOGLE_CLOUD_SHELL" if os.environ.get("CLOUD_SHELL") == "true" else "LOCAL",
             "project": project, "origem": "SIMULADO", "transport": "HTTP loopback + SQLite WAL",
             "interval_seconds": interval, "baseline": str(baseline), "official_hashes_before": official_hashes,
             "jobs": [], "checkpoints": [], "proofs": {}}
    write_json(audit_path, audit)
    client = receiver = consumer = None
    started = time.monotonic()
    try:
        if project:
            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"], quota_project_id=project)
            client = AuthorizedSession(credentials)
            audit["billing_before"] = require_no_billing(client, project)
            dataset = f"fase2_stream_{run_id}"
            audit["dataset"] = dataset
            response_json(client.post(f"{BQ}/{project}/datasets", json={
                "datasetReference": {"projectId": project, "datasetId": dataset}, "location": "US",
                "defaultTableExpirationMs": str(60 * 86400000),
                "labels": {"projeto": "postech_fase2", "status": "candidate"},
                "description": "Cenário SIMULADO de streaming; aguardando primeiro checkpoint validado."}, timeout=30))
        store = EventStore(directory, baseline)
        receiver = Receiver(store)
        receiver.start()
        consumer = Consumer(store, interval)
        consumer.start()
        with baseline.open(encoding="utf-8", newline="") as stream:
            candidates = [r["id_municipio"] for r in csv.DictReader(stream) if r["meta_alfabetizacao_2024"]]
        if len(candidates) < 2:
            raise ValueError("A demonstração exige dois municípios com meta")
        a = "3106200" if "3106200" in candidates else candidates[0]
        b = "3170206" if "3170206" in candidates else next(code for code in candidates if code != a)
        audit["demo_municipalities"] = {"a": a, "b": b}

        def send(payload):
            raw = payload.encode() if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode()
            # Espera real entre produção e envio; recepção grava outro horário depois do HTTP.
            time.sleep(0.03)
            result = requests.post(receiver.url, data=raw, headers={"Content-Type": "application/json"}, timeout=10)
            result.raise_for_status()
            if result.status_code != 202:
                raise ValueError("Recebimento não foi confirmado como persistido")

        first = event("e01", a, 60)
        send(first)
        send(event("e02", b, 70))
        send(first)
        send(event("invalid_percent", a, 120))
        send({**event("invalid_origin", a, 60), "origem": "OFICIAL"})
        send("{json incompleto")
        send(event("invalid_territory", "0000000", 50))
        send({**event("invalid_future", a, 60), "produced_at": (datetime.now(timezone.utc)+timedelta(seconds=30)).isoformat()})
        consumer.drain()
        first_summary = store.summary()
        assert (first_summary["received"],first_summary["accepted"],first_summary["duplicates"],first_summary["quarantined"]) == (8,2,1,5)
        tables = store.snapshot("c01")
        audit["checkpoints"].append({"checkpoint": "c01", "summary": first_summary, "tables": tables})
        write_json(audit_path, audit)
        if client:
            publish(client, project, dataset, "c01", tables, audit, audit_path)
        print("[stream] checkpoint c01: 8 recebimentos, 2 únicos, 1 duplicado, 5 em quarentena", flush=True)

        consumer.stop()
        consumer = None
        recovery = event("e03", a, 62)
        send(recovery)
        try:
            store.process_once(inject_failure=True)
        except RuntimeError as exc:
            if str(exc) != "FALHA_SIMULADA_ANTES_DO_COMMIT":
                raise
            state = store.summary()
            assert state["pending"] == 1 and state["unique_events"] == 2 and state["gold_rows"] == 2
            audit["proofs"]["rollback_before_commit"] = {"error": str(exc), "pending": 1, "events_unchanged": True}
        else:
            raise AssertionError("Falha antes do commit não ocorreu")
        store = EventStore(directory, baseline)
        consumer = Consumer(store, interval)
        consumer.start()
        consumer.drain()
        assert store.summary()["unique_events"] == 3
        audit["proofs"]["restart_recovered_pending_event"] = True
        print("[stream] falha antes do commit comprovada; novo consumidor recuperou o pendente", flush=True)
        send(recovery)
        send({**recovery, "taxa_alfabetizacao": 63})
        older = event("e04", a, 55)
        time.sleep(0.04)
        newer = event("e05", a, 65)
        send(newer)
        send(older)
        send(event("e06", b, 75))
        send({**event("invalid_version", b, 60), "schema_version": 2})
        send(event("invalid_nan", b, float("nan")))
        send({**event("invalid_naive", b, 60), "produced_at": datetime.now().isoformat()})
        consumer.drain()
        consumer.stop()
        consumer = None
        final = store.summary()
        assert (final["received"],final["accepted"],final["duplicates"],final["quarantined"],final["pending"],final["gold_rows"]) == (17,6,2,9,0,2)
        assert final["unique_events"] == final["accepted"]
        assert final["received"] == final["accepted"] + final["duplicates"] + final["quarantined"]
        assert final["microbatches"] >= 3
        with store.connect() as con:
            state_a = con.execute("SELECT e.event_id,e.taxa FROM state s JOIN events e USING(event_id) WHERE s.id_municipio=?", (a,)).fetchone()
            assert tuple(state_a) == ("e05",65)
            assert con.execute("SELECT updated_state FROM events WHERE event_id='e04'").fetchone()[0] == 0
            assert con.execute("SELECT count(*) FROM events WHERE origem<>'SIMULADO' OR latency_ingest_ms<0 OR latency_processing_ms<latency_ingest_ms").fetchone()[0] == 0
        audit["proofs"]["late_event_preserved_without_overwriting_newer_state"] = True
        restart = EventStore(directory, baseline)
        assert restart.process_once() == 0 and restart.summary() == final
        audit["proofs"]["restart_without_new_events_does_not_reapply"] = True
        assert all(digest(Path(path)) == fingerprint for path,fingerprint in official_hashes.items())
        audit["proofs"]["official_files_unchanged"] = True
        audit["proofs"]["all_received_events_accounted_for"] = True
        tables = store.snapshot("c02")
        audit["checkpoints"].append({"checkpoint": "c02", "summary": final, "tables": tables})
        write_json(audit_path, audit)
        if client:
            publish(client, project, dataset, "c02", tables, audit, audit_path)
            audit["billing_after"] = require_no_billing(client, project)
            audit["console_url"] = f"https://console.cloud.google.com/bigquery?project={project}&p={project}&d={dataset}&page=dataset"
        audit.update(status="SUCCESS", finished_at=now(), duration_seconds=round(time.monotonic()-started,3), summary=final)
        write_json(audit_path, audit)
        print(json.dumps({"status": audit["status"], "summary": final, "console_url": audit.get("console_url")}, ensure_ascii=False), flush=True)
    except Exception as exc:
        audit.update(status="FAILED", finished_at=now(), error=f"{type(exc).__name__}: {exc}", duration_seconds=round(time.monotonic()-started,3))
        write_json(audit_path, audit)
        raise
    finally:
        if consumer:
            consumer.stop()
        if receiver:
            receiver.stop()
        if client:
            client.close()
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="Publicar na GCP, somente a partir do Cloud Shell sem faturamento")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--interval", type=float, default=0.5)
    args = parser.parse_args()
    def main():
        baseline = args.baseline
        if baseline is None:
            latest = json.loads((ROOT / "data" / "latest.json").read_text(encoding="utf-8"))
            baseline = Path(latest["gold"]) / "comparacao_municipal_2024.csv"
        return execute(baseline, args.project, args.interval)

    from alerts import run_monitored
    run_monitored("streaming", main)
