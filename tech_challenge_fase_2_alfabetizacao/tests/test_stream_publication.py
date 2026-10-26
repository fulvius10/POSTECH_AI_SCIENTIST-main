import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import stream_demo


class CheckpointPublicationTests(unittest.TestCase):
    def test_cloud_row_mismatch_preserves_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pointer = root / "data/streaming_latest.json"
            pointer.parent.mkdir()
            pointer.write_text(json.dumps({"checkpoint": "c01"}))
            original = pointer.read_bytes()
            client = MagicMock()
            client.get.return_value.json.return_value = {"numRows": "1"}
            tables = {"gold_cenario_municipal": {"file": "unused.parquet", "rows": 2, "sha256": "unused"}}
            job = {"statistics": {"load": {"outputRows": "2"}}}
            with patch.object(stream_demo, "ROOT", root), patch.object(stream_demo, "require_no_billing"), \
                    patch.object(stream_demo, "load_parquet", return_value=job):
                with self.assertRaisesRegex(ValueError, "Contagem divergente"):
                    stream_demo.publish(client, "teste-fase2", "dataset", "c02", tables,
                                        {"run_id": "test", "jobs": []}, root / "audit.json")
            self.assertEqual(pointer.read_bytes(), original)
            client.patch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
