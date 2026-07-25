/**
 * AI最新情報 LINE自動配信bot
 *
 * セットアップ手順は README.md を参照。
 * 実行前に「プロジェクトの設定」→「スクリプト プロパティ」に以下を設定すること:
 *   LINE_CHANNEL_ACCESS_TOKEN
 *   LINE_USER_ID
 *
 * 使い方:
 *   1. testFetchAll() を実行して各ソースが正しく取れるか確認
 *   2. main() を手動実行して実際にLINEへ届くか確認
 *   3. setupTrigger() を1回実行して毎朝7時(JST)の自動実行を設定
 */

var SOURCES = [
  { name: 'OpenAI Blog', url: 'https://openai.com/news/rss.xml' },
  { name: 'Google DeepMind Blog', url: 'https://deepmind.google/blog/feed/basic/' },
  { name: 'TestingCatalog', url: 'https://www.testingcatalog.com/feed/' },
  { name: 'Hacker News (AI関連)', url: 'https://hnrss.org/newest?q=AI+OR+GPT+OR+Claude&count=30' },
  { name: 'Reddit r/OpenAI', url: 'https://old.reddit.com/r/OpenAI/.rss' },
  { name: 'Reddit r/ClaudeAI', url: 'https://old.reddit.com/r/ClaudeAI/.rss' },
  { name: 'Reddit r/singularity', url: 'https://old.reddit.com/r/singularity/.rss' },
  { name: 'Reddit r/artificial', url: 'https://old.reddit.com/r/artificial/.rss' },
  { name: 'ITmedia AI+', url: 'https://rss.itmedia.co.jp/rss/2.0/aiplus.xml' },
  { name: 'Ledge.ai', url: 'https://yoshiori.github.io/ledge-ai-feed/rss.xml' }
];

var BOOTSTRAP_WINDOW_MS = 36 * 60 * 60 * 1000; // lastRunAt未設定時の初回フォールバック窓
var MAX_MESSAGE_CHARS = 4800; // LINEの1メッセージ5000文字制限に対する安全マージン
var MAX_MESSAGES_PER_PUSH = 5; // LINE Messaging APIのpush上限

/**
 * 毎朝のトリガーから呼ばれるオーケストレーター
 */
function main() {
  var props = PropertiesService.getScriptProperties();
  var lastRunAtStr = props.getProperty('lastRunAt');
  var cutoffMs = lastRunAtStr ? new Date(lastRunAtStr).getTime() : (Date.now() - BOOTSTRAP_WINDOW_MS);

  var itemsBySource = {};
  SOURCES.forEach(function (source) {
    try {
      var items = fetchAndParseFeed_(source.url);
      itemsBySource[source.name] = items.filter(function (item) {
        return item.pubDate.getTime() > cutoffMs;
      });
    } catch (e) {
      Logger.log('ソース取得失敗: ' + source.name + ' - ' + e);
      itemsBySource[source.name] = [];
    }
    Utilities.sleep(700); // Reddit等の連続アクセスによるレート制限(429)を避ける
  });

  var messages = buildMessages_(itemsBySource);
  if (messages.length > 0) {
    sendLineMessage_(messages);
    Logger.log(messages.length + '件のメッセージを送信しました');
  } else {
    Logger.log('新着なし。送信スキップ');
  }

  props.setProperty('lastRunAt', new Date().toISOString());
}

/**
 * 各ソースを個別にログ出力するデバッグ用関数（LINE送信なし）
 */
function testFetchAll() {
  SOURCES.forEach(function (source) {
    try {
      var items = fetchAndParseFeed_(source.url);
      Logger.log('--- ' + source.name + ' (' + items.length + '件) ---');
      items.slice(0, 3).forEach(function (item) {
        Logger.log(item.pubDate + ' | ' + item.title + ' | ' + item.link);
      });
    } catch (e) {
      Logger.log('エラー: ' + source.name + ' - ' + e);
    }
    Utilities.sleep(700);
  });
}

/**
 * 毎日07:00(JST)の時間主導型トリガーを作成する（1回だけ手動実行すればよい）
 */
function setupTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (trigger) {
    if (trigger.getHandlerFunction() === 'main') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  ScriptApp.newTrigger('main')
    .timeBased()
    .atHour(7)
    .everyDays(1)
    .inTimezone('Asia/Tokyo')
    .create();
  Logger.log('毎朝7時(JST)のトリガーを作成しました');
}

/**
 * 友だち追加済みユーザーのUser IDを取得する（Webhook不要）。
 * LINE_CHANNEL_ACCESS_TOKEN をScript Propertiesに設定済みであれば実行できる。
 * 実行後、実行ログに出た自分のuserIdを LINE_USER_ID として登録すること。
 */
function getFollowerIds() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('LINE_CHANNEL_ACCESS_TOKEN');
  if (!token) {
    throw new Error('LINE_CHANNEL_ACCESS_TOKEN が Script Properties に設定されていません');
  }
  var response = UrlFetchApp.fetch('https://api.line.me/v2/bot/followers/ids', {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  });
  Logger.log(response.getResponseCode() + ' ' + response.getContentText());
}

// ---- 内部関数 ----

function fetchAndParseFeed_(url) {
  var options = {
    headers: { 'User-Agent': 'Mozilla/5.0 (compatible; AINewsDigestBot/1.0)' },
    muteHttpExceptions: true
  };
  var response = UrlFetchApp.fetch(url, options);
  if (response.getResponseCode() !== 200) {
    // 一時的な5xxエラー対策で1回だけリトライ
    Utilities.sleep(1500);
    response = UrlFetchApp.fetch(url, options);
    if (response.getResponseCode() !== 200) {
      throw new Error('HTTP ' + response.getResponseCode());
    }
  }
  return parseFeed_(response.getContentText());
}

/**
 * RSS 2.0 / Atom 両対応のフィードパーサー
 */
function parseFeed_(xmlText) {
  var root = XmlService.parse(xmlText).getRootElement();
  var items = [];

  if (root.getName() === 'rss') {
    var channel = root.getChild('channel');
    channel.getChildren('item').forEach(function (item) {
      items.push({
        title: getChildText_(item, 'title'),
        link: getChildText_(item, 'link'),
        pubDate: parseDate_(getChildText_(item, 'pubDate'))
      });
    });
  } else if (root.getName() === 'feed') {
    var ns = root.getNamespace();
    root.getChildren('entry', ns).forEach(function (entry) {
      var dateText = getChildText_(entry, 'updated', ns) || getChildText_(entry, 'published', ns);
      items.push({
        title: getChildText_(entry, 'title', ns),
        link: getAtomLink_(entry, ns),
        pubDate: parseDate_(dateText)
      });
    });
  }

  return items;
}

function getChildText_(parent, name, ns) {
  var el = ns ? parent.getChild(name, ns) : parent.getChild(name);
  return el ? el.getText() : '';
}

function getAtomLink_(entry, ns) {
  var links = entry.getChildren('link', ns);
  for (var i = 0; i < links.length; i++) {
    var rel = links[i].getAttribute('rel');
    if (!rel || rel.getValue() === 'alternate') {
      return links[i].getAttribute('href').getValue();
    }
  }
  return links.length > 0 ? links[0].getAttribute('href').getValue() : '';
}

function parseDate_(text) {
  var d = new Date(text);
  return isNaN(d.getTime()) ? new Date(0) : d;
}

/**
 * タイトルを日本語に翻訳する（既に日本語の場合もそのまま渡してOK）。
 * 翻訳に失敗した場合は原文のまま返す。
 */
function translateTitle_(text) {
  try {
    return LanguageApp.translate(text, '', 'ja');
  } catch (e) {
    return text;
  }
}

/**
 * ソースごとにグルーピングしたテキストを組み立て、LINEの文字数・件数上限に合わせて分割
 */
function buildMessages_(itemsBySource) {
  var blocks = [];
  Object.keys(itemsBySource).forEach(function (sourceName) {
    var items = itemsBySource[sourceName];
    if (items.length === 0) return;
    var lines = ['■ ' + sourceName, ''];
    items.forEach(function (item) {
      lines.push('・' + translateTitle_(item.title));
      lines.push(item.link);
      lines.push('');
    });
    blocks.push(lines.join('\n').replace(/\n+$/, ''));
  });

  if (blocks.length === 0) return [];

  var messages = [];
  var current = '';
  blocks.forEach(function (block) {
    var candidate = current ? current + '\n\n' + block : block;
    if (candidate.length > MAX_MESSAGE_CHARS && current) {
      messages.push(current);
      current = block;
    } else {
      current = candidate;
    }
  });
  if (current) messages.push(current);

  return messages.slice(0, MAX_MESSAGES_PER_PUSH);
}

function sendLineMessage_(texts) {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('LINE_CHANNEL_ACCESS_TOKEN');
  var userId = props.getProperty('LINE_USER_ID');
  if (!token || !userId) {
    throw new Error('LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が Script Properties に設定されていません');
  }

  var payload = {
    to: userId,
    messages: texts.map(function (t) { return { type: 'text', text: t }; })
  };

  var response = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  var code = response.getResponseCode();
  if (code !== 200) {
    throw new Error('LINE送信失敗: ' + code + ' ' + response.getContentText());
  }
}
