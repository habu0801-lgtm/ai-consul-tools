#!/usr/bin/env python3
"""
Research Hub - Slack風WebアプリサーバーFlask + SSEでリアルタイムエージェント会話を配信
"""
import json
import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from flask import Flask, render_template, Response, request, jsonify
from openai import OpenAI

import config
from agents.wikipedia_agent import WikipediaAgent
from agents.web_agent import WebAgent
from agents.youtube_agent import YouTubeAgent
from agents.reddit_agent import RedditAgent
from agents.trends_agent import TrendsAgent

app = Flask(__name__)
client = OpenAI(api_key=config.OPENAI_API_KEY)


# ── SSEヘルパー ──────────────────────────────────────────────

def sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ── 調査データのフォーマット ─────────────────────────────────

def fmt_trends(data):
    if not data: return "（データなし）"
    lines = []
    trending = data.get("trending_now", [])
    related  = data.get("related_trends", [])
    suggs    = data.get("suggestions", [])
    kw       = data.get("keyword", "")
    if related:
        lines.append(f"「{kw}」関連の急上昇: " + " / ".join(t["keyword"] for t in related[:3]))
    if trending:
        lines.append("今日の急上昇TOP5: " + " / ".join(t["keyword"] for t in trending[:5]))
    if suggs:
        lines.append("Googleサジェスト: " + " / ".join(s["title"][:20] for s in suggs[:3]))
    return "\n".join(lines) if lines else "（トレンドデータなし）"

def fmt_reddit(posts):
    if not posts: return "（投稿なし）"
    return "\n".join(
        f"・{p.get('title','')[:50]}（{p.get('subreddit','')}）👍{p.get('score',0)} 💬{p.get('num_comments',0)}\n  {p.get('selftext','')[:80]}"
        for p in posts[:5])

def fmt_web(articles):
    if not articles: return "（記事なし）"
    lines = []
    for a in articles[:5]:
        title   = a.get('title', '')[:50]
        site    = a.get('site', '')
        summary = a.get('summary', '')[:100]
        full    = a.get('full_text', '')
        if full:
            body = full[:500]  # 全文の最初500文字をGPTに渡す
        else:
            body = summary
        lines.append(f"・{title}（{site}）\n  {body}")
    return "\n".join(lines)

def fmt_youtube(videos):
    if not videos: return "（動画なし）"
    return "\n".join(
        f"・『{v.get('title','')[:50]}』 再生{v.get('views',0):,}回 / {v.get('channel','')}\n  {v.get('description','')[:80]}"
        for v in videos[:5])

def fmt_wiki(articles):
    if not articles: return "（記事なし）"
    return "\n".join(
        f"・{a.get('title','')}：{a.get('snippet','')[:80]}"
        for a in articles[:4])


# ── サブクエリ生成 ───────────────────────────────────────────

def generate_subqueries(query: str, findings: dict) -> list:
    """Round 1の結果をもとに深掘りサブクエリを2〜3個生成"""
    summary = (
        f"Web: {fmt_web(findings.get('web', []))[:300]}\n"
        f"YouTube: {fmt_youtube(findings.get('youtube', []))[:150]}\n"
        f"Wikipedia: {fmt_wiki(findings.get('wikipedia', []))[:150]}\n"
        f"Reddit: {fmt_reddit(findings.get('reddit', []))[:150]}"
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


# ── GPTでエージェント会話を生成 ──────────────────────────────

def generate_discussion(query: str, findings: dict):
    """実際の調査データをもとにGPTでエージェント間の会話を生成しストリーミングで返す"""

    deep_section = ""
    if findings.get("web_deep"):
        deep_section = f"\n### 🔬 深掘りWeb調査（Round 2）\n{fmt_web(findings.get('web_deep', []))}"

    prompt = f"""
あなたは調査チャットシステムのシミュレーターです。
以下の実際の調査結果をもとに、エージェントが自然な会話をしている様子を生成してください。

## 調査クエリ
「{query}」

## 実際の調査結果

### 🌐 Web調査員（Round 1）
{fmt_web(findings.get('web', []))}
{deep_section}

### 📺 YouTube調査員
{fmt_youtube(findings.get('youtube', []))}

### 📖 Wikipedia調査員
{fmt_wiki(findings.get('wikipedia', []))}

### 📱 Reddit調査員
{fmt_reddit(findings.get('reddit', []))}

### 📈 トレンド調査員
{fmt_trends(findings.get('trends', {}))}

## 会話のルール
- 各エージェントは自分が実際に見つけた情報を具体的に引用して話す
  （例：「〇〇というサイトによると」「再生数△万回の動画では」「Redditの r/〇〇 では」）
- Round 2の深掘り結果があれば積極的に言及する
- エージェント同士が互いの発見に反応・質問する自然な会話にする
- AI統括（synthesizer）が要所で整理・深掘り質問をする
- 会話は8〜10ターン

## まとめのルール（最重要）
- 最後にsynthesizerが5〜7点のインサイトを出す
- **各インサイトは必ず以下を含む：**
  1. 具体的なサイト名・動画タイトル・Redditスレッド・数字・固有名詞
  2. 「なぜそれが重要か」の一文
- **以下は絶対禁止：**
  - 「〜が進んでいる」「〜が注目されている」「〜が急務となっている」のような抽象的な一般論
  - 調査結果に書いていない架空の情報
  - ソースを示さない断言

## 出力フォーマット（厳守）
- **必ず全行**を「エージェントID: メッセージ」形式で出力する
- IDは web / youtube / wikipedia / reddit / trends / synthesizer のみ
- 箇条書きや番号リストも必ずエージェントIDを先頭につける
- 空行は出力しない

## まとめの良い例（このレベルを目指す）:
synthesizer: では調査結果をまとめます。
synthesizer: 1.【具体的発見】brainpad.co.jp の記事では、ChatGPT導入後に問い合わせ対応時間が平均40%削減された事例が紹介されていました。単なる効率化ではなく「定量的な成果が出ている」点が重要です。
synthesizer: 2.【YouTube傾向】「一人で100人分働く社長」動画（242,740回再生）が突出しており、個人・中小企業が主な関心層であることがわかります。大企業向けより個人活用の需要が高い。
synthesizer: 3.【海外動向】Reddit の r/technology では IHOP・Applebee'sがAI導入を発表したスレッドが話題で、日本より先行している飲食チェーンの事例として参考になります。
synthesizer: 4.【トレンド】Googleサジェストに「UMAME!（AIグルメマッチング）」が複数登場しており、飲食×AI領域で新サービスが生まれ始めているシグナルです。
web: 補足すると、深掘り調査でも「補助金との組み合わせ」というキーワードが複数記事に登場していました。
"""

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=2500,
        stream=True,
    )

    buffer = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        buffer += delta
        # 行が完成したらyield
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line:
                yield line

    if buffer.strip():
        yield buffer.strip()


def parse_agent_line(line: str):
    """'agent: message' 形式をパース"""
    ids = ["web", "youtube", "wikipedia", "reddit", "trends", "synthesizer"]
    for aid in ids:
        if line.lower().startswith(f"{aid}:"):
            msg = line[len(aid)+1:].strip()
            return aid, msg
    return None, line


# ── ルーティング ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/research")
def research():
    query = request.args.get("q", "").strip()
    if not query:
        return Response("data: {}\n\n", mimetype="text/event-stream")

    def generate():
        findings = {}

        # Phase 1: 並列調査
        agents = {
            "web":       WebAgent(),
            "youtube":   YouTubeAgent(),
            "wikipedia": WikipediaAgent(),
            "reddit":    RedditAgent(),
            "trends":    TrendsAgent(),
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(a.research, query): name for name, a in agents.items()}
            for future in as_completed(futures):
                name   = futures[future]
                result = future.result()
                data   = result.get("data", {})

                # タイピング表示
                yield sse({"type": "typing", "agent": name})
                time.sleep(0.5)

                if result.get("status") == "error":
                    yield sse({"type": "result", "agent": name,
                               "lines": [f"エラーが発生しました: {result.get('error','不明')}"]})
                    continue

                if name == "web":
                    articles = data.get("articles", [])
                    findings["web"] = articles
                    lines = [f"Web記事 {len(articles)}件 ヒット！"] if articles else ["記事が見つかりませんでした"]
                    yield sse({"type": "result", "agent": "web",
                               "lines": lines, "articles": articles})

                elif name == "youtube":
                    videos = data.get("videos", [])
                    findings["youtube"] = videos
                    lines = [f"YouTube動画 {len(videos)}本 発見！"] if videos else ["動画が見つかりませんでした"]
                    yield sse({"type": "result", "agent": "youtube",
                               "lines": lines, "videos": videos})

                elif name == "wikipedia":
                    articles = data.get("articles", [])
                    findings["wikipedia"] = articles
                    lines = [f"Wikipedia関連記事 {len(articles)}件"] if articles else ["記事が見つかりませんでした"]
                    yield sse({"type": "result", "agent": "wikipedia",
                               "lines": lines, "articles": articles})

                elif name == "reddit":
                    posts = data.get("posts", [])
                    findings["reddit"] = posts
                    lines = [f"Reddit投稿 {len(posts)}件 発見！"] if posts else ["投稿が見つかりませんでした"]
                    yield sse({"type": "result", "agent": "reddit",
                               "lines": lines, "posts": posts})

                elif name == "trends":
                    findings["trends"] = data
                    trending = data.get("trending_now", [])
                    related  = data.get("related_trends", [])
                    suggs    = data.get("suggestions", [])
                    if related:
                        lines = [f"関連急上昇: {' / '.join(t['keyword'] for t in related[:3])}"]
                    elif trending:
                        lines = [f"今日の急上昇TOP: {' / '.join(t['keyword'] for t in trending[:3])}"]
                    else:
                        lines = ["トレンドデータを取得しました"]
                    if suggs:
                        lines.append(f"サジェスト: {' / '.join(s['title'][:15] for s in suggs[:3])}")
                    yield sse({"type": "result", "agent": "trends", "lines": lines})

        # Phase 1.5: サブクエリ生成 → Phase 2: 深掘り検索
        yield sse({"type": "divider", "text": "🔍 深掘りクエリを生成中..."})
        time.sleep(0.3)

        try:
            subqueries = generate_subqueries(query, findings)
            yield sse({"type": "subquery", "agent": "synthesizer",
                       "queries": subqueries,
                       "text": f"以下のサブクエリで深掘りします：" + " / ".join(f"「{q}」" for q in subqueries)})
            time.sleep(0.5)

            yield sse({"type": "divider", "text": "🔬 Round 2: 深掘り検索"})
            deep_articles = []

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(WebAgent().research, sq): sq for sq in subqueries}
                for future in as_completed(futures):
                    sq     = futures[future]
                    result = future.result()
                    arts   = result.get("data", {}).get("articles", [])

                    yield sse({"type": "typing", "agent": "web"})
                    time.sleep(0.3)

                    if arts:
                        deep_articles.extend(arts[:3])
                        yield sse({"type": "result", "agent": "web",
                                   "lines": [f"「{sq[:25]}」→ {len(arts)}件追加取得"],
                                   "articles": arts[:3], "subquery": sq})
                    else:
                        yield sse({"type": "result", "agent": "web",
                                   "lines": [f"「{sq[:25]}」→ 追加記事なし"]})

            findings["web_deep"] = deep_articles

        except Exception as e:
            yield sse({"type": "chat", "agent": "system",
                       "text": f"深掘り検索エラー: {e}"})

        # Phase 3: GPT会話
        yield sse({"type": "divider", "text": "💬 エージェント間ディスカッション"})
        time.sleep(0.3)

        try:
            last_agent = "synthesizer"
            for line in generate_discussion(query, findings):
                agent_id, msg = parse_agent_line(line)
                if agent_id:
                    last_agent = agent_id  # 最後に発言したエージェントを記憶
                else:
                    agent_id = last_agent  # IDなし行は直前エージェントに紐付け
                if msg:
                    yield sse({"type": "chat", "agent": agent_id, "text": msg})
                    time.sleep(0.35)
        except Exception as e:
            yield sse({"type": "chat", "agent": "system",
                       "text": f"GPT会話生成エラー: {e}"})

        # レポート保存
        output_dir = Path(config.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"report_{ts}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"query": query, "timestamp": datetime.now().isoformat(),
                       "findings": findings}, f, ensure_ascii=False, indent=2)

        yield sse({"type": "done", "report": str(path)})

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/reports")
def reports():
    output_dir = Path(config.OUTPUT_DIR)
    files = sorted(output_dir.glob("report_*.json"), reverse=True)[:15]
    result = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fp:
                d = json.load(fp)
            result.append({
                "file": f.name,
                "query": d.get("query", "不明"),
                "date": d.get("timestamp", "")[:16].replace("T", " "),
            })
        except Exception:
            pass
    return jsonify(result)


@app.route("/report/<filename>")
def view_report(filename):
    path = Path(config.OUTPUT_DIR) / filename
    if not path.exists():
        return "Not found", 404
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    findings = d.get("findings", {})

    html = f"<html><head><meta charset='UTF-8'><title>{d.get('query','')}</title>"
    html += "<style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;background:#1a1d21;color:#d1d2d3}}h1{{color:#fff}}h2{{color:#aaa;border-bottom:1px solid #333;padding-bottom:6px}}a{{color:#60a5fa}}</style></head><body>"
    html += f"<h1>🔍 {d.get('query','')}</h1>"
    html += f"<p style='color:#666'>{d.get('timestamp','')[:19]}</p>"

    for source, items in findings.items():
        html += f"<h2>{source.upper()}</h2>"
        if isinstance(items, list):
            for item in items[:10]:
                if "title" in item:
                    url = item.get("url", "#")
                    title = item.get("title", "")
                    summary = item.get("summary") or item.get("snippet", "")
                    html += f"<p>📄 <a href='{url}' target='_blank'>{title}</a><br><small style='color:#666'>{summary[:100]}</small></p>"
                elif "video_id" in item:
                    url = f"https://youtube.com/watch?v={item['video_id']}"
                    html += f"<p>🎬 <a href='{url}' target='_blank'>{item.get('title','')}</a> — {item.get('channel','')} 👁{item.get('views',0):,}</p>"
    html += "</body></html>"
    return html


if __name__ == "__main__":
    print("🚀 Research Hub 起動中... http://localhost:5000")
    app.run(debug=False, threaded=True, port=5000)
