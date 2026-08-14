#!/usr/bin/env python3
"""
Claude Code / CLIから直接呼ぶ高速リサーチスクリプト
スリープ・アニメーションなし。結果をJSONで outputs/ に保存し、
Claudeが読みやすいテキストサマリーを stdout に出力する。

使い方:
  python research_quick.py "調査クエリ"
"""
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

import config
from agents.web_agent import WebAgent
from agents.youtube_agent import YouTubeAgent
from agents.wikipedia_agent import WikipediaAgent
from agents.reddit_agent import RedditAgent
from agents.trends_agent import TrendsAgent

client = OpenAI(api_key=config.OPENAI_API_KEY)


# ── フォーマットヘルパー ─────────────────────────────────────

def fmt_web(articles):
    if not articles: return "（記事なし）"
    lines = []
    for a in articles[:5]:
        full = a.get("full_text", "")
        body = full[:400] if full else a.get("summary", "")[:150]
        lines.append(f"・{a.get('title','')[:60]}（{a.get('site','')}）\n  {body}")
    return "\n".join(lines)

def fmt_youtube(videos):
    if not videos: return "（動画なし）"
    return "\n".join(
        f"・『{v.get('title','')[:50]}』 {v.get('views',0):,}回 / {v.get('channel','')}"
        for v in videos[:5])

def fmt_wiki(articles):
    if not articles: return "（記事なし）"
    return "\n".join(
        f"・{a.get('title','')}：{a.get('snippet','')[:80]}"
        for a in articles[:4])

def fmt_reddit(posts):
    if not posts: return "（投稿なし）"
    return "\n".join(
        f"・{p.get('title','')[:50]}（{p.get('subreddit','')}）👍{p.get('score',0)}"
        for p in posts[:5])

def fmt_trends(data):
    if not data: return "（データなし）"
    lines = []
    related = data.get("related_trends", [])
    trending = data.get("trending_now", [])
    suggs = data.get("suggestions", [])
    if related:
        lines.append("関連急上昇: " + " / ".join(t["keyword"] for t in related[:3]))
    if trending:
        lines.append("今日の急上昇TOP5: " + " / ".join(t["keyword"] for t in trending[:5]))
    if suggs:
        lines.append("サジェスト: " + " / ".join(s["title"][:20] for s in suggs[:3]))
    return "\n".join(lines) if lines else "（トレンドデータなし）"


# ── サブクエリ生成 ──────────────────────────────────────────

def generate_subqueries(query: str, findings: dict) -> list:
    summary = (
        f"Web: {fmt_web(findings.get('web', []))[:200]}\n"
        f"YouTube: {fmt_youtube(findings.get('youtube', []))[:100]}\n"
        f"Wikipedia: {fmt_wiki(findings.get('wikipedia', []))[:100]}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"""
調査クエリ「{query}」の初回調査結果を読んで、さらに深掘りすべき日本語検索クエリを2〜3個考えてください。

## 初回調査の概要
{summary}

## 条件
- 初回調査で出てきた具体的なキーワードや話題を深掘りする
- 日本語の検索クエリのみ出力
- 1行に1クエリ、番号・記号・説明なし
"""}],
        max_tokens=80,
        temperature=0.7,
    )
    lines = resp.choices[0].message.content.strip().split("\n")
    return [l.strip().lstrip("・-1234567890. 　") for l in lines if l.strip()][:3]


# ── GPT総合インサイト生成 ──────────────────────────────────

def generate_insights(query: str, findings: dict, subqueries: list, deep_articles: list) -> str:
    deep_section = ""
    if deep_articles:
        deep_fmt = "\n".join(
            f"・{a.get('title','')[:50]}（{a.get('site','')}）\n  {(a.get('full_text','') or a.get('summary',''))[:200]}"
            for a in deep_articles[:5])
        deep_section = f"\n### 🔬 深掘りWeb（Round 2）\nサブクエリ: {', '.join(subqueries)}\n{deep_fmt}"

    prompt = f"""
以下の調査結果を読んで、「{query}」についての総合インサイトを日本語でまとめてください。

### 🌐 Web調査
{fmt_web(findings.get('web', []))}
{deep_section}

### 📺 YouTube
{fmt_youtube(findings.get('youtube', []))}

### 📖 Wikipedia
{fmt_wiki(findings.get('wikipedia', []))}

### 📱 Reddit
{fmt_reddit(findings.get('reddit', []))}

### 📈 Googleトレンド
{fmt_trends(findings.get('trends', {}))}

## 出力形式
- 箇条書き5〜7点でインサイトをまとめる
- 各ポイントは具体的な情報源や数字を引用する
- 最後に「まとめ」を2〜3文で記述する
- 架空の情報は作らない
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


# ── メイン処理 ─────────────────────────────────────────────

def run_research(query: str) -> dict:
    print(f"🔍 調査開始: 「{query}」\n")
    findings = {}

    # ── Phase 1: 5エージェント並列調査 ──
    print("⚡ Phase 1: 5エージェント並列調査中...")
    agents = {
        "web":       WebAgent(),
        "youtube":   YouTubeAgent(),
        "wikipedia": WikipediaAgent(),
        "reddit":    RedditAgent(),
        "trends":    TrendsAgent(),
    }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(a.research, query): name for name, a in agents.items()}
        for future in as_completed(futures):
            name   = futures[future]
            result = future.result()
            data   = result.get("data", {})

            if result.get("status") == "error":
                print(f"  ⚠️  {name}: エラー - {result.get('error','')[:50]}")
                continue

            if name == "web":
                articles = data.get("articles", [])
                findings["web"] = articles
                full_count = sum(1 for a in articles if a.get("full_text"))
                print(f"  ✅ Web: {len(articles)}件（全文取得: {full_count}件）")
            elif name == "youtube":
                videos = data.get("videos", [])
                findings["youtube"] = videos
                print(f"  ✅ YouTube: {len(videos)}本")
            elif name == "wikipedia":
                articles = data.get("articles", [])
                findings["wikipedia"] = articles
                print(f"  ✅ Wikipedia: {len(articles)}件")
            elif name == "reddit":
                posts = data.get("posts", [])
                findings["reddit"] = posts
                en_q = data.get("en_query", "")
                print(f"  ✅ Reddit: {len(posts)}件（英語変換: 「{en_q}」）")
            elif name == "trends":
                findings["trends"] = data
                trending_count = len(data.get("trending_now", []))
                print(f"  ✅ Trends: 急上昇{trending_count}件取得")

    # ── Phase 2: サブクエリ生成 → 深掘り検索 ──
    print("\n🔬 Phase 2: 深掘りクエリを生成・再検索中...")
    subqueries  = []
    deep_articles = []
    try:
        subqueries = generate_subqueries(query, findings)
        print(f"  生成されたサブクエリ: {subqueries}")

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures2 = {executor.submit(WebAgent().research, sq): sq for sq in subqueries}
            for future in as_completed(futures2):
                sq     = futures2[future]
                result = future.result()
                arts   = result.get("data", {}).get("articles", [])
                deep_articles.extend(arts[:3])
                full_count = sum(1 for a in arts[:3] if a.get("full_text"))
                print(f"  ✅ 「{sq[:25]}」→ {len(arts)}件（全文: {full_count}件）")

        findings["web_deep"] = deep_articles
    except Exception as e:
        print(f"  ⚠️  深掘りエラー: {e}")

    # ── Phase 3: GPT総合インサイト ──
    print("\n💡 Phase 3: GPT総合インサイト生成中...")
    insights = ""
    try:
        insights = generate_insights(query, findings, subqueries, deep_articles)
    except Exception as e:
        insights = f"インサイト生成エラー: {e}"

    # ── レポート保存 ──
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"quick_report_{ts}.json"
    report = {
        "query":      query,
        "timestamp":  datetime.now().isoformat(),
        "subqueries": subqueries,
        "insights":   insights,
        "findings":   {k: v for k, v in findings.items()},
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── stdout に結果出力（Claudeが読む用）──
    print(f"\n{'='*60}")
    print(f"📊 調査結果サマリー：{query}")
    print(f"{'='*60}")

    web_arts = findings.get("web", [])
    if web_arts:
        print("\n🌐 Web記事 TOP3:")
        for a in web_arts[:3]:
            print(f"  ・{a['title'][:55]}")
            print(f"    {a['url']}")

    yt_vids = findings.get("youtube", [])
    if yt_vids:
        print("\n📺 YouTube TOP3:")
        for v in yt_vids[:3]:
            print(f"  ・{v['title'][:50]} | {v.get('views',0):,}回 / {v['channel']}")

    wiki_arts = findings.get("wikipedia", [])
    if wiki_arts:
        print("\n📖 Wikipedia:")
        for a in wiki_arts[:3]:
            print(f"  ・{a['title']}")

    reddit_posts = findings.get("reddit", [])
    if reddit_posts:
        print("\n📱 Reddit TOP3:")
        for p in reddit_posts[:3]:
            print(f"  ・{p['title'][:50]} ({p['subreddit']}) 👍{p['score']}")

    trends_data = findings.get("trends", {})
    if trends_data:
        print("\n📈 Googleトレンド:")
        for t in trends_data.get("trending_now", [])[:5]:
            print(f"  ・{t['keyword']}")

    if deep_articles:
        print(f"\n🔬 深掘り記事（Round 2）: {len(deep_articles)}件")
        for a in deep_articles[:3]:
            print(f"  ・{a['title'][:55]}")

    print(f"\n{'='*60}")
    print("💡 GPT総合インサイト:")
    print(f"{'='*60}")
    print(insights)
    print(f"\n📁 レポート保存: {report_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="マルチエージェント高速リサーチ")
    parser.add_argument("query", nargs="?", default="飲食店 AI活用", help="調査クエリ")
    args = parser.parse_args()
    try:
        run_research(args.query)
    except KeyboardInterrupt:
        print("\n中断しました")
        sys.exit(0)


if __name__ == "__main__":
    main()
