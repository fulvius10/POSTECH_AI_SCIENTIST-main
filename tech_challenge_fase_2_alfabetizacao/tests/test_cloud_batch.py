import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cloud_batch


class FreeCloudGuardTests(unittest.TestCase):
    def test_billing_enabled_is_rejected(self):
        client = MagicMock()
        client.get.return_value.json.return_value = {"projectId": "teste-fase2", "billingEnabled": True}
        with self.assertRaisesRegex(ValueError, "sem faturamento"):
            cloud_batch.require_no_billing(client, "teste-fase2")

    def test_unknown_billing_state_is_rejected(self):
        client = MagicMock()
        client.get.return_value.json.return_value = {"projectId": "teste-fase2"}
        with self.assertRaises(ValueError):
            cloud_batch.require_no_billing(client, "teste-fase2")

    def test_local_execution_cannot_be_presented_as_cloud(self):
        with patch.dict(os.environ, {"CLOUD_SHELL": "false"}):
            with self.assertRaisesRegex(ValueError, "Cloud Shell"):
                cloud_batch.execute("teste-fase2")


if __name__ == "__main__":
    unittest.main()
