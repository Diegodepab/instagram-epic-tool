"""
Main CLI interface for Instagram Epic Tool.
"""
import os
import argparse
import json
from dotenv import load_dotenv
from instagram_client import InstagramClient
from analyzer import FollowerAnalyzer
from visualizer import NetworkVisualizer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_credentials():
    """Load Instagram credentials from environment or config file."""
    # Try to load from .env file
    load_dotenv('config.env')
    
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')
    
    if not username or not password:
        logger.error("Instagram credentials not found!")
        logger.error("Please create a config.env file with INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")
        return None, None
    
    return username, password


def save_user_list(users: dict, filename: str):
    """Save user list to JSON file."""
    user_list = []
    for user_id, user_info in users.items():
        user_list.append({
            'user_id': user_id,
            'username': user_info.username if hasattr(user_info, 'username') else 'unknown',
            'full_name': user_info.full_name if hasattr(user_info, 'full_name') else 'unknown'
        })
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(user_list, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(user_list)} users to {filename}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Instagram Epic Tool - Analyze and visualize your Instagram network',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --visualize                    # Create network graph visualization
  python main.py --analyze                      # Analyze followers and following
  python main.py --unfollowers                  # Show users who don't follow back
  python main.py --visualize --analyze          # Do both visualization and analysis
        """
    )
    
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='Create network graph visualization')
    parser.add_argument('--analyze', '-a', action='store_true',
                       help='Analyze followers and following relationships')
    parser.add_argument('--unfollowers', '-u', action='store_true',
                       help='Show users who don\'t follow you back')
    parser.add_argument('--fans', '-f', action='store_true',
                       help='Show users who follow you but you don\'t follow back')
    parser.add_argument('--mutual', '-m', action='store_true',
                       help='Show mutual followers')
    parser.add_argument('--output', '-o', default='instagram_network.png',
                       help='Output file for visualization (default: instagram_network.png)')
    parser.add_argument('--save-data', '-s', action='store_true',
                       help='Save follower/following data to JSON files')
    
    args = parser.parse_args()
    
    # If no action specified, show help
    if not any([args.visualize, args.analyze, args.unfollowers, args.fans, args.mutual]):
        parser.print_help()
        return
    
    # Load credentials
    username, password = load_credentials()
    if not username or not password:
        return
    
    # Initialize client and login
    client = InstagramClient(username, password)
    if not client.login():
        return
    
    # Fetch data
    logger.info("Fetching followers and following data...")
    followers = client.get_followers()
    following = client.get_following()
    
    if not followers and not following:
        logger.error("Failed to fetch data from Instagram")
        return
    
    # Save raw data if requested
    if args.save_data:
        save_user_list(followers, 'followers.json')
        save_user_list(following, 'following.json')
    
    # Create analyzer
    analyzer = FollowerAnalyzer(followers, following)
    
    # Analysis
    if args.analyze or args.unfollowers or args.fans or args.mutual:
        logger.info("\n" + "="*60)
        logger.info("INSTAGRAM NETWORK ANALYSIS")
        logger.info("="*60)
        
        summary = analyzer.get_summary()
        logger.info(f"\nTotal Followers: {summary['total_followers']}")
        logger.info(f"Total Following: {summary['total_following']}")
        logger.info(f"Mutual Followers: {summary['mutual_followers']}")
        logger.info(f"Fans (follow you but you don't follow back): {summary['fans']}")
        logger.info(f"Unfollowers (you follow but they don't follow back): {summary['unfollowers']}")
        
        if args.unfollowers:
            unfollowers = analyzer.get_unfollowers()
            logger.info("\n" + "-"*60)
            logger.info("USERS WHO DON'T FOLLOW YOU BACK:")
            logger.info("-"*60)
            for user_id, user_info in list(unfollowers.items())[:20]:  # Show first 20
                username = user_info.username if hasattr(user_info, 'username') else 'unknown'
                full_name = user_info.full_name if hasattr(user_info, 'full_name') else 'unknown'
                logger.info(f"  @{username} - {full_name}")
            if len(unfollowers) > 20:
                logger.info(f"  ... and {len(unfollowers) - 20} more")
            
            if args.save_data:
                save_user_list(unfollowers, 'unfollowers.json')
        
        if args.fans:
            fans = analyzer.get_fans()
            logger.info("\n" + "-"*60)
            logger.info("FANS (Followers you don't follow back):")
            logger.info("-"*60)
            for user_id, user_info in list(fans.items())[:20]:  # Show first 20
                username = user_info.username if hasattr(user_info, 'username') else 'unknown'
                full_name = user_info.full_name if hasattr(user_info, 'full_name') else 'unknown'
                logger.info(f"  @{username} - {full_name}")
            if len(fans) > 20:
                logger.info(f"  ... and {len(fans) - 20} more")
            
            if args.save_data:
                save_user_list(fans, 'fans.json')
        
        if args.mutual:
            mutual = analyzer.get_mutual_followers()
            logger.info("\n" + "-"*60)
            logger.info("MUTUAL FOLLOWERS:")
            logger.info("-"*60)
            for user_id, user_info in list(mutual.items())[:20]:  # Show first 20
                username = user_info.username if hasattr(user_info, 'username') else 'unknown'
                full_name = user_info.full_name if hasattr(user_info, 'full_name') else 'unknown'
                logger.info(f"  @{username} - {full_name}")
            if len(mutual) > 20:
                logger.info(f"  ... and {len(mutual) - 20} more")
            
            if args.save_data:
                save_user_list(mutual, 'mutual_followers.json')
    
    # Visualization
    if args.visualize:
        logger.info("\n" + "="*60)
        logger.info("CREATING NETWORK VISUALIZATION")
        logger.info("="*60)
        
        visualizer = NetworkVisualizer(username)
        visualizer.add_followers_and_following(followers, following)
        
        stats = visualizer.get_statistics()
        logger.info(f"\nGraph Statistics:")
        logger.info(f"  Nodes: {stats['total_nodes']}")
        logger.info(f"  Edges: {stats['total_edges']}")
        logger.info(f"  Density: {stats['density']:.4f}")
        
        visualizer.visualize(output_file=args.output)
        logger.info(f"\nVisualization saved to: {args.output}")
    
    logger.info("\n" + "="*60)
    logger.info("DONE!")
    logger.info("="*60)


if __name__ == '__main__':
    main()
