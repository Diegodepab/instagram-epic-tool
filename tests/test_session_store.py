import unittest

from backend.services.session_store import AnalysisSessionStore, DuplicateImportError, SessionNotFoundError


class TestAnalysisSessionStore(unittest.TestCase):
    def test_creates_reads_and_deletes_a_session(self) -> None:
        store = AnalysisSessionStore(ttl_seconds=60, max_sessions=2)
        session = store.create("owner", {"owner": {"alice"}}, {"owner": set()})

        self.assertEqual(store.get(session.session_id).root_user_id, "owner")
        self.assertTrue(store.delete(session.session_id))
        with self.assertRaises(SessionNotFoundError):
            store.get(session.session_id)

    def test_evicts_the_oldest_session_at_capacity(self) -> None:
        store = AnalysisSessionStore(ttl_seconds=60, max_sessions=1)
        oldest = store.create("first", {"first": set()}, {"first": set()})
        newest = store.create("second", {"second": set()}, {"second": set()})

        with self.assertRaises(SessionNotFoundError):
            store.get(oldest.session_id)
        self.assertEqual(store.get(newest.session_id).root_user_id, "second")

    def test_expired_sessions_are_not_returned(self) -> None:
        store = AnalysisSessionStore(ttl_seconds=0, max_sessions=1)
        session = store.create("owner", {"owner": set()}, {"owner": set()})

        with self.assertRaises(SessionNotFoundError):
            store.get(session.session_id)

    def test_merges_authorized_exports_without_overwriting_the_primary_profile(self) -> None:
        store = AnalysisSessionStore(ttl_seconds=60, max_sessions=2)
        session = store.create(
            "owner",
            {"owner": {"friend"}},
            {"owner": set()},
            {("owner", "friend"): 20},
        )

        merged = store.merge(
            session.session_id,
            "friend",
            {"friend": {"second_degree"}},
            {"friend": {"owner"}},
            {("friend", "second_degree"): 30},
        )

        self.assertEqual(merged.root_user_id, "owner")
        self.assertEqual(merged.imported_profiles, {"owner", "friend"})
        self.assertEqual(merged.following_map["friend"], {"second_degree"})
        self.assertEqual(merged.relationship_timestamps[("friend", "second_degree")], 30)

        with self.assertRaises(DuplicateImportError):
            store.merge(session.session_id, "friend", {}, {})


if __name__ == "__main__":
    unittest.main()
