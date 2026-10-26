import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ingest


class DownloadIntegrityTests(unittest.TestCase):
    def run_download(self, responses):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        with patch.object(ingest, "ROOT", root), patch.object(ingest, "new_run_id", return_value="teste"), \
                patch.object(ingest, "session", return_value=MagicMock()), patch.object(ingest, "get", side_effect=responses):
            try:
                path = ingest.download(("uf",))
                return root, path, None
            except ValueError as exc:
                return root, root / "data/bronze/teste", exc

    @staticmethod
    def metadata(modified="1"):
        return {"schema": {"fields": [{"name": "texto", "type": "STRING"}]},
                "numRows": "2", "lastModifiedTime": modified}

    def test_null_and_empty_string_remain_different(self):
        meta = self.metadata()
        _, path, error = self.run_download([meta, {"rows": [{"f": [{"v": None}]}, {"f": [{"v": ""}]}]}, meta])
        self.assertIsNone(error)
        with gzip.open(path / "uf.csv.gz", "rt", encoding="utf-8", newline="") as f:
            self.assertEqual(list(csv.reader(f)), [["texto"], [r"\N"], [""]])
        self.assertEqual(json.loads((path / "manifest.json").read_text())["status"], "SUCCESS")

    def test_source_change_does_not_publish_snapshot(self):
        _, path, error = self.run_download([
            self.metadata(), {"rows": [{"f": [{"v": "A"}]}, {"f": [{"v": "B"}]}]}, self.metadata("2")])
        self.assertIsInstance(error, ValueError)
        self.assertFalse((path / "uf.csv.gz").exists())
        self.assertEqual(json.loads((path / "manifest.json").read_text())["status"], "FAILED")

    def test_incomplete_pagination_does_not_publish_snapshot(self):
        meta = self.metadata()
        _, path, error = self.run_download([meta, {"rows": [{"f": [{"v": "A"}]}]}, meta])
        self.assertIsInstance(error, ValueError)
        self.assertFalse((path / "uf.csv.gz").exists())
        self.assertEqual(json.loads((path / "manifest.json").read_text())["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
