import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from streaming import EventStore, Receiver
from stream_demo import event


class StreamingGuaranteeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline = self.root / "baseline.csv"
        with self.baseline.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["id_municipio", "nome_municipio", "sigla_uf", "ano", "resultado_publicado", "resultado_agregado", "meta_alfabetizacao_2024"])
            writer.writeheader()
            writer.writerow(dict(id_municipio="3106200", nome_municipio="Belo Horizonte", sigla_uf="MG", ano=2024,
                                 resultado_publicado=68.58, resultado_agregado=68.58, meta_alfabetizacao_2024=61.33))
        self.store = EventStore(self.root / "run", self.baseline)

    def receive(self, payload):
        self.store.receive(json.dumps(payload).encode())

    def test_http_ack_means_durable_receipt_before_processing(self):
        receiver = Receiver(self.store)
        receiver.start()
        self.addCleanup(receiver.stop)
        result = requests.post(receiver.url, json=event("http01", "3106200", 62), timeout=5)
        self.assertEqual(result.status_code, 202)
        reopened = EventStore(self.root / "run", self.baseline)
        self.assertEqual(reopened.summary()["pending"], 1)
        self.assertEqual(reopened.summary()["unique_events"], 0)

    def test_failure_rolls_back_state_and_restart_processes_exactly_once(self):
        payload = event("recover01", "3106200", 65)
        self.receive(payload)
        with self.assertRaisesRegex(RuntimeError, "ANTES_DO_COMMIT"):
            self.store.process_once(inject_failure=True)
        self.assertEqual(self.store.summary()["pending"], 1)
        self.assertEqual(self.store.summary()["unique_events"], 0)
        self.assertEqual(self.store.summary()["gold_rows"], 0)
        reopened = EventStore(self.root / "run", self.baseline)
        reopened.process_once()
        self.receive(payload)
        reopened.process_once()
        self.assertEqual(reopened.summary()["unique_events"], 1)
        self.assertEqual(reopened.summary()["duplicates"], 1)
        self.assertEqual(reopened.process_once(), 0)

    def test_reused_id_with_changed_value_is_quarantined(self):
        payload = event("same01", "3106200", 65)
        self.receive(payload)
        self.receive({**payload, "taxa_alfabetizacao": 90})
        self.store.process_once()
        self.assertEqual(self.store.summary()["quarantined"], 1)
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT taxa FROM events").fetchone()[0], 65)
            self.assertEqual(con.execute("SELECT reason FROM deliveries WHERE status='QUARENTENA'").fetchone()[0], "ID_REUTILIZADO_PAYLOAD_DIFERENTE")

    def test_late_event_is_retained_but_does_not_replace_newer(self):
        old = {**event("older", "3106200", 40), "produced_at": (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()}
        new = event("newer", "3106200", 80)
        self.receive(new)
        self.receive(old)
        self.store.process_once()
        with self.store.connect() as con:
            self.assertEqual(con.execute("SELECT event_id FROM state").fetchone()[0], "newer")
            self.assertEqual(con.execute("SELECT count(*) FROM events").fetchone()[0], 2)

    def test_invalid_inputs_cannot_advance_to_silver_or_gold(self):
        base = event("bad", "3106200", 50)
        invalid = [
            {**base, "taxa_alfabetizacao": value} for value in (True, None, -1, 101, float("nan"), float("inf"), 10**400)
        ] + [{**base, "origem": "OFICIAL"}, {**base, "id_municipio": "0000000"},
             {**base, "ano": True}, {**base, "rede": "Pública"}, {**base, "schema_version": 2},
             {**base, "produced_at": "2024-01-01"},
             {**base, "produced_at": (datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}]
        for payload in invalid:
            self.receive(payload)
        self.store.receive(b'{"event_id":"one","event_id":"two"}')
        self.store.receive(b'not json')
        self.store.process_once()
        summary = self.store.summary()
        self.assertEqual(summary["quarantined"], len(invalid)+2)
        self.assertEqual(summary["unique_events"], 0)
        self.assertEqual(summary["gold_rows"], 0)

    def test_changed_official_baseline_cannot_silently_reuse_checkpoint(self):
        self.baseline.write_text(self.baseline.read_text(encoding="utf-8").replace("68.58", "69.58"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "referência oficial mudou"):
            EventStore(self.root / "run", self.baseline)


if __name__ == "__main__":
    unittest.main()
