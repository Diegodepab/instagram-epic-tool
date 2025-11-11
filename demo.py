"""
Example demonstration of Instagram Epic Tool functionality.
This creates a mock network for demonstration purposes.
"""
import networkx as nx
import matplotlib.pyplot as plt


def create_demo_visualization():
    """Create a demo network visualization without requiring Instagram credentials."""
    print("Creating demo Instagram network visualization...")
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add central user node
    central_user = "your_username"
    G.add_node(central_user, node_type='user', color='red')
    
    # Add some mock followers (people who follow you)
    followers = ['alice', 'bob', 'charlie', 'david', 'emma']
    for follower in followers:
        G.add_node(follower, node_type='follower', color='lightblue')
        G.add_edge(follower, central_user)
    
    # Add some mock following (people you follow)
    following = ['frank', 'grace', 'henry', 'isabel']
    for follow in following:
        G.add_node(follow, node_type='following', color='lightyellow')
        G.add_edge(central_user, follow)
    
    # Add some mutual followers
    mutual = ['alice', 'bob', 'charlie']
    for mutual_user in mutual:
        if mutual_user in followers:
            G.nodes[mutual_user]['color'] = 'lightgreen'
            G.nodes[mutual_user]['node_type'] = 'mutual'
            G.add_edge(central_user, mutual_user)
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Get node colors
    colors = [G.nodes[node].get('color', 'gray') for node in G.nodes()]
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    
    # Draw the graph
    nx.draw(G, pos, 
           node_color=colors,
           node_size=800,
           with_labels=True,
           arrows=True,
           arrowsize=20,
           edge_color='gray',
           alpha=0.7,
           font_size=10,
           font_weight='bold',
           ax=ax)
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='red', markersize=15, label='You'),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='lightgreen', markersize=15, 
                  label='Mutual Followers'),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='lightblue', markersize=15, 
                  label='Followers'),
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor='lightyellow', markersize=15, 
                  label='Following')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    plt.title(f"Demo Instagram Network for @{central_user}", 
             fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    
    # Save the demo visualization
    output_file = 'demo_instagram_network.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Demo visualization saved to {output_file}")
    
    # Print statistics
    print("\nDemo Network Statistics:")
    print(f"  Total nodes: {G.number_of_nodes()}")
    print(f"  Total edges: {G.number_of_edges()}")
    print(f"  Followers: {len([n for n, d in G.nodes(data=True) if d.get('node_type') in ['follower', 'mutual']])}")
    print(f"  Following: {len([n for n, d in G.nodes(data=True) if d.get('node_type') in ['following', 'mutual']])}")
    print(f"  Mutual: {len([n for n, d in G.nodes(data=True) if d.get('node_type') == 'mutual'])}")
    
    # Print analysis
    print("\nDemo Analysis:")
    print("  Unfollowers (you follow but they don't follow back):")
    for user in following:
        if user not in mutual:
            print(f"    - @{user}")
    
    print("\n  Fans (they follow you but you don't follow back):")
    for user in followers:
        if user not in mutual:
            print(f"    - @{user}")


if __name__ == '__main__':
    create_demo_visualization()
