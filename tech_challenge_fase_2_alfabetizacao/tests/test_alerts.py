import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alerts import Alerts, run_monitored
from ingest import now


class AlertDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.alerts = Alerts(self.root)
        self.alerts.setup("Responsável de teste")
        self.http = patch("alerts.requests.post")
        self.post = self.http.start()
        self.addCleanup(self.http.stop)
        self.post.return_value = self.accepted()
        self.sleep = patch("alerts.time.sleep")
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    @staticmethod
    def accepted():
        response = MagicMock(status_code=200)
        response.json.return_value = {"event": "message", "id": "provider123"}
        return response

    def test_persisted_success_is_not_sent_again(self):
        incident = self.alerts.enqueue("run01", "batch", "ValueError", now())
        self.assertEqual(self.alerts.deliver(incident)["status"], "SENT")
        reopened = Alerts(self.root)
        same = reopened.enqueue("run01", "batch", "ValueError", now())
        self.assertEqual(same, incident)
        self.assertTrue(reopened.deliver(same)["duplicate_suppressed"])
        self.post.assert_called_once()

    def test_unavailable_service_remains_pending_then_retries(self):
        self.post.return_value = MagicMock(status_code=503)
        incident = self.alerts.enqueue("retry01", "streaming", "TimeoutError", now())
        self.assertEqual(self.alerts.deliver(incident)["status"], "PENDING")
        self.assertEqual(len(self.alerts.export()["attempts"]), 3)
        self.post.return_value = self.accepted()
        self.assertEqual(self.alerts.retry()[0]["status"], "SENT")
        self.assertEqual(len(self.alerts.export()["attempts"]), 4)

    def test_failure_to_notify_does_not_turn_pipeline_failure_into_success(self):
        self.post.side_effect = requests.Timeout("https://ntfy.sh/private-topic")
        def failing():
            raise ValueError("falha original")
        with self.assertRaisesRegex(ValueError, "falha original"):
            run_monitored("batch", failing, self.root)
        audit = json.loads(next((self.root/"data/monitor").glob("*.json")).read_text())
        self.assertEqual(audit["status"], "FAILED")
        self.assertEqual(audit["notification"]["status"], "PENDING")
        report = json.dumps(self.alerts.export())
        self.assertNotIn("private-topic", report)
        self.assertNotIn(self.alerts.config()["topic"], report)

    def test_real_failure_dispatches_and_still_raises_original_error(self):
        def failing():
            raise KeyError("falha")
        with self.assertRaises(KeyError):
            run_monitored("streaming", failing, self.root)
        audit = json.loads(next((self.root/"data/monitor").glob("*.json")).read_text())
        self.assertEqual(audit["notification"]["status"], "SENT")
        self.assertEqual(audit["status"], "FAILED")
        self.assertEqual(len(self.alerts.export()["notifications"]), 1)

    def test_success_does_not_send_alert(self):
        self.assertEqual(run_monitored("batch", lambda: {"status": "SUCCESS"}, self.root), {"status": "SUCCESS"})
        self.post.assert_not_called()

    def test_controlled_demonstration_is_identified_in_the_notification(self):
        def failing():
            raise ValueError("falha controlada")
        with patch.dict("os.environ", {"POSTECH_ALERT_TEST_MODE": "1"}):
            with self.assertRaises(ValueError):
                run_monitored("batch", failing, self.root)
        self.assertIn("TESTE CONTROLADO", self.post.call_args.kwargs["json"]["title"])

    def test_missing_configuration_is_explicit_and_preserves_incident(self):
        self.alerts.config_path.unlink()
        incident = self.alerts.enqueue("unconfigured", "batch", "ValueError", now())
        self.assertEqual(self.alerts.deliver(incident)["status"], "UNCONFIGURED")
        self.assertEqual(self.alerts.export()["notifications"][0]["status"], "PENDING")
        self.post.assert_not_called()

    def test_non_retryable_http_failure_does_not_loop(self):
        self.post.return_value = MagicMock(status_code=403)
        incident = self.alerts.enqueue("forbidden", "batch", "ValueError", now())
        self.assertEqual(self.alerts.deliver(incident)["status"], "PENDING")
        self.post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
