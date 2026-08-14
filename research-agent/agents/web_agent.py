import logging
import re
from typing import Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# スクレイピングをスキップするドメイン（ログイン必須・JS依存など）
SKIP_DOMAINS = {
    "twitter.com", "x.com", "facebook.com", "instagram.com",
    "linkedin.com", "tiktok.com", "youtube.com",
    "amazon.co.jp", "amazon.com", "rakuten.co.jp",
    "pdf", ".pdf"
}

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


class WebAgent(BaseAgent):
    """Web記事の検索＋本文全文取得エージェント（DuckDuckGo + BeautifulSoup）"""

    def __init__(self):
        super().__init__("web")

    def research(self, query: str) -> Dict[str, Any]:
        start_time = datetime.now()
        try:
            articles = self._search_duckduckgo(query)
            # 上位3件だけ本文を全文取得（速度とのバランス）
            for i, article in enumerate(articles[:3]):
                full_text = self._scrape_full_text(article["url"])
                articles[i]["full_text"] = full_text

            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "source": self.name,
                "status": "success",
                "data": {"articles": articles, "total_found": len(articles)},
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"WebAgent error: {e}")
            return {
                "source": self.name,
                "status": "error",
                "data": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time
            }

    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """DuckDuckGo で検索（APIキー不要）"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query, max_results=10,
                    region="jp-ja", safesearch="moderate"
                ))
            articles = []
            for item in results:
                articles.append({
                    "title":     item.get("title", ""),
                    "url":       item.get("href", ""),
                    "summary":   item.get("body", ""),
                    "site":      self._extract_domain(item.get("href", "")),
                    "published": None,
                    "full_text": ""   # 後で埋める
                })
            logger.info(f"DuckDuckGo: {len(articles)} results for '{query}'")
            return articles
        except Exception as e:
            logger.error(f"DuckDuckGo error: {e}")
            return []

    def _scrape_full_text(self, url: str, max_chars: int = 2000) -> str:
        """記事URLから本文テキストを抽出する"""
        try:
            # スキップ対象チェック
            domain = self._extract_domain(url)
            if any(s in domain or s in url for s in SKIP_DOMAINS):
                return ""

            resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=8, allow_redirects=True)
            resp.raise_for_status()

            # 文字コード対応
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            # 不要タグを除去
            for tag in soup(["script", "style", "nav", "header", "footer",
                              "aside", "form", "noscript", "iframe", "ads"]):
                tag.decompose()

            # 記事本文の抽出（優先順: article > main > .content系 > body）
            body = (
                soup.find("article") or
                soup.find("main") or
                soup.find(class_=re.compile(r"article|content|post|entry|body", re.I)) or
                soup.find("body")
            )

            if not body:
                return ""

            # <p>タグのテキストを連結
            paragraphs = [p.get_text(strip=True) for p in body.find_all("p") if len(p.get_text(strip=True)) > 30]
            text = "\n".join(paragraphs)

            # 連続空白を整理して文字数制限
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text[:max_chars]

        except Exception as e:
            logger.debug(f"Scrape failed ({url}): {e}")
            return ""

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            return urlparse(url).netloc.replace("www.", "")
        except Exception:
            return "Unknown"
