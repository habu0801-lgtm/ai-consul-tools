#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import config
from utils import setup_logger, log_json
from agents.wikipedia_agent import WikipediaAgent
from agents.web_agent import WebAgent
from agents.youtube_agent import YouTubeAgent
from agents.sns_agent import SNSAgent

logger = setup_logger(__name__)


def validate_env():
    """Validate that required environment variables are set (optional - Wikipedia works without API keys)."""
    # Note: All agents can work without API keys
    # Wikipedia requires no API key
    # Web, YouTube, SNS agents can work with limited functionality
    pass


def aggregate_results(results: list, query: str, execution_time: float) -> dict:
    """Aggregate results from multiple agents into a single report."""
    aggregated = {
        "metadata": {
            "query": query,
            "research_date": datetime.now().isoformat(),
            "total_sources": 4,
            "execution_time_seconds": execution_time,
            "agents_status": {}
        },
        "findings": {}
    }

    for result in results:
        source = result.get("source", "unknown")
        status = result.get("status", "error")
        aggregated["metadata"]["agents_status"][source] = status
        aggregated["findings"][source] = result

    return aggregated


def generate_markdown_report(aggregated: dict) -> str:
    """Generate Markdown report from aggregated results."""
    query = aggregated["metadata"]["query"]
    research_date = aggregated["metadata"]["research_date"]

    report = f"""# 飲食店のAI活用事例 調査レポート

**調査日時**: {research_date}
**調査キーワード**: {query}

---

## 📋 調査概要

- **総情報源数**: 4
- **実行時間**: {aggregated["metadata"]["execution_time_seconds"]:.1f}秒

### 各情報源の状態
"""

    for source, status in aggregated["metadata"]["agents_status"].items():
        status_emoji = "✅" if status == "success" else "❌"
        report += f"- {status_emoji} {source}: {status}\n"

    report += "\n---\n\n"

    # Add findings from each source
    for source, result in aggregated["findings"].items():
        report += f"## {source.upper()}\n\n"

        if result.get("status") == "error":
            report += f"⚠️ **エラー**: {result.get('error', 'Unknown error')}\n\n"
        else:
            data = result.get("data", {})
            report += _format_source_data(source, data)

    report += "\n---\n"
    report += f"*レポート生成: {datetime.now().isoformat()}*\n"

    return report


def _format_source_data(source: str, data: dict) -> str:
    """Format source-specific data for the report."""
    if source == "wikipedia":
        articles = data.get("articles", [])
        if not articles:
            return "情報が見つかりませんでした。\n\n"

        output = ""
        for article in articles[:5]:
            output += f"### {article.get('title', 'No title')}\n"
            output += f"- **URL**: {article.get('url', 'N/A')}\n"
            if article.get("sections"):
                output += f"- **関連セクション**: {', '.join(article['sections'])}\n"
            output += "\n"
        return output

    elif source == "web":
        articles = data.get("articles", [])
        if not articles:
            return "情報が見つかりませんでした。\n\n"

        output = ""
        for article in articles[:5]:
            output += f"### {article.get('title', 'No title')}\n"
            output += f"- **サイト**: {article.get('site', 'N/A')}\n"
            output += f"- **URL**: {article.get('url', 'N/A')}\n"
            if article.get("published"):
                output += f"- **公開日**: {article['published']}\n"
            output += "\n"
        return output

    elif source == "youtube":
        videos = data.get("videos", [])
        if not videos:
            return "動画が見つかりませんでした。\n\n"

        output = ""
        for video in videos[:5]:
            output += f"### {video.get('title', 'No title')}\n"
            output += f"- **チャンネル**: {video.get('channel', 'N/A')}\n"
            output += f"- **URL**: https://youtube.com/watch?v={video.get('video_id', 'N/A')}\n"
            output += f"- **再生数**: {video.get('views', 'N/A'):,}\n"
            output += f"- **高評価**: {video.get('likes', 'N/A'):,}\n"
            output += "\n"
        return output

    elif source == "sns":
        output = ""
        platforms = data.get("platforms", {})
        for platform, posts in platforms.items():
            output += f"### {platform.upper()}\n"
            for post in posts[:3]:
                output += f"- {post.get('text', 'No text')[:100]}...\n"
                output += f"  - エンゲージメント: {post.get('engagement', 'N/A')}\n"
            output += "\n"
        return output

    return "フォーマット不明です。\n\n"


def run_research(query: str, output_format: str = "markdown") -> dict:
    """
    Run research with all agents in parallel.

    Args:
        query: Search query string
        output_format: "markdown", "json", or "both"

    Returns:
        Aggregated results dictionary
    """
    logger.info(f"Starting research for query: {query}")

    agents = [
        WikipediaAgent(),
        WebAgent(),
        YouTubeAgent(),
        SNSAgent(),
    ]

    results = []
    execution_start = datetime.now()

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_agent = {
            executor.submit(agent.research, query): agent
            for agent in agents
        }

        for future in as_completed(future_to_agent, timeout=config.TOTAL_TIMEOUT_SECONDS):
            agent = future_to_agent[future]
            try:
                result = future.result(timeout=config.TIMEOUT_SECONDS)
                results.append(result)
                logger.info(f"✅ {agent.name} completed successfully")
            except Exception as e:
                logger.error(f"❌ {agent.name} failed: {str(e)}")
                results.append({
                    "source": agent.name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

    execution_time = (datetime.now() - execution_start).total_seconds()
    aggregated = aggregate_results(results, query, execution_time)

    # Save outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format in ["markdown", "both"]:
        markdown_file = output_dir / f"report_{timestamp}.md"
        markdown_content = generate_markdown_report(aggregated)
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"📄 Markdown report saved: {markdown_file}")

    if output_format in ["json", "both"]:
        json_file = output_dir / f"report_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(aggregated, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 JSON report saved: {json_file}")

    return aggregated


def main():
    parser = argparse.ArgumentParser(
        description="飲食店AI活用事例 並列調査エージェント"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="飲食店 AI活用事例",
        help="Search query (default: 飲食店 AI活用事例)"
    )
    parser.add_argument(
        "--output-format",
        choices=["markdown", "json", "both"],
        default="markdown",
        help="Output format (default: markdown)"
    )

    args = parser.parse_args()

    try:
        validate_env()
        result = run_research(args.query, args.output_format)
        logger.info("✨ Research completed successfully")
        return 0
    except KeyboardInterrupt:
        logger.info("Research cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
