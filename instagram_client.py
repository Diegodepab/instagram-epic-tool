"""
Instagram client module for authentication and data fetching.
"""
import os
from typing import List, Dict, Set
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InstagramClient:
    """Client for interacting with Instagram API."""
    
    def __init__(self, username: str, password: str):
        """
        Initialize Instagram client.
        
        Args:
            username: Instagram username
            password: Instagram password
        """
        self.username = username
        self.password = password
        self.client = Client()
        self.user_id = None
        
    def login(self) -> bool:
        """
        Login to Instagram.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info(f"Logging in as {self.username}...")
            self.client.login(self.username, self.password)
            self.user_id = self.client.user_id
            logger.info("Login successful!")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def get_followers(self, user_id: str = None) -> Dict[str, Dict]:
        """
        Get followers for a user.
        
        Args:
            user_id: User ID to fetch followers for (defaults to authenticated user)
            
        Returns:
            Dict mapping user_id to user info
        """
        try:
            if user_id is None:
                user_id = self.user_id
            
            logger.info(f"Fetching followers for user {user_id}...")
            followers = self.client.user_followers(user_id)
            logger.info(f"Found {len(followers)} followers")
            return followers
        except Exception as e:
            logger.error(f"Error fetching followers: {str(e)}")
            return {}
    
    def get_following(self, user_id: str = None) -> Dict[str, Dict]:
        """
        Get users that a user is following.
        
        Args:
            user_id: User ID to fetch following for (defaults to authenticated user)
            
        Returns:
            Dict mapping user_id to user info
        """
        try:
            if user_id is None:
                user_id = self.user_id
            
            logger.info(f"Fetching following for user {user_id}...")
            following = self.client.user_following(user_id)
            logger.info(f"Following {len(following)} users")
            return following
        except Exception as e:
            logger.error(f"Error fetching following: {str(e)}")
            return {}
    
    def get_user_info(self, username: str) -> Dict:
        """
        Get user information by username.
        
        Args:
            username: Instagram username
            
        Returns:
            Dict with user information
        """
        try:
            user_info = self.client.user_info_by_username(username)
            return user_info.dict()
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            return {}
