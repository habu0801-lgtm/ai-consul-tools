import requests
from typing import Dict, Any
from urllib.parse import quote
from datetime import datetime

from agents.base_agent import BaseAgent


class WikipediaAgent(BaseAgent):
    """Research agent for Wikipedia articles about food industry and AI."""

    def __init__(self):
        super().__init__("wikipedia")
        self.base_url = "https://ja.wikipedia.org/w/api.php"
        self.headers = {
            "User-Agent": "RestaurantAI-Research/1.0 (habu0801@gmail.com)"
        }

    def research(self, query: str) -> Dict[str, Any]:
        """
        Search Wikipedia for food industry and AI-related articles.

        Args:
            query: Search query

        Returns:
            Standardized response dict
        """
        start_time = datetime.now()

        try:
            # クエリから検索用キーワードを抽出（助詞・副詞を除去して短くする）
            search_term = self._extract_search_term(query)
            articles = self._search_wikipedia(search_term)

            # Remove duplicates
            unique_articles = {a["url"]: a for a in articles}.values()
            articles = list(unique_articles)[:10]

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "source": self.name,
                "status": "success",
                "data": {
                    "articles": articles,
                    "total_found": len(articles),
                    "search_queries": 1
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

    def _extract_search_term(self, query: str) -> str:
        """クエリから余分な語を除いて短い検索ワードを作る"""
        # 除去する語（日本語の助詞・副詞・汎用語）
        stop_words = [
            "について", "に関して", "の", "最新", "情報", "事例", "次回", "発売",
            "活用", "について", "方法", "やり方", "とは", "一覧", "まとめ",
            "調査", "してください", "教えて", "を", "は", "が", "で", "に",
        ]
        term = query
        for w in stop_words:
            term = term.replace(w, " ")
        # 連続スペースを1つに
        import re
        term = re.sub(r"\s+", " ", term).strip()
        # 長すぎる場合は先頭の重要そうな部分だけ使う
        words = term.split()
        return " ".join(words[:3]) if words else query

    def _search_wikipedia(self, query: str) -> list:
        """
        Search Wikipedia for articles matching the query.

        Args:
            query: Search query string

        Returns:
            List of article dicts with title, url, sections
        """
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srprop": "timestamp",
                "srlimit": 5,
                "format": "json"
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            articles = []
            search_results = data.get("query", {}).get("search", [])

            for result in search_results:
                article_title = result["title"]
                article_url = f"https://ja.wikipedia.org/wiki/{quote(article_title)}"

                # Get sections for each article
                sections = self._get_article_sections(article_title)

                articles.append({
                    "title": article_title,
                    "url": article_url,
                    "sections": sections,
                    "snippet": result.get("snippet", "")[:200]
                })

            return articles

        except Exception as e:
            return []

    def _get_article_sections(self, article_title: str) -> list:
        """Get the main sections of an article."""
        try:
            params = {
                "action": "query",
                "titles": article_title,
                "prop": "sections",
                "format": "json"
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                sections = page.get("sections", [])
                # Extract section titles (level 2 headings)
                return [s["line"] for s in sections if s.get("level") == "2"][:5]

            return []

        except Exception as e:
            return []
