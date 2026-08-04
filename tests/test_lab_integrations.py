import os
import unittest
from unittest.mock import patch

from backend.services.lab_integrations import (
    LabDisabledError,
    inspect_offensive_repository,
    inspect_own_instagram_account,
    integration_status,
)


class TestLabIntegrations(unittest.TestCase):
    def test_offensive_repository_is_only_inspected_statically(self) -> None:
        result = inspect_offensive_repository()

        self.assertFalse(result["executed"])
        self.assertFalse(result["network_access"])
        self.assertEqual(result["classification"], "prohibited_offensive_capability")
        self.assertGreater(result["summary"]["python_files"], 0)
        self.assertGreater(result["indicator_counts"]["credential_attempts"], 0)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in result["files"]))

    def test_instagram_integration_is_disabled_by_default(self) -> None:
        with patch.dict(os.environ, {"ENABLE_INSTAGRAPI_LAB": "false"}):
            with self.assertRaises(LabDisabledError):
                inspect_own_instagram_account("owner", "password", 1, 0, "test")

    def test_status_exposes_safe_modes(self) -> None:
        status = integration_status()
        self.assertEqual(status["instagrapi"]["mode"], "cuenta_propia")
        self.assertEqual(status["instagram_bruter"]["mode"], "analisis_estatico_sin_ejecucion")


if __name__ == "__main__":
    unittest.main()
