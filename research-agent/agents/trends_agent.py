import re
import xml.etree.ElementTree as ET
from typing import Dict, Any
from datetime import datetime

import requests
from pytrends.request import TrendReq

from agents.base_agent import BaseAgent

RSS_URL = "https://trends.google.com/trending/rss?geo=JP"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


class TrendsAgent(BaseAgent):
    """Google Trendsでトレンドデータを取得するエージェント（APIキー不要）"""

    def __init__(self):
        super().__init__("trends")

    def research(self, query: str) -> Dict[str, Any]:
        start_time = datetime.now()
        try:
            kw = self._trim_query(query)

            # ① 日本の急上昇トレンドを RSS で取得（安定・高速）
            trending_now = self._fetch_trending_rss()

            # ② pytrends.suggestions() で関連キーワードを取得
            suggestions = self._fetch_suggestions(kw)

            # ③ トレンドと検索クエリの関連度チェック
            related_trends = self._filter_related(trending_now, kw)

            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "source": self.name,
                "status": "success",
                "data": {
                    "keyword":        kw,
                    "trending_now":   trending_now,       # 今日の急上昇トレンド全件
                    "related_trends": related_trends,     # クエリ関連のトレンド
                    "suggestions":    suggestions,        # Googleサジェスト系キーワード
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

    def _fetch_trending_rss(self) -> list:
        """Google Trends RSS から今日の急上昇キーワードを取得"""
        try:
            r = requests.get(RSS_URL, headers=HEADERS, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            items = root.findall("./channel/item")
            results = []
            for item in items[:20]:
                title = item.find("title")
                traffic = item.find("{https://trends.google.com/trending/rss}approx_traffic")
                results.append({
                    "keyword": title.text if title is not None else "",
                    "traffic": traffic.text if traffic is not None else "",
                })
            return results
        except Exception:
            return []

    def _fetch_suggestions(self, keyword: str) -> list:
        """pytrends.suggestions() でGoogleのキーワードサジェストを取得"""
        try:
            pt = TrendReq(hl="ja-JP", tz=540, timeout=(8, 15))
            suggs = pt.suggestions(keyword)
            return [{"title": s.get("title", ""), "type": s.get("type", "")}
                    for s in suggs[:5]]
        except Exception:
            return []

    def _filter_related(self, trending: list, keyword: str) -> list:
        """急上昇トレンドからクエリ関連のものを抽出"""
        kw_words = set(re.split(r"\s+|　", keyword.lower()))
        related = []
        for t in trending:
            kw_text = t.get("keyword", "").lower()
            if any(w in kw_text for w in kw_words if len(w) > 1):
                related.append(t)
        return related

    @staticmethod
    def _trim_query(query: str) -> str:
        """検索キーワードを短く整形"""
        stop = ["について", "に関して", "の", "最新", "情報", "事例", "活用",
                "方法", "とは", "まとめ", "を", "は", "が", "で", "に"]
        term = query
        for w in stop:
            term = term.replace(w, " ")
        term = re.sub(r"\s+", " ", term).strip()
        words = term.split()
        return " ".join(words[:3]) if words else query[:50]
