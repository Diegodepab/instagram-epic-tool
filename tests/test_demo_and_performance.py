import unittest

from backend.services.demo_data import generate_demo_data
from backend.services.graph_analyzer import GraphAnalyzer, MAX_GRAPH_PROFILES


class TestDemoAndGraphPerformance(unittest.TestCase):
    def test_demo_is_consistent_and_useful_for_the_product_tour(self) -> None:
        root, following_map, follower_map = generate_demo_data()
        analyzer = GraphAnalyzer(root, following_map, follower_map)

        self.assertEqual(len(analyzer.l1_followers), 130)
        self.assertEqual(len(analyzer.l1_followings), 120)
        self.assertEqual(len(analyzer.get_mutuals()), 70)
        self.assertEqual(len(analyzer.get_fans()), 60)
        self.assertEqual(len(analyzer.get_traitors()), 50)
        self.assertGreater(
            len(following_map["amigo_001"].union(follower_map["amigo_001"])),
            1,
        )

    def test_large_graph_is_balanced_and_visually_limited(self) -> None:
        root = "owner"
        following = {f"profile_{index:04d}" for index in range(700)}
        followers = {f"profile_{index:04d}" for index in range(300, 1000)}
        analyzer = GraphAnalyzer(root, {root: following}, {root: followers})

        graph = analyzer.get_base_graph()
        visible_relations = {node.metadata.get("relation") for node in graph.nodes}

        self.assertEqual(len(graph.nodes), MAX_GRAPH_PROFILES + 1)
        self.assertEqual(graph.metadata["total_nodes"], 1001)
        self.assertTrue(graph.metadata["truncated"])
        self.assertEqual(
            visible_relations,
            {"root", "mutual", "follower_only", "following_only"},
        )


if __name__ == "__main__":
    unittest.main()
