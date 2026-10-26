"""Recepção HTTP durável e consumo incremental de eventos simulados, sem serviços pagos."""
from __future__ import annotations

import base64
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
import time

import duckdb

from ingest import digest, now, write_json


class EventStore:
    def __init__(self, directory: Path, baseline: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "stream.sqlite"
        with self.connect() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript("""
                CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS baseline(
                    id_municipio TEXT PRIMARY KEY,nome_municipio TEXT,sigla_uf TEXT,ano INTEGER,
                    resultado_oficial REAL,resultado_agregado REAL,meta_2024 REAL);
                CREATE TABLE IF NOT EXISTS deliveries(
                    delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,payload_base64 TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDENTE',reason TEXT,
                    event_id TEXT,produced_at TEXT,processed_at TEXT,latency_ingest_ms REAL,
                    latency_processing_ms REAL,microbatch_id INTEGER);
                CREATE INDEX IF NOT EXISTS pending ON deliveries(status,delivery_id);
                CREATE TABLE IF NOT EXISTS events(
                    event_id TEXT PRIMARY KEY,payload_hash TEXT NOT NULL,id_municipio TEXT NOT NULL,
                    ano INTEGER NOT NULL,taxa REAL NOT NULL,origem TEXT NOT NULL CHECK(origem='SIMULADO'),
                    produced_at TEXT NOT NULL,ingested_at TEXT NOT NULL,processed_at TEXT NOT NULL,
                    latency_ingest_ms REAL NOT NULL,latency_processing_ms REAL NOT NULL,
                    microbatch_id INTEGER NOT NULL,updated_state INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS state(
                    id_municipio TEXT PRIMARY KEY,event_id TEXT NOT NULL,produced_at TEXT NOT NULL,
                    FOREIGN KEY(event_id) REFERENCES events(event_id));
                CREATE TABLE IF NOT EXISTS microbatches(
                    microbatch_id INTEGER PRIMARY KEY AUTOINCREMENT,started_at TEXT,finished_at TEXT,
                    input_count INTEGER,accepted INTEGER,duplicates INTEGER,quarantined INTEGER,
                    duration_seconds REAL);
            """)
            existing = con.execute("SELECT value FROM config WHERE key='baseline_sha256'").fetchone()
            baseline_hash = digest(baseline)
            if existing:
                if existing[0] != baseline_hash:
                    raise ValueError("A referência oficial mudou; use outro diretório de cenário.")
            else:
                with baseline.open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream))
                con.execute("BEGIN IMMEDIATE")
                try:
                    con.executemany("INSERT INTO baseline VALUES (?,?,?,?,?,?,?)", [
                        (r["id_municipio"], r["nome_municipio"], r["sigla_uf"], int(r["ano"]),
                         float(r["resultado_publicado"]) if r["resultado_publicado"] else None,
                         float(r["resultado_agregado"]) if r["resultado_agregado"] else None,
                         float(r["meta_alfabetizacao_2024"]) if r["meta_alfabetizacao_2024"] else None)
                        for r in rows])
                    con.execute("INSERT INTO config VALUES ('baseline_sha256',?)", (baseline_hash,))
                    con.commit()
                except Exception:
                    con.rollback()
                    raise

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA synchronous=FULL")
        try:
            yield con
        finally:
            con.close()

    def receive(self, payload: bytes) -> int:
        # O ACK HTTP só acontece depois do commit durável deste recebimento.
        with self.connect() as con:
            cur = con.execute("INSERT INTO deliveries(payload_base64,ingested_at) VALUES (?,?)",
                              (base64.b64encode(payload).decode("ascii"), now()))
            return cur.lastrowid

    @staticmethod
    def validate(raw: bytes, ingested_at: str, con) -> dict:
        def unique_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("CHAVE_JSON_REPETIDA")
                result[key] = value
            return result

        try:
            event = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys)
        except (ValueError, UnicodeError):
            raise ValueError("JSON_INVALIDO") from None
        required = {"event_id", "schema_version", "event_type", "origem", "produced_at",
                    "ano", "id_municipio", "serie", "rede", "taxa_alfabetizacao"}
        if not isinstance(event, dict) or set(event) != required:
            raise ValueError("ESTRUTURA_INVALIDA")
        if not isinstance(event["event_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", event["event_id"]):
            raise ValueError("ID_INVALIDO")
        if type(event["schema_version"]) is not int or event["schema_version"] != 1:
            raise ValueError("VERSAO_INVALIDA")
        if event["event_type"] != "resultado_municipal_atualizado":
            raise ValueError("TIPO_INVALIDO")
        if event["origem"] != "SIMULADO":
            raise ValueError("ORIGEM_INVALIDA")
        if type(event["ano"]) is not int or event["ano"] != 2024 or event["serie"] != "2" or event["rede"] != "Municipal":
            raise ValueError("RECORTE_INVALIDO")
        if not isinstance(event["id_municipio"], str) or not re.fullmatch(r"\d{7}", event["id_municipio"]):
            raise ValueError("TERRITORIO_INVALIDO")
        if not con.execute("SELECT 1 FROM baseline WHERE id_municipio=? AND ano=?", (event["id_municipio"], event["ano"])).fetchone():
            raise ValueError("TERRITORIO_SEM_REFERENCIA")
        rate = event["taxa_alfabetizacao"]
        if type(rate) not in (int, float) or not 0 <= rate <= 100 or not math.isfinite(rate):
            raise ValueError("PERCENTUAL_INVALIDO")
        try:
            produced = datetime.fromisoformat(event["produced_at"])
            if produced.tzinfo is None:
                raise ValueError()
            produced = produced.astimezone(timezone.utc)
            if produced > datetime.fromisoformat(ingested_at):
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError("HORARIO_INVALIDO_OU_FUTURO") from None
        event["produced_at"] = produced.isoformat()
        event["taxa_alfabetizacao"] = float(rate)
        return event

    def process_once(self, limit=100, inject_failure=False) -> int:
        if not 1 <= limit <= 1000:
            raise ValueError("Limite do microlote deve ficar entre 1 e 1000")
        started = time.monotonic()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                deliveries = con.execute("SELECT * FROM deliveries WHERE status='PENDENTE' ORDER BY delivery_id LIMIT ?", (limit,)).fetchall()
                if not deliveries:
                    con.rollback()
                    return 0
                batch_id = con.execute("INSERT INTO microbatches(started_at) VALUES (?)", (now(),)).lastrowid
                counts = {"ACEITO": 0, "DUPLICADO": 0, "QUARENTENA": 0}
                for delivery in deliveries:
                    processed_at = now()
                    event_id = produced_at = ingest_ms = processing_ms = None
                    status, reason = "QUARENTENA", None
                    try:
                        event = self.validate(base64.b64decode(delivery["payload_base64"]), delivery["ingested_at"], con)
                        event_id, produced_at = event["event_id"], event["produced_at"]
                        ingest_ms = (datetime.fromisoformat(delivery["ingested_at"]) - datetime.fromisoformat(produced_at)).total_seconds() * 1000
                        processing_ms = (datetime.fromisoformat(processed_at) - datetime.fromisoformat(produced_at)).total_seconds() * 1000
                        fingerprint = hashlib.sha256(json.dumps(event, sort_keys=True, allow_nan=False).encode()).hexdigest()
                        existing = con.execute("SELECT payload_hash FROM events WHERE event_id=?", (event_id,)).fetchone()
                        if existing:
                            if existing[0] != fingerprint:
                                raise ValueError("ID_REUTILIZADO_PAYLOAD_DIFERENTE")
                            status, reason = "DUPLICADO", "EVENTO_JA_PROCESSADO"
                        else:
                            current = con.execute("SELECT produced_at,event_id FROM state WHERE id_municipio=?", (event["id_municipio"],)).fetchone()
                            update = current is None or (produced_at, event_id) > (current[0], current[1])
                            con.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                                event_id, fingerprint, event["id_municipio"], event["ano"], event["taxa_alfabetizacao"],
                                "SIMULADO", produced_at, delivery["ingested_at"], processed_at, ingest_ms, processing_ms, batch_id, int(update)))
                            if update:
                                con.execute("INSERT INTO state VALUES (?,?,?) ON CONFLICT(id_municipio) DO UPDATE SET event_id=excluded.event_id,produced_at=excluded.produced_at",
                                            (event["id_municipio"], event_id, produced_at))
                            status, reason = "ACEITO", "ESTADO_ATUALIZADO" if update else "ATRASADO_PRESERVADO_SEM_SOBRESCRITA"
                    except ValueError as exc:
                        reason = str(exc)
                    con.execute("""UPDATE deliveries SET status=?,reason=?,event_id=?,produced_at=?,processed_at=?,
                        latency_ingest_ms=?,latency_processing_ms=?,microbatch_id=? WHERE delivery_id=?""",
                        (status, reason, event_id, produced_at, processed_at, ingest_ms, processing_ms, batch_id, delivery["delivery_id"]))
                    counts[status] += 1
                if inject_failure:
                    raise RuntimeError("FALHA_SIMULADA_ANTES_DO_COMMIT")
                con.execute("""UPDATE microbatches SET finished_at=?,input_count=?,accepted=?,duplicates=?,quarantined=?,duration_seconds=?
                    WHERE microbatch_id=?""", (now(), len(deliveries), counts["ACEITO"], counts["DUPLICADO"], counts["QUARENTENA"], time.monotonic()-started, batch_id))
                con.commit()
                return len(deliveries)
            except Exception:
                con.rollback()
                raise

    def summary(self) -> dict:
        with self.connect() as con:
            counts = dict(con.execute("SELECT status,count(*) FROM deliveries GROUP BY status").fetchall())
            result = {"received": sum(counts.values()), "accepted": counts.get("ACEITO", 0),
                      "duplicates": counts.get("DUPLICADO", 0), "quarantined": counts.get("QUARENTENA", 0),
                      "pending": counts.get("PENDENTE", 0), "unique_events": con.execute("SELECT count(*) FROM events").fetchone()[0],
                      "gold_rows": con.execute("SELECT count(*) FROM state").fetchone()[0],
                      "microbatches": con.execute("SELECT count(*) FROM microbatches").fetchone()[0]}
            result["latency_ms"] = dict(con.execute("""SELECT 'ingestion_avg',avg(latency_ingest_ms) FROM events UNION ALL
                SELECT 'ingestion_max',max(latency_ingest_ms) FROM events UNION ALL
                SELECT 'processing_avg',avg(latency_processing_ms) FROM events UNION ALL
                SELECT 'processing_max',max(latency_processing_ms) FROM events""").fetchall())
            return result

    def snapshot(self, checkpoint: str) -> dict:
        target = self.directory / "snapshots" / checkpoint
        target.mkdir(parents=True, exist_ok=False)
        specs = {
            "bronze_recebimentos": ("SELECT delivery_id,payload_base64,ingested_at FROM deliveries ORDER BY delivery_id", "delivery_id BIGINT,payload_base64 VARCHAR,ingested_at VARCHAR"),
            "silver_eventos": ("SELECT * FROM events ORDER BY event_id", "event_id VARCHAR,payload_hash VARCHAR,id_municipio VARCHAR,ano BIGINT,taxa DOUBLE,origem VARCHAR,produced_at VARCHAR,ingested_at VARCHAR,processed_at VARCHAR,latency_ingest_ms DOUBLE,latency_processing_ms DOUBLE,microbatch_id BIGINT,updated_state BOOLEAN"),
            "silver_destinos": ("SELECT delivery_id,status,reason,event_id,produced_at,ingested_at,processed_at,latency_ingest_ms,latency_processing_ms,microbatch_id FROM deliveries ORDER BY delivery_id", "delivery_id BIGINT,status VARCHAR,reason VARCHAR,event_id VARCHAR,produced_at VARCHAR,ingested_at VARCHAR,processed_at VARCHAR,latency_ingest_ms DOUBLE,latency_processing_ms DOUBLE,microbatch_id BIGINT"),
            "quarentena": ("SELECT delivery_id,payload_base64,ingested_at,reason FROM deliveries WHERE status='QUARENTENA' ORDER BY delivery_id", "delivery_id BIGINT,payload_base64 VARCHAR,ingested_at VARCHAR,reason VARCHAR"),
            "metricas_microlotes": ("SELECT * FROM microbatches ORDER BY microbatch_id", "microbatch_id BIGINT,started_at VARCHAR,finished_at VARCHAR,input_count BIGINT,accepted BIGINT,duplicates BIGINT,quarantined BIGINT,duration_seconds DOUBLE"),
            "gold_cenario_municipal": ("""SELECT b.id_municipio,b.nome_municipio,b.sigla_uf,b.ano,'Municipal','SIMULADO',
                b.resultado_oficial,b.resultado_agregado,e.taxa,b.meta_2024,e.taxa-b.meta_2024,
                CASE WHEN b.meta_2024 IS NULL THEN 'Sem meta' WHEN e.taxa>=b.meta_2024 THEN 'Atingiu' ELSE 'Não atingiu' END,
                e.event_id,e.produced_at,e.ingested_at,e.processed_at,e.latency_processing_ms
                FROM state s JOIN events e USING(event_id) JOIN baseline b ON b.id_municipio=s.id_municipio ORDER BY b.id_municipio""",
                "id_municipio VARCHAR,nome_municipio VARCHAR,sigla_uf VARCHAR,ano BIGINT,rede VARCHAR,origem VARCHAR,resultado_oficial_referencia DOUBLE,resultado_agregado_referencia DOUBLE,resultado_simulado DOUBLE,meta_2024 DOUBLE,saldo_simulado_pp DOUBLE,situacao_simulada VARCHAR,event_id VARCHAR,produced_at VARCHAR,ingested_at VARCHAR,processed_at VARCHAR,latency_processing_ms DOUBLE")}
        output = {}
        with self.connect() as source, duckdb.connect() as dest:
            source.execute("BEGIN")
            expected_gold = source.execute("SELECT count(*) FROM state").fetchone()[0]
            for name, (query, schema) in specs.items():
                rows = source.execute(query).fetchall()
                if name == "gold_cenario_municipal" and len(rows) != expected_gold:
                    raise ValueError("Junção Gold perdeu ou multiplicou estados municipais")
                dest.execute(f'CREATE TABLE "{name}" ({schema})')
                if rows:
                    dest.executemany(f'INSERT INTO "{name}" VALUES ({",".join("?" for _ in rows[0])})', [tuple(r) for r in rows])
                for suffix, options in (("parquet", "FORMAT PARQUET, COMPRESSION ZSTD"), ("csv", "HEADER")):
                    path = target / f"{name}.{suffix}"
                    dest.execute(f'COPY "{name}" TO ? ({options})', [str(path)])
                output[name] = {"file": str(target / f"{name}.parquet"), "rows": len(rows),
                                "sha256": digest(target / f"{name}.parquet")}
            source.commit()
        if output["bronze_recebimentos"]["rows"] != output["silver_destinos"]["rows"]:
            raise ValueError("Recebimentos e destinos não conciliam")
        write_json(target / "manifest.json", {"checkpoint": checkpoint, "tables": output,
                   "gold_join": {"expected": expected_gold, "matched": output["gold_cenario_municipal"]["rows"],
                                 "match_rate": 1.0 if expected_gold else None}})
        return output


class Receiver:
    def __init__(self, store: EventStore):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path != "/events":
                    self.send_error(404)
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self.send_error(400)
                    return
                if not 0 < size <= 16384:
                    self.send_error(413)
                    return
                raw = self.rfile.read(size)
                delivery_id = store.receive(raw)
                body = json.dumps({"delivery_id": delivery_id, "status": "PERSISTIDO"}).encode()
                self.send_response(202)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{self.server.server_port}/events"

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class Consumer:
    def __init__(self, store: EventStore, interval=0.5):
        self.store, self.interval = store, interval
        self.stopping = threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self.work, daemon=True)

    def work(self):
        try:
            while not self.stopping.is_set():
                count = self.store.process_once()
                if count:
                    print(f"[stream] microlote: {count} recebimentos processados", flush=True)
                self.stopping.wait(self.interval)
        except Exception as exc:
            self.error = exc
            self.stopping.set()

    def start(self):
        self.thread.start()

    def drain(self, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.error:
                raise RuntimeError("Consumidor falhou") from self.error
            if not self.store.summary()["pending"]:
                return
            time.sleep(0.05)
        raise TimeoutError("Há eventos pendentes no consumidor")

    def stop(self):
        self.stopping.set()
        self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise TimeoutError("Consumidor não encerrou")
        if self.error:
            raise RuntimeError("Consumidor falhou") from self.error
