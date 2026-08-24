import unittest

from backend.domain.schemas import ConnectionType
from backend.services.graph_analyzer import GraphAnalyzer


class TestGraphAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        following = {
            "root": {"mutual", "outgoing"},
            "mutual": {"root", "hub"},
            "outgoing": {"hub"},
            "fan": {"root", "hub"},
        }
        followers = {"root": {"mutual", "fan"}}
        self.analyzer = GraphAnalyzer("root", following, followers)

    def test_classifies_first_degree_relationships(self) -> None:
        self.assertEqual(self.analyzer.get_mutuals(), {"mutual"})
        self.assertEqual(self.analyzer.get_traitors(), {"outgoing"})
        self.assertEqual(self.analyzer.get_fans(), {"fan"})

        payload = self.analyzer.get_base_graph()
        node_ids = {node.id for node in payload.nodes}
        self.assertEqual(node_ids, {"root", "mutual", "outgoing", "fan"})
        self.assertTrue(
            any(edge.connection_type == ConnectionType.MUTUAL for edge in payload.edges)
        )

    def test_expansion_returns_only_known_relationships(self) -> None:
        payload = self.analyzer.expand_known_node("mutual")

        self.assertEqual({node.id for node in payload.nodes}, {"mutual", "root", "hub"})
        self.assertEqual(payload.metadata["known_connections"], 2)
        self.assertEqual(payload.metadata["data_scope"], "imported_exports_only")


if __name__ == "__main__":
    unittest.main()
