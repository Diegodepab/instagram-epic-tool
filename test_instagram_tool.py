"""
Unit tests for Instagram Epic Tool components.
"""
import unittest
from analyzer import FollowerAnalyzer
from visualizer import NetworkVisualizer


class MockUser:
    """Mock user object for testing."""
    def __init__(self, user_id, username, full_name):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name


class TestFollowerAnalyzer(unittest.TestCase):
    """Test cases for FollowerAnalyzer."""
    
    def setUp(self):
        """Set up test data."""
        # Create mock followers
        self.followers = {
            '1': MockUser('1', 'alice', 'Alice Smith'),
            '2': MockUser('2', 'bob', 'Bob Jones'),
            '3': MockUser('3', 'charlie', 'Charlie Brown'),
        }
        
        # Create mock following
        self.following = {
            '2': MockUser('2', 'bob', 'Bob Jones'),
            '3': MockUser('3', 'charlie', 'Charlie Brown'),
            '4': MockUser('4', 'david', 'David Wilson'),
        }
        
        self.analyzer = FollowerAnalyzer(self.followers, self.following)
    
    def test_get_unfollowers(self):
        """Test unfollowers detection."""
        unfollowers = self.analyzer.get_unfollowers()
        self.assertEqual(len(unfollowers), 1)
        self.assertIn('4', unfollowers)
        self.assertEqual(unfollowers['4'].username, 'david')
    
    def test_get_fans(self):
        """Test fans detection."""
        fans = self.analyzer.get_fans()
        self.assertEqual(len(fans), 1)
        self.assertIn('1', fans)
        self.assertEqual(fans['1'].username, 'alice')
    
    def test_get_mutual_followers(self):
        """Test mutual followers detection."""
        mutual = self.analyzer.get_mutual_followers()
        self.assertEqual(len(mutual), 2)
        self.assertIn('2', mutual)
        self.assertIn('3', mutual)
    
    def test_get_summary(self):
        """Test summary statistics."""
        summary = self.analyzer.get_summary()
        self.assertEqual(summary['total_followers'], 3)
        self.assertEqual(summary['total_following'], 3)
        self.assertEqual(summary['mutual_followers'], 2)
        self.assertEqual(summary['unfollowers'], 1)
        self.assertEqual(summary['fans'], 1)


class TestNetworkVisualizer(unittest.TestCase):
    """Test cases for NetworkVisualizer."""
    
    def setUp(self):
        """Set up test data."""
        self.visualizer = NetworkVisualizer('testuser')
        
        self.followers = {
            '1': MockUser('1', 'alice', 'Alice Smith'),
            '2': MockUser('2', 'bob', 'Bob Jones'),
        }
        
        self.following = {
            '2': MockUser('2', 'bob', 'Bob Jones'),
            '3': MockUser('3', 'charlie', 'Charlie Brown'),
        }
    
    def test_graph_creation(self):
        """Test graph creation."""
        self.visualizer.add_followers_and_following(self.followers, self.following)
        
        # Check nodes
        self.assertIn('testuser', self.visualizer.graph.nodes)
        self.assertIn('alice', self.visualizer.graph.nodes)
        self.assertIn('bob', self.visualizer.graph.nodes)
        self.assertIn('charlie', self.visualizer.graph.nodes)
        
        # Check node types
        self.assertEqual(self.visualizer.graph.nodes['testuser']['node_type'], 'user')
        self.assertEqual(self.visualizer.graph.nodes['bob']['node_type'], 'mutual')
        self.assertEqual(self.visualizer.graph.nodes['alice']['node_type'], 'follower')
        self.assertEqual(self.visualizer.graph.nodes['charlie']['node_type'], 'following')
    
    def test_graph_statistics(self):
        """Test graph statistics."""
        self.visualizer.add_followers_and_following(self.followers, self.following)
        stats = self.visualizer.get_statistics()
        
        self.assertEqual(stats['total_nodes'], 4)
        self.assertEqual(stats['total_edges'], 4)
        self.assertTrue('density' in stats)
        self.assertTrue('is_connected' in stats)


if __name__ == '__main__':
    unittest.main()
