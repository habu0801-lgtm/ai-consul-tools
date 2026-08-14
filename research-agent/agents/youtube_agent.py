import requests
from typing import Dict, Any, List
from datetime import datetime

import config
from agents.base_agent import BaseAgent


class YouTubeAgent(BaseAgent):
    """Research agent for YouTube videos about food industry and AI."""

    def __init__(self):
        super().__init__("youtube")
        self.api_key = config.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3/search"

    def research(self, query: str) -> Dict[str, Any]:
        """
        Search YouTube for videos about food industry and AI.

        Args:
            query: Search query

        Returns:
            Standardized response dict
        """
        start_time = datetime.now()

        try:
            if not self.api_key:
                return {
                    "source": self.name,
                    "status": "error",
                    "data": {},
                    "error": "YouTube API key not configured",
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": 0
                }

            videos = self._search_youtube(query)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "source": self.name,
                "status": "success",
                "data": {
                    "videos": videos,
                    "total_found": len(videos)
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

    def _search_youtube(self, query: str) -> List[Dict[str, Any]]:
        """
        Search YouTube API for relevant videos.

        Args:
            query: Search query

        Returns:
            List of video dicts
        """
        try:
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 10,
                "order": "relevance",
                "regionCode": "JP",
                "key": self.api_key
            }

            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")

                if video_id:
                    video_info = self._get_video_statistics(video_id)

                    videos.append({
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "video_id": video_id,
                        "description": snippet.get("description", "")[:200],
                        "published": snippet.get("publishedAt", ""),
                        "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                        "views": video_info.get("views", 0),
                        "likes": video_info.get("likes", 0)
                    })

            return videos

        except Exception as e:
            return []

    def _get_video_statistics(self, video_id: str) -> Dict[str, Any]:
        """
        Get view and like statistics for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with views and likes (note: likes may not be accessible)
        """
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "statistics",
                "id": video_id,
                "key": self.api_key
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            stats = data.get("items", [{}])[0].get("statistics", {})

            return {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)) if "likeCount" in stats else 0,
                "comments": int(stats.get("commentCount", 0))
            }

        except Exception as e:
            return {"views": 0, "likes": 0, "comments": 0}
