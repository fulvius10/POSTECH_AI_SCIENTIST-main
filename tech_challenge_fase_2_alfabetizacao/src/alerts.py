"""Alertas ntfy gratuitos, com fila persistente e monitoramento dos comandos da pipeline."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import socket
import sqlite3
import time
import os

import requests

from ingest import ROOT, new_run_id, now, write_json


class Alerts:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.directory = root / "data" / "alerts"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.config_path = self.directory / "config.json"
        self.db_path = self.directory / "outbox.sqlite"
        con = self.connect()
        try:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS notifications(
                    notification_id TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,
                    created_at TEXT NOT NULL,attempted_at TEXT,delivered_at TEXT,provider_id TEXT);
                CREATE TABLE IF NOT EXISTS attempts(
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,notification_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,finished_at TEXT,http_status INTEGER,error_class TEXT,
                    duration_seconds REAL,provider_id TEXT);
            """)
            con.commit()
        finally:
            con.close()

    def connect(self):
        # Connections are explicitly closed by callers; FULL is SQLite's default.
        return sqlite3.connect(self.db_path, timeout=30)

    def config(self):
        if not self.config_path.exists():
            return None
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        if config.get("provider") != "ntfy" or config.get("base_url") != "https://ntfy.sh":
            raise ValueError("Configure o provedor gratuito ntfy.sh")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", config.get("topic", "")):
            raise ValueError("Tópico de alerta inválido")
        return config

    def setup(self, owner="Responsável pelo projeto"):
        if not self.config_path.exists():
            write_json(self.config_path, {"provider": "ntfy", "base_url": "https://ntfy.sh",
                       "topic": "postech-fase2-" + secrets.token_hex(16), "owner": owner})
        config = self.config()
        return config["base_url"] + "/" + config["topic"]

    def enqueue(self, incident_id: str, pipeline: str, error_class: str, detected_at: str, test_mode=False):
        notification_id = hashlib.sha256(incident_id.encode()).hexdigest()[:32]
        payload = {"incident_id": incident_id, "pipeline": pipeline, "error_class": error_class,
                   "detected_at": detected_at, "test_mode": bool(test_mode)}
        con = self.connect()
        try:
            with con:
                con.execute("INSERT OR IGNORE INTO notifications VALUES (?,?,'PENDING',?,NULL,NULL,NULL)",
                            (notification_id, json.dumps(payload), now()))
        finally:
            con.close()
        return notification_id

    def deliver(self, notification_id, max_attempts=3):
        if not 1 <= max_attempts <= 3:
            raise ValueError("Use entre uma e três tentativas por envio")
        config = self.config()
        if config is None:
            return {"status": "UNCONFIGURED", "notification_id": notification_id}
        con = self.connect()
        con.row_factory = sqlite3.Row
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM notifications WHERE notification_id=?", (notification_id,)).fetchone()
            if row is None:
                raise ValueError("Alerta não encontrado")
            if row["status"] == "SENT":
                con.rollback()
                return {"status": "SENT", "notification_id": notification_id, "provider_id": row["provider_id"],
                        "duplicate_suppressed": True, "delivered_at": row["delivered_at"]}
            if row["status"] == "SENDING" and (datetime.now(timezone.utc)-datetime.fromisoformat(row["attempted_at"])).total_seconds() < 90:
                con.rollback()
                return {"status": "IN_PROGRESS", "notification_id": notification_id}
            con.execute("UPDATE notifications SET status='SENDING',attempted_at=? WHERE notification_id=?", (now(), notification_id))
            con.commit()
            payload = json.loads(row["payload"])
            prefix = "TESTE CONTROLADO - " if payload.get("test_mode") else ""
            message = (prefix + f"A pipeline {payload['pipeline']} terminou com falha.\n"
                       f"Execução: {payload['incident_id']}\nDetectada em: {payload['detected_at']}\n"
                       f"Tipo: {payload['error_class']}\nResponsável: {config.get('owner','Responsável pelo projeto')}\n"
                       "Consulte data/monitor/ para o registro. A publicação válida anterior permanece disponível.")
            for number in range(max_attempts):
                started = time.monotonic()
                with con:
                    attempt_id = con.execute("INSERT INTO attempts(notification_id,started_at) VALUES (?,?)", (notification_id, now())).lastrowid
                http_status = provider_id = error = None
                try:
                    response = requests.post(config["base_url"] + "/", json={"topic": config["topic"],
                        "title": prefix + f"POSTECH Fase 2: falha em {payload['pipeline']}", "message": message,
                        "priority": 4, "tags": ["warning"]}, timeout=(3, 5), allow_redirects=False)
                    http_status = response.status_code
                    if not 200 <= http_status < 300:
                        error = "HTTP_ERROR"
                    else:
                        receipt = response.json()
                        if receipt.get("event") != "message" or not isinstance(receipt.get("id"), str):
                            error = "INVALID_PROVIDER_RECEIPT"
                        else:
                            provider_id = receipt["id"]
                except Exception as exc:
                    # Não registrar exception text: pode conter o URL privado do tópico.
                    error = type(exc).__name__
                finished = now()
                with con:
                    con.execute("""UPDATE attempts SET finished_at=?,http_status=?,error_class=?,duration_seconds=?,provider_id=?
                        WHERE attempt_id=?""", (finished, http_status, error, time.monotonic()-started, provider_id, attempt_id))
                    if provider_id:
                        con.execute("UPDATE notifications SET status='SENT',delivered_at=?,provider_id=? WHERE notification_id=?", (finished, provider_id, notification_id))
                if provider_id:
                    return {"status": "SENT", "notification_id": notification_id, "provider_id": provider_id,
                            "delivered_at": finished, "attempts_this_call": number+1,
                            "seconds_from_failure": (datetime.fromisoformat(finished)-datetime.fromisoformat(payload["detected_at"])).total_seconds()}
                if http_status is not None and 400 <= http_status < 500 and http_status != 429:
                    break
                if number+1 < max_attempts:
                    time.sleep(0.5 * (number+1))
            with con:
                con.execute("UPDATE notifications SET status='PENDING' WHERE notification_id=?", (notification_id,))
            return {"status": "PENDING", "notification_id": notification_id, "last_http_status": http_status,
                    "last_error_class": error}
        finally:
            con.close()

    def retry(self):
        con = self.connect()
        try:
            ids = [row[0] for row in con.execute("SELECT notification_id FROM notifications WHERE status<>'SENT' ORDER BY created_at LIMIT 10")]
        finally:
            con.close()
        return [self.deliver(notification_id) for notification_id in ids]

    def export(self):
        con = self.connect()
        con.row_factory = sqlite3.Row
        try:
            report = {"notifications": [dict(row) for row in con.execute("SELECT * FROM notifications ORDER BY created_at")],
                      "attempts": [dict(row) for row in con.execute("SELECT * FROM attempts ORDER BY attempt_id")]}
            # O destino privado não é incluído no histórico exportável.
            write_json(self.directory / "delivery_history.json", report)
            return report
        finally:
            con.close()


def run_monitored(pipeline, function, root: Path = ROOT):
    run_id = new_run_id().lower()
    path = root / "data" / "monitor" / f"{run_id}.json"
    audit = {"run_id": run_id, "pipeline": pipeline, "started_at": now(), "status": "RUNNING",
             "execution": "GOOGLE_CLOUD_SHELL" if os.environ.get("CLOUD_SHELL") == "true" else "LOCAL",
             "hostname": socket.gethostname()}
    write_json(path, audit)
    started = time.monotonic()
    try:
        result = function()
        audit.update(status="SUCCESS", finished_at=now(), duration_seconds=round(time.monotonic()-started,3))
        if isinstance(result, dict):
            audit["pipeline_run_id"] = result.get("run_id")
            audit["pipeline_status"] = result.get("status")
        write_json(path, audit)
        return result
    except Exception as exc:
        audit.update(status="FAILED", failure_detected_at=now(), error_class=type(exc).__name__,
                     duration_until_failure_seconds=round(time.monotonic()-started,3))
        write_json(path, audit)
        try:
            alerts = Alerts(root)
            notification_id = alerts.enqueue(run_id, pipeline, type(exc).__name__, audit["failure_detected_at"],
                                              test_mode=os.environ.get("POSTECH_ALERT_TEST_MODE") == "1")
            audit["notification"] = alerts.deliver(notification_id)
            alerts.export()
        except Exception as alert_error:
            audit["notification"] = {"status": "DELIVERY_ERROR", "error_class": type(alert_error).__name__}
        audit["finished_at"] = now()
        audit["duration_seconds"] = round(time.monotonic()-started,3)
        write_json(path, audit)
        print(f"[alert] pipeline FAILED; notification={audit['notification']['status']}; monitor={run_id}", flush=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("setup", "retry", "export"))
    parser.add_argument("--owner", default="Responsável pelo projeto")
    args = parser.parse_args()
    alerts = Alerts()
    if args.action == "setup":
        print(alerts.setup(args.owner))
    elif args.action == "retry":
        results = alerts.retry()
        print(json.dumps(results, ensure_ascii=False))
        alerts.export()
        if any(item["status"] != "SENT" for item in results):
            raise SystemExit(1)
    else:
        print(json.dumps(alerts.export(), ensure_ascii=False))
