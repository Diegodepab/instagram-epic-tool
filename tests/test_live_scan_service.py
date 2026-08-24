import os
import secrets
import unittest
from unittest.mock import patch

from backend.services import live_scan_service as service
from backend.services.live_scan_service import LiveScanNotFoundError, PendingScan
from backend.services.session_store import session_store


class TestLiveScanCommit(unittest.TestCase):
    def setUp(self) -> None:
        self.env = patch.dict(os.environ, {"ENABLE_INSTAGRAPI_LAB": "true"})
        self.env.start()
        self.scan_ids: list[str] = []
        self.session_ids: list[str] = []

    def tearDown(self) -> None:
        for scan_id in self.scan_ids:
            with service._scan_lock:
                service._pending_scans.pop(scan_id, None)
        for session_id in self.session_ids:
            session_store.delete(session_id)
        self.env.stop()

    def add_scan(self, target: str, followers: list[str], following: list[str]) -> str:
        scan_id = secrets.token_urlsafe(24)
        self.scan_ids.append(scan_id)
        with service._scan_lock:
            service._pending_scans[scan_id] = PendingScan(
                scan_id=scan_id,
                target_username=target,
                followers=followers,
                following=following,
            )
        return scan_id

    def test_two_accounts_merge_and_preserve_shared_connections(self) -> None:
        first_scan = self.add_scan(
            "account_one", ["shared", "fan_one"], ["shared", "followed_one"]
        )
        first = service.commit_scan(first_scan)
        self.session_ids.append(first["session_id"])

        second_scan = self.add_scan(
            "account_two", ["shared", "fan_two"], ["shared", "followed_two"]
        )
        merged = service.commit_scan(second_scan, first["session_id"])
        stored = session_store.get(first["session_id"])

        self.assertEqual(merged["session_id"], first["session_id"])
        self.assertEqual(merged["imported_profiles"], ["account_one", "account_two"])
        self.assertEqual(stored.root_user_id, "account_one")
        self.assertEqual(stored.following_map["shared"], {"account_one", "account_two"})
        self.assertEqual(
            stored.relationship_sources[("shared", "account_one")], {"account_one"}
        )
        self.assertEqual(
            stored.relationship_sources[("shared", "account_two")], {"account_two"}
        )

    def test_failed_merge_keeps_preview_available_for_retry(self) -> None:
        scan_id = self.add_scan("account_two", ["shared"], ["friend"])

        with self.assertRaises(LiveScanNotFoundError):
            service.commit_scan(scan_id, "missing-session")

        created = service.commit_scan(scan_id)
        self.session_ids.append(created["session_id"])
        self.assertEqual(created["imported_profiles"], ["account_two"])


if __name__ == "__main__":
    unittest.main()
