import io
import json
import unittest
import zipfile

from pydantic import ValidationError

from backend.application.instagram_import_service import analyze_instagram_export
from backend.domain.models import NodeGroup, RawStringListItem
from backend.domain.relationship_service import calculate_relationships
from backend.infrastructure.instagram_export_reader import ExportFormatError


def zip_bytes(files: dict[str, object]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename, payload in files.items():
            archive.writestr(filename, json.dumps(payload))
    return output.getvalue()


class TestDDDImportService(unittest.TestCase):
    def test_set_mathematics_are_exact(self) -> None:
        result = calculate_relationships(
            followers={"mutual", "fan"},
            following={"mutual", "non_follower"},
        )

        self.assertEqual(result.mutuals, {"mutual"})
        self.assertEqual(result.fans, {"fan"})
        self.assertEqual(result.non_followers, {"non_follower"})

    def test_all_partitions_and_nested_usernames_reach_the_graph(self) -> None:
        archive = zip_bytes({
            "connections/followers_and_following/followers.json": [
                {"metadata": {"nested": {"value": "fan"}}}
            ],
            "connections/followers_and_following/followers_1.json": [
                {"string_list_data": [{"value": "mutual", "timestamp": 10}]}
            ],
            "connections/followers_and_following/followers_2.json": [
                {"string_list_data": [{"href": "https://instagram.com/second_fan/"}]}
            ],
            "connections/followers_and_following/following.json": {
                "relationships_following": [
                    {"title": "mutual", "string_list_data": [{"timestamp": 10}]},
                    {"title": "non_follower", "string_list_data": []},
                ]
            },
        })

        result = analyze_instagram_export(archive, "owner")
        groups = {node.id: node.group for node in result.graph.nodes}
        links = {(link.source, link.target) for link in result.graph.links}

        self.assertEqual(result.relationships.mutuals, {"mutual"})
        self.assertEqual(result.relationships.fans, {"fan", "second_fan"})
        self.assertEqual(result.relationships.non_followers, {"non_follower"})
        self.assertEqual(groups["owner"], NodeGroup.CENTRAL)
        self.assertEqual(groups["mutual"], NodeGroup.MUTUAL)
        self.assertEqual(groups["fan"], NodeGroup.FAN)
        self.assertEqual(groups["non_follower"], NodeGroup.NON_FOLLOWER)
        self.assertIn(("fan", "owner"), links)
        self.assertIn(("owner", "non_follower"), links)
        self.assertEqual(result.relationship_timestamps[("owner", "mutual")], 10)
        self.assertEqual(result.relationship_timestamps[("mutual", "owner")], 10)

    def test_raw_pydantic_model_is_strict(self) -> None:
        with self.assertRaises(ValidationError):
            RawStringListItem.model_validate({"value": "user", "timestamp": "not-an-int"})

    def test_missing_following_document_is_explicit(self) -> None:
        archive = zip_bytes({"connections/followers_1.json": []})

        with self.assertRaisesRegex(ExportFormatError, "following.json"):
            analyze_instagram_export(archive, "owner")


if __name__ == "__main__":
    unittest.main()
