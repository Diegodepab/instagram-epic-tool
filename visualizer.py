"""
Module for visualizing Instagram network as a graph.
"""
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class NetworkVisualizer:
    """Create and visualize Instagram network graphs."""
    
    def __init__(self, username: str):
        """
        Initialize visualizer.
        
        Args:
            username: Username of the central user
        """
        self.username = username
        self.graph = nx.DiGraph()
        
    def add_followers_and_following(self, followers: Dict[str, Dict], 
                                    following: Dict[str, Dict]):
        """
        Add followers and following to the graph.
        
        Args:
            followers: Dict of followers (user_id -> user_info)
            following: Dict of following (user_id -> user_info)
        """
        # Add central node (the user)
        self.graph.add_node(self.username, node_type='user', color='red')
        
        # Add followers (edges pointing to user)
        for user_id, user_info in followers.items():
            username = user_info.username if hasattr(user_info, 'username') else str(user_id)
            self.graph.add_node(username, node_type='follower', color='lightblue')
            self.graph.add_edge(username, self.username)
        
        # Add following (edges from user to others)
        for user_id, user_info in following.items():
            username = user_info.username if hasattr(user_info, 'username') else str(user_id)
            
            # If node already exists (mutual follower), update color
            if username in self.graph.nodes:
                self.graph.nodes[username]['color'] = 'lightgreen'
                self.graph.nodes[username]['node_type'] = 'mutual'
            else:
                self.graph.add_node(username, node_type='following', color='lightyellow')
            
            self.graph.add_edge(self.username, username)
        
        logger.info(f"Graph created with {self.graph.number_of_nodes()} nodes "
                   f"and {self.graph.number_of_edges()} edges")
    
    def visualize(self, output_file: str = 'instagram_network.png', 
                  figsize: tuple = (20, 20)):
        """
        Create and save visualization of the network graph.
        
        Args:
            output_file: Path to save the visualization
            figsize: Figure size (width, height)
        """
        logger.info("Creating network visualization...")
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get node colors
        colors = [self.graph.nodes[node].get('color', 'gray') 
                 for node in self.graph.nodes()]
        
        # Use spring layout for positioning
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50, seed=42)
        
        # Draw the graph
        nx.draw(self.graph, pos, 
               node_color=colors,
               node_size=100,
               with_labels=False,
               arrows=True,
               arrowsize=10,
               edge_color='gray',
               alpha=0.6,
               ax=ax)
        
        # Draw the central node with a label
        central_pos = {self.username: pos[self.username]}
        nx.draw_networkx_labels(self.graph, central_pos, 
                               {self.username: self.username},
                               font_size=12, font_weight='bold')
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='red', markersize=10, label='You'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='lightgreen', markersize=10, 
                      label='Mutual Followers'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='lightblue', markersize=10, 
                      label='Followers'),
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor='lightyellow', markersize=10, 
                      label='Following')
        ]
        ax.legend(handles=legend_elements, loc='upper left')
        
        plt.title(f"Instagram Network for @{self.username}", 
                 fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved to {output_file}")
    
    def get_statistics(self) -> Dict:
        """
        Get graph statistics.
        
        Returns:
            Dict with graph statistics
        """
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph)
        }
