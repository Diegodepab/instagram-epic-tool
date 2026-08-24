import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import backend.infrastructure.instagram_export_reader as zip_parser
from backend.utils.zip_parser import (
    ExportFormatError,
    UnsafeArchiveError,
    parse_instagram_export,
    parse_instagram_export_with_diagnostics,
)


def relationship(username: str) -> dict:
    return {
        "title": "",
        "media_list_data": [],
        "string_list_data": [
            {
                "href": f"https://www.instagram.com/{username}",
                "value": username,
                "timestamp": 1_700_000_000,
            }
        ],
    }


def make_export_zip(files: dict[str, object]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            archive.writestr(name, json.dumps(payload))
    return output.getvalue()


class TestInstagramExportParser(unittest.TestCase):
    def setUp(self) -> None:
        base = "your_instagram_activity/connections/followers_and_following"
        self.files = {
            f"{base}/followers_1.json": [relationship("Alice"), relationship("mutual.user")],
            f"{base}/followers_2.json": [relationship("second_part")],
            f"{base}/following.json": {
                "relationships_following": [
                    relationship("mutual.user"),
                    relationship("Bob_2"),
                ]
            },
            "personal_information/personal_information.json": {"ignored": True},
        }

    def test_parses_all_follower_parts_and_builds_inverse_edges(self) -> None:
        following_map, follower_map = parse_instagram_export(
            make_export_zip(self.files), "Owner.Account"
        )

        self.assertEqual(following_map["owner.account"], {"mutual.user", "bob_2"})
        self.assertEqual(
            follower_map["owner.account"], {"alice", "mutual.user", "second_part"}
        )
        self.assertEqual(follower_map["bob_2"], {"owner.account"})
        self.assertEqual(following_map["alice"], {"owner.account"})

    def test_accepts_an_extracted_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, payload in self.files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload), encoding="utf-8")

            following_map, follower_map = parse_instagram_export(root, "owner")

        self.assertEqual(len(following_map["owner"]), 2)
        self.assertEqual(len(follower_map["owner"]), 3)

    def test_rejects_zip_slip_paths(self) -> None:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("../followers_1.json", "[]")
            archive.writestr("following.json", '{"relationships_following": []}')

        with self.assertRaises(UnsafeArchiveError):
            parse_instagram_export(output.getvalue(), "owner")

    def test_rejects_exports_without_both_relationship_lists(self) -> None:
        archive = make_export_zip({"connections/followers_1.json": []})

        with self.assertRaisesRegex(ExportFormatError, "following.json"):
            parse_instagram_export(archive, "owner")

    def test_rejects_html_exports(self) -> None:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("connections/followers_1.html", "<html></html>")
            archive.writestr("connections/following.html", "<html></html>")

        with self.assertRaisesRegex(ExportFormatError, "formato HTML"):
            parse_instagram_export(output.getvalue(), "owner")

    def test_explains_mixed_html_and_json_exports(self) -> None:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("connections/followers_1.html", "<html></html>")
            archive.writestr(
                "connections/following.json",
                json.dumps({"relationships_following": []}),
            )

        with self.assertRaisesRegex(ExportFormatError, "JSON, no HTML"):
            parse_instagram_export(output.getvalue(), "owner")

    def test_large_unrelated_media_does_not_consume_json_limit(self) -> None:
        files = {
            "connections/followers_1.json": [relationship("alice")],
            "connections/following.json": {
                "relationships_following": [relationship("bob")]
            },
        }
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("media/large-video-placeholder.bin", b"x" * 10_000)
            for name, payload in files.items():
                archive.writestr(name, json.dumps(payload))

        original_limit = zip_parser.MAX_UNCOMPRESSED_BYTES
        zip_parser.MAX_UNCOMPRESSED_BYTES = 2_000
        try:
            following_map, follower_map = parse_instagram_export(output.getvalue(), "owner")
        finally:
            zip_parser.MAX_UNCOMPRESSED_BYTES = original_limit

        self.assertEqual(following_map["owner"], {"bob"})
        self.assertEqual(follower_map["owner"], {"alice"})

    def test_detects_a_likely_partial_follower_date_range(self) -> None:
        follower = relationship("alice")
        follower["string_list_data"][0]["timestamp"] = 1_750_000_000
        followed = relationship("bob")
        followed["string_list_data"][0]["timestamp"] = 1_400_000_000
        archive = make_export_zip({
            "connections/followers_1.json": [follower],
            "connections/following.json": {
                "relationships_following": [followed, relationship("charlie")]
            },
        })

        _, _, diagnostics = parse_instagram_export_with_diagnostics(archive, "owner")

        self.assertTrue(diagnostics.likely_partial_followers)


if __name__ == "__main__":
    unittest.main()
