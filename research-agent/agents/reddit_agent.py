import re
import requests
from typing import Dict, Any, List
from datetime import datetime

from openai import OpenAI
import config
from agents.base_agent import BaseAgent

# クエリに関連する優先Subreddit（幅広くカバー）
SUBREDDITS = [
    "artificial", "ChatGPT", "MachineLearning", "technology",
    "singularity", "OpenAI", "business", "entrepreneur",
    "restaurant", "foodtech", "Futurology",
]


class RedditAgent(BaseAgent):
    """Research agent using Reddit's public JSON API (no auth required)."""

    def __init__(self):
        super().__init__("reddit")
        self.base_url = "https://www.reddit.com/search.json"
        self.headers = {"User-Agent": "ResearchHub/1.0 (personal research tool)"}
        self.openai = OpenAI(api_key=config.OPENAI_API_KEY)

    def research(self, query: str) -> Dict[str, Any]:
        start_time = datetime.now()
        try:
            # 日本語クエリを複数の英語クエリに変換
            en_queries = self._to_english_variants(query) if self._has_japanese(query) else [query]

            # 複数クエリで検索してマージ
            all_posts: List[Dict] = []
            seen_urls = set()

            for eq in en_queries:
                results = self._search_reddit(eq, limit=8)
                for p in results:
                    if p["url"] not in seen_urls:
                        seen_urls.add(p["url"])
                        all_posts.append(p)
                if len(all_posts) >= 8:
                    break

            # 結果が少ない場合はSubredditを直接検索
            if len(all_posts) < 4 and en_queries:
                main_kw = en_queries[0]
                sub_results = self._search_in_subreddits(main_kw)
                for p in sub_results:
                    if p["url"] not in seen_urls:
                        seen_urls.add(p["url"])
                        all_posts.append(p)

            # スコア順にソートして上位10件
            all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
            final_posts = all_posts[:10]

            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "source": self.name,
                "status": "success",
                "data": {
                    "posts": final_posts,
                    "total_found": len(final_posts),
                    "en_queries": en_queries,
                },
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "source": self.name,
                "status": "error",
                "data": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
            }

    def _has_japanese(self, text: str) -> bool:
        return bool(re.search(r'[぀-鿿]', text))

    def _to_english_variants(self, query: str) -> List[str]:
        """日本語クエリを3パターンの英語キーワードに変換（短いキーワード形式）"""
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Convert this Japanese query into 3 short English keyword phrases (2-5 words each) "
                        f"for Reddit search. Go from specific to broad. "
                        f"Output ONLY the keywords, one per line, no questions, no explanation:\n「{query}」\n\n"
                        f"Example output for 「飲食店 AI活用」:\n"
                        f"restaurant AI automation\n"
                        f"AI food service technology\n"
                        f"generative AI restaurant industry"
                    )
                }],
                max_tokens=50,
                temperature=0.2,
            )
            lines = resp.choices[0].message.content.strip().split("\n")
            variants = [l.strip().strip('"').strip("・-") for l in lines if l.strip()][:3]
            return variants if variants else [query]
        except Exception:
            return [query]

    def _search_reddit(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """全Reddit横断検索"""
        try:
            params = {"q": query, "sort": "relevance", "limit": limit, "type": "link"}
            response = requests.get(
                self.base_url, params=params,
                headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            return self._parse_posts(response.json())
        except Exception:
            return []

    def _search_in_subreddits(self, query: str) -> List[Dict[str, Any]]:
        """関連Subredditを直接検索"""
        posts = []
        seen = set()
        for sr in SUBREDDITS[:6]:  # 上位6つのSubredditを試す
            try:
                url = f"https://www.reddit.com/r/{sr}/search.json"
                params = {"q": query, "restrict_sr": "1", "sort": "relevance", "limit": 5}
                r = requests.get(url, params=params, headers=self.headers, timeout=8)
                r.raise_for_status()
                for p in self._parse_posts(r.json()):
                    if p["url"] not in seen:
                        seen.add(p["url"])
                        posts.append(p)
                if len(posts) >= 8:
                    break
            except Exception:
                continue
        return posts

    def _parse_posts(self, data: dict) -> List[Dict[str, Any]]:
        posts = []
        for item in data.get("data", {}).get("children", []):
            post = item.get("data", {})
            posts.append({
                "title":        post.get("title", ""),
                "url":          f"https://www.reddit.com{post.get('permalink', '')}",
                "subreddit":    post.get("subreddit_name_prefixed", ""),
                "score":        post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "selftext":     post.get("selftext", "")[:200],
                "created_utc":  post.get("created_utc", 0),
            })
        return posts
