"""
Module for analyzing Instagram followers and following.
"""
from typing import Dict, Set, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FollowerAnalyzer:
    """Analyze followers and following relationships."""
    
    def __init__(self, followers: Dict[str, Dict], following: Dict[str, Dict]):
        """
        Initialize analyzer with followers and following data.
        
        Args:
            followers: Dict of followers (user_id -> user_info)
            following: Dict of following (user_id -> user_info)
        """
        self.followers = followers
        self.following = following
        
    def get_unfollowers(self) -> Dict[str, Dict]:
        """
        Get users you follow who don't follow you back.
        
        Returns:
            Dict of users who don't follow back
        """
        follower_ids = set(self.followers.keys())
        following_ids = set(self.following.keys())
        
        unfollower_ids = following_ids - follower_ids
        unfollowers = {uid: self.following[uid] for uid in unfollower_ids}
        
        logger.info(f"Found {len(unfollowers)} users who don't follow back")
        return unfollowers
    
    def get_fans(self) -> Dict[str, Dict]:
        """
        Get users who follow you but you don't follow back.
        
        Returns:
            Dict of fans
        """
        follower_ids = set(self.followers.keys())
        following_ids = set(self.following.keys())
        
        fan_ids = follower_ids - following_ids
        fans = {uid: self.followers[uid] for uid in fan_ids}
        
        logger.info(f"Found {len(fans)} fans (followers you don't follow back)")
        return fans
    
    def get_mutual_followers(self) -> Dict[str, Dict]:
        """
        Get users who follow you and you follow back.
        
        Returns:
            Dict of mutual followers
        """
        follower_ids = set(self.followers.keys())
        following_ids = set(self.following.keys())
        
        mutual_ids = follower_ids & following_ids
        mutual = {uid: self.followers[uid] for uid in mutual_ids}
        
        logger.info(f"Found {len(mutual)} mutual followers")
        return mutual
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics.
        
        Returns:
            Dict with summary statistics
        """
        unfollowers = self.get_unfollowers()
        fans = self.get_fans()
        mutual = self.get_mutual_followers()
        
        return {
            'total_followers': len(self.followers),
            'total_following': len(self.following),
            'unfollowers': len(unfollowers),
            'fans': len(fans),
            'mutual_followers': len(mutual)
        }
