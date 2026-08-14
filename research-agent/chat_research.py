#!/usr/bin/env python3
"""
Slack風マルチエージェント調査チャット（GPT会話生成版）
使い方: python chat_research.py "調査したいテーマ"
"""
import sys
import time
import argparse
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from openai import OpenAI

import config
from agents.wikipedia_agent import WikipediaAgent
from agents.web_agent import WebAgent
from agents.youtube_agent import YouTubeAgent
from agents.reddit_agent import RedditAgent

client = OpenAI(api_key=config.OPENAI_API_KEY)

# ========== ターミナルカラー ==========
R   = "\033[0m"
B   = "\033[1m"
DIM = "\033[2m"

COLORS = {
    "web":         "\033[96m",
    "youtube":     "\033[91m",
    "wikipedia":   "\033[94m",
    "reddit":      "\033[33m",
    "synthesizer": "\033[93m",
    "system":      "\033[90m",
}
NAMES = {
    "web":         "🌐 Web調査員",
    "youtube":     "📺 YouTube調査員",
    "wikipedia":   "📖 Wikipedia調査員",
    "reddit":      "📱 Reddit調査員",
    "synthesizer": "🧠 AI統括",
    "system":      "⚙️  SYSTEM",
}

lock = threading.Lock()


def ts():
    return datetime.now().strftime("%H:%M")


def header(query: str):
    print(f"\n{B}{'━' * 64}{R}")
    print(f"{B}  # research-channel{R}")
    print(f"{DIM}  クエリ: {query}{R}")
    print(f"{B}{'━' * 64}{R}\n")


def divider():
    print(f"{DIM}{'─' * 64}{R}\n")


def say(agent: str, *lines: str, pause: float = 0.0):
    if pause:
        time.sleep(pause)
    with lock:
        color = COLORS.get(agent, "")
        name  = NAMES.get(agent, agent)
        print(f"{color}{B}{name}{R}  {DIM}{ts()}{R}")
        for line in lines:
            print(f"  {line}")
        print()


def typing(agent: str, duration: float = 0.8):
    color = COLORS.get(agent, "")
    name  = NAMES.get(agent, agent)
    print(f"  {DIM}{name} が入力中...{R}", end="\r", flush=True)
    time.sleep(duration)
    print(" " * 60, end="\r", flush=True)


def stream_say(agent: str, text: str):
    """GPT出力をストリーミング風に1文字ずつ表示"""
    color = COLORS.get(agent, "")
    name  = NAMES.get(agent, agent)
    print(f"{color}{B}{name}{R}  {DIM}{ts()}{R}")
    print("  ", end="", flush=True)
    for i, ch in enumerate(text):
        if ch == "\n":
            print(f"\n  ", end="", flush=True)
        else:
            print(ch, end="", flush=True)
        # 句読点で少しポーズ
        if ch in "。！？\n":
            time.sleep(0.06)
        else:
            time.sleep(0.012)
    print("\n")


# ========== 調査データのサマリー生成 ==========

def format_web_findings(articles: list) -> str:
    if not articles:
        return "（検索結果なし）"
    lines = []
    for a in articles[:5]:
        title   = a.get("title", "")[:50]
        site    = a.get("site", "")
        full    = a.get("full_text", "")
        summary = a.get("summary", "")[:100]
        body    = full[:500] if full else summary
        lines.append(f"・{title}（{site}）\n  本文: {body}")
    return "\n".join(lines)


def format_youtube_findings(videos: list) -> str:
    if not videos:
        return "（動画なし）"
    lines = []
    for v in videos[:5]:
        title = v.get("title", "")[:50]
        ch    = v.get("channel", "")
        views = v.get("views", 0)
        desc  = v.get("description", "")[:80]
        lines.append(f"・『{title}』/ {ch} / 再生{views:,}回\n  説明: {desc}")
    return "\n".join(lines)


def format_reddit_findings(posts: list) -> str:
    if not posts:
        return "（投稿なし）"
    lines = []
    for p in posts[:5]:
        title = p.get("title", "")[:50]
        sub   = p.get("subreddit", "")
        score = p.get("score", 0)
        text  = p.get("selftext", "")[:80]
        lines.append(f"・{title}（{sub}）👍{score}\n  本文: {text}")
    return "\n".join(lines)


def format_wiki_findings(articles: list) -> str:
    if not articles:
        return "（記事なし）"
    lines = []
    for a in articles[:4]:
        title   = a.get("title", "")
        snippet = a.get("snippet", "")[:80]
        lines.append(f"・{title}\n  抜粋: {snippet}")
    return "\n".join(lines)


# ========== GPTでエージェント会話を生成 ==========

def generate_discussion(query: str, findings: dict) -> str:
    """実際の調査データをもとにGPTでエージェント間の会話を生成"""

    web_text  = format_web_findings(findings.get("web", []))
    yt_text   = format_youtube_findings(findings.get("youtube", []))
    wiki_text = format_wiki_findings(findings.get("wikipedia", []))

    prompt = f"""
あなたは調査チャットシステムのシミュレーターです。
以下の実際の調査結果をもとに、4人のエージェントが自然な会話をしている様子を生成してください。

## 調査クエリ
「{query}」

## 実際の調査結果

### 🌐 Web調査員が見つけた記事
{web_text}

### 📺 YouTube調査員が見つけた動画
{yt_text}

### 📖 Wikipedia調査員が見つけた記事
{wiki_text}

### 📱 Reddit調査員が見つけた投稿
{format_reddit_findings(findings.get("reddit", []))}

## ルール
- 各エージェントは自分が実際に見つけた情報だけを話す
- 調査結果の内容を具体的に引用して会話する（「○○という記事に〜と書いてありました」など）
- エージェント同士が互いの発見に驚いたり質問したり自然に反応する
- AI統括（🧠）が要所で質問や整理をする
- 会話は8〜12ターン程度
- 最後にAI統括が3〜5点のインサイトでまとめる
- Reddit調査員は海外の視点や英語圏の議論を紹介する

## 出力フォーマット（必ずこの形式で）
各行を「エージェントID: メッセージ」の形式で出力する。
エージェントIDは web / youtube / wikipedia / reddit / synthesizer のいずれか。
例:
web: 「〇〇」という記事によると...
youtube: それ面白いですね！YouTubeでも...
synthesizer: @web なるほど、具体的には？

## 注意
- 実際に見つかった情報に基づいて話すこと（架空の情報を作らない）
- 自然な日本語で話しかけるように
- ですます調で統一
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1200,
    )
    return response.choices[0].message.content


def parse_and_display_discussion(text: str):
    """GPTの出力をパースしてSlack風に表示"""
    agent_map = {
        "web": "web",
        "youtube": "youtube",
        "wikipedia": "wikipedia",
        "reddit": "reddit",
        "synthesizer": "synthesizer",
    }

    current_agent = None
    current_lines = []

    for raw_line in text.strip().split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # 「agent: message」形式を検出
        matched = False
        for key in agent_map:
            if line.lower().startswith(f"{key}:"):
                # 前のエージェントのメッセージを表示
                if current_agent and current_lines:
                    typing(current_agent, duration=0.7)
                    stream_say(current_agent, "\n".join(current_lines))
                    current_lines = []

                current_agent = agent_map[key]
                msg = line[len(key)+1:].strip()
                if msg:
                    current_lines.append(msg)
                matched = True
                break

        if not matched and current_agent:
            current_lines.append(line)

    # 最後のメッセージを表示
    if current_agent and current_lines:
        typing(current_agent, duration=0.7)
        stream_say(current_agent, "\n".join(current_lines))


# ========== メイン ==========

def run_chat_research(query: str):
    header(query)

    say("system", f"4エージェントが並列で「{query}」を調査中...", pause=0.3)

    agents = {
        "web":       WebAgent(),
        "youtube":   YouTubeAgent(),
        "wikipedia": WikipediaAgent(),
        "reddit":    RedditAgent(),
    }

    results     = {}
    all_findings = {}

    # ── Phase 1: 並列調査 + 逐次報告 ──────────────────────────
    divider()
    say("synthesizer", "みなさん、担当分野の調査をお願いします！結果が出た順に報告してください 🙌")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(a.research, query): name for name, a in agents.items()}
        for future in as_completed(futures):
            name   = futures[future]
            result = future.result()
            results[name] = result
            data   = result.get("data", {})

            typing(name, duration=0.5)

            if result.get("status") == "error":
                say(name, f"エラーが発生しました: {result.get('error', '不明')}")
                continue

            if name == "web":
                articles = data.get("articles", [])
                all_findings["web"] = articles
                if articles:
                    say(name,
                        f"Web記事 {len(articles)}件 ヒット！上位3件：",
                        *[f"  📄 {a.get('title','')[:45]}  ({a.get('site','')})"
                          for a in articles[:3]],
                        f"  ── {a.get('summary','')[:60]}..." if (a := articles[0]) else "")
                else:
                    say(name, "該当記事が見つかりませんでした")

            elif name == "youtube":
                videos = data.get("videos", [])
                all_findings["youtube"] = videos
                if videos:
                    say(name,
                        f"YouTube動画 {len(videos)}本 発見！上位3本：",
                        *[f"  🎬 『{v.get('title','')[:40]}』"
                          f"  👁 {v.get('views',0):,}回  /{v.get('channel','')}"
                          for v in videos[:3]])
                else:
                    say(name, "関連動画が見つかりませんでした")

            elif name == "wikipedia":
                articles = data.get("articles", [])
                all_findings["wikipedia"] = articles
                if articles:
                    say(name,
                        f"Wikipedia関連記事 {len(articles)}件：",
                        *[f"  📖 {a.get('title','')}  — {a.get('snippet','')[:50]}..."
                          for a in articles[:3]])
                else:
                    say(name, "関連記事が見つかりませんでした")

            elif name == "reddit":
                posts = data.get("posts", [])
                all_findings["reddit"] = posts
                if posts:
                    say(name,
                        f"Reddit投稿 {len(posts)}件 発見！上位3件：",
                        *[f"  🔶 {p.get('title','')[:45]}  ({p.get('subreddit','')})"
                          f"  👍{p.get('score',0)} 💬{p.get('num_comments',0)}"
                          for p in posts[:3]])
                else:
                    say(name, "関連投稿が見つかりませんでした")

    # ── Phase 2: GPTによるエージェント間ディスカッション ──────
    divider()
    say("system", "調査完了！エージェント間のディスカッションを生成中...", pause=0.3)

    try:
        discussion_text = generate_discussion(query, all_findings)
        parse_and_display_discussion(discussion_text)
    except Exception as e:
        say("system", f"GPT会話生成エラー: {e}")

    # ── レポート保存 ──────────────────────────────────────────
    divider()
    from pathlib import Path
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path  = output_dir / f"chat_report_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"query": query, "timestamp": datetime.now().isoformat(),
                   "findings": {k: v for k, v in all_findings.items()}},
                  f, ensure_ascii=False, indent=2)
    say("system", f"レポート保存完了: {json_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", default="飲食店 AI活用",
                        help="調査クエリ")
    args = parser.parse_args()
    try:
        run_chat_research(args.query)
    except KeyboardInterrupt:
        print(f"\n{DIM}  中断しました{R}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
