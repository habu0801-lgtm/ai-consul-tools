import requests
from typing import Dict, Any, List
from datetime import datetime

import config
from agents.base_agent import BaseAgent


class SNSAgent(BaseAgent):
    """Research agent for SNS posts about food industry and AI."""

    def __init__(self):
        super().__init__("sns")
        self.twitter_token = config.TWITTER_BEARER_TOKEN
        self.instagram_token = config.INSTAGRAM_ACCESS_TOKEN
        self.tiktok_key = config.TIKTOK_CLIENT_KEY

    def research(self, query: str) -> Dict[str, Any]:
        """
        Search SNS platforms for posts about food industry and AI.

        Args:
            query: Search query

        Returns:
            Standardized response dict
        """
        start_time = datetime.now()

        try:
            platforms_data = {}

            # Search Twitter
            if self.twitter_token:
                twitter_posts = self._search_twitter(query)
                platforms_data["twitter"] = twitter_posts
            else:
                platforms_data["twitter"] = []

            # Search Instagram
            if self.instagram_token:
                instagram_posts = self._search_instagram(query)
                platforms_data["instagram"] = instagram_posts
            else:
                platforms_data["instagram"] = []

            # TikTok search (limited without API key)
            platforms_data["tiktok"] = []

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "source": self.name,
                "status": "success",
                "data": {
                    "platforms": platforms_data,
                    "total_posts": sum(len(posts) for posts in platforms_data.values())
                },
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "source": self.name,
                "status": "error",
                "data": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time
            }

    def _search_twitter(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Twitter API v2 for recent posts.

        Args:
            query: Search query

        Returns:
            List of tweet dicts
        """
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                "Authorization": f"Bearer {self.twitter_token}",
                "User-Agent": "RestaurantAI-Research/1.0"
            }

            params = {
                "query": f"{query} lang:ja -is:retweet",
                "max_results": 10,
                "tweet.fields": "public_metrics,created_at",
                "expansions": "author_id"
            }

            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            tweets = []
            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                tweets.append({
                    "text": tweet.get("text", "")[:200],
                    "engagement": metrics.get("like_count", 0) + metrics.get("retweet_count", 0),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "created_at": tweet.get("created_at", ""),
                    "url": f"https://twitter.com/i/web/status/{tweet.get('id', '')}"
                })

            return tweets

        except Exception as e:
            return []

    def _search_instagram(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Instagram Graph API for posts.

        Args:
            query: Search query

        Returns:
            List of Instagram post dicts
        """
        try:
            # Instagram Graph API requires hashtag ID first
            url = f"https://graph.instagram.com/ig_hashtag_search"
            params = {
                "user_id": config.INSTAGRAM_APP_ID,
                "fields": "id,name",
                "access_token": self.instagram_token
            }

            # Note: This is a simplified implementation
            # Full implementation would require more complex OAuth flow

            return []

        except Exception as e:
            return []

    def _search_tiktok(self, query: str) -> List[Dict[str, Any]]:
        """
        Search TikTok for videos.

        Args:
            query: Search query

        Returns:
            List of TikTok video dicts
        """
        # TikTok API requires OAuth and approval process
        # This is a placeholder for future implementation
        return []
