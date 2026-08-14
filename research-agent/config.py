import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")

# Execution Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "35"))
TOTAL_TIMEOUT_SECONDS = int(os.getenv("TOTAL_TIMEOUT_SECONDS", "60"))
MAX_RETRIES = 3

# Prompts
GPT_SUMMARY_PROMPT = """
4つの情報源（SNS、Web記事、YouTube動画、Wikipedia）から
飲食店のAI活用事例を調査しました。

以下の形式で最終レポートを生成してください：

## 📊 キーインサイト（Top 3）
- ...

## 🔥 トレンド分析
- ...

## 💡 実例紹介
各情報源から見つかった最も実用的な導入事例：
- ...

## 📚 参考リソース
詳しく知るためのリンク：
- ...

出力はMarkdown形式で、見出しと箇条書きを使用してください。
"""

# API Rate Limits
GOOGLE_SEARCH_RATE_LIMIT = 100  # monthly free tier
YOUTUBE_RATE_LIMIT = 10000  # daily quota
