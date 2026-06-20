/**
 * kpi-reporter
 * ---------------------------------------------
 * 店舗の週次売上データを自動集計し、サマリーレポートを生成して
 * 関係者に自動送信するツール。
 *
 * 想定シート構成:
 *   - 「回答ログ」シート: フォーム送信された日々の実績データ
 *       A列: タイムスタンプ
 *       B列: スタッフ名
 *       C列: 項目（auMNP / マネ活 / 付属品売上 等、自由記述）
 *       D列: 金額・件数
 *   - 「週次レポート」シート: 本スクリプトが出力するレポート置き場
 *
 * 主な機能:
 *   1. 直近1週間（実行日から7日前〜実行日）の実績を「回答ログ」から集計
 *   2. スタッフ別・項目別のサマリーを作成
 *   3. サマリーを「週次レポート」シートに書き出し
 *   4. メール（または Slack / Chat Webhook）でサマリーを送信
 *
 * 使い方:
 *   1. このファイルをGASエディタに貼り付ける
 *   2. CONFIG セクションの値を環境に合わせて書き換える
 *   3. weeklyReport() を時間主導型トリガーに設定（毎週月曜 9:00 等）
 */

// ============ CONFIG ============
const CONFIG = {
  LOG_SHEET_NAME: '回答ログ',
  REPORT_SHEET_NAME: '週次レポート',
  // タイムスタンプが入っている列（1-indexed）
  COL_TIMESTAMP: 1,
  COL_STAFF: 2,
  COL_ITEM: 3,
  COL_AMOUNT: 4,
  // レポートの送信先メールアドレス（カンマ区切りで複数可）
  REPORT_RECIPIENTS: 'your-email@example.com',
  // 件名のプレフィックス
  MAIL_SUBJECT_PREFIX: '【週次売上レポート】',
};
// =================================

/**
 * メインエントリーポイント。
 * 時間主導型トリガーに登録して週次で実行する。
 */
function weeklyReport() {
  const { startDate, endDate } = getReportingWindow_();
  const records = fetchRecordsInRange_(startDate, endDate);

  if (records.length === 0) {
    Logger.log('対象期間のデータがありませんでした: ' + formatDate_(startDate) + ' 〜 ' + formatDate_(endDate));
    return;
  }

  const summary = buildSummary_(records);
  writeSummaryToSheet_(summary, startDate, endDate);
  sendSummaryMail_(summary, startDate, endDate);

  Logger.log('週次レポートを生成・送信しました: ' + formatDate_(startDate) + ' 〜 ' + formatDate_(endDate));
}

/**
 * 集計対象期間（直近7日間）を算出する。
 */
function getReportingWindow_() {
  const today = new Date();
  const endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const startDate = new Date(endDate);
  startDate.setDate(startDate.getDate() - 7);
  return { startDate, endDate };
}

/**
 * 「回答ログ」シートから、指定期間内のレコードを取得する。
 */
function fetchRecordsInRange_(startDate, endDate) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.LOG_SHEET_NAME);
  if (!sheet) {
    throw new Error('シートが見つかりません: ' + CONFIG.LOG_SHEET_NAME);
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];

  const values = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();

  return values
    .map((row) => ({
      timestamp: row[CONFIG.COL_TIMESTAMP - 1],
      staff: row[CONFIG.COL_STAFF - 1],
      item: row[CONFIG.COL_ITEM - 1],
      amount: Number(row[CONFIG.COL_AMOUNT - 1]) || 0,
    }))
    .filter((r) => {
      if (!(r.timestamp instanceof Date)) return false;
      return r.timestamp >= startDate && r.timestamp < endDate;
    });
}

/**
 * レコード一覧から、スタッフ別・項目別のサマリーを作成する。
 */
function buildSummary_(records) {
  const byStaff = {};
  const byItem = {};
  let total = 0;

  records.forEach((r) => {
    byStaff[r.staff] = (byStaff[r.staff] || 0) + r.amount;
    byItem[r.item] = (byItem[r.item] || 0) + r.amount;
    total += r.amount;
  });

  return {
    total,
    byStaff,
    byItem,
    recordCount: records.length,
  };
}

/**
 * サマリーを「週次レポート」シートに書き出す。
 * 過去の履歴を残すため、毎回新しい行を追記する形式。
 */
function writeSummaryToSheet_(summary, startDate, endDate) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONFIG.REPORT_SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.REPORT_SHEET_NAME);
    sheet.appendRow(['期間開始', '期間終了', '合計', '件数', 'スタッフ別内訳', '項目別内訳', '出力日時']);
  }

  sheet.appendRow([
    formatDate_(startDate),
    formatDate_(endDate),
    summary.total,
    summary.recordCount,
    formatBreakdown_(summary.byStaff),
    formatBreakdown_(summary.byItem),
    new Date(),
  ]);
}

/**
 * サマリーをメールで送信する。
 */
function sendSummaryMail_(summary, startDate, endDate) {
  const subject = CONFIG.MAIL_SUBJECT_PREFIX + formatDate_(startDate) + '〜' + formatDate_(endDate);
  const body = buildMailBody_(summary, startDate, endDate);

  MailApp.sendEmail({
    to: CONFIG.REPORT_RECIPIENTS,
    subject,
    body,
  });
}

/**
 * メール本文を組み立てる。
 */
function buildMailBody_(summary, startDate, endDate) {
  const lines = [];
  lines.push('週次売上レポート（' + formatDate_(startDate) + ' 〜 ' + formatDate_(endDate) + '）');
  lines.push('');
  lines.push('■ 合計: ' + summary.total.toLocaleString() + ' 円（' + summary.recordCount + '件）');
  lines.push('');
  lines.push('■ スタッフ別内訳');
  lines.push(formatBreakdown_(summary.byStaff));
  lines.push('');
  lines.push('■ 項目別内訳');
  lines.push(formatBreakdown_(summary.byItem));
  lines.push('');
  lines.push('---');
  lines.push('このレポートは自動生成されています。');

  return lines.join('\n');
}

/**
 * 内訳オブジェクトを「key: value」の複数行テキストに変換する。
 */
function formatBreakdown_(breakdown) {
  return Object.keys(breakdown)
    .sort((a, b) => breakdown[b] - breakdown[a])
    .map((key) => '  ・' + key + ': ' + breakdown[key].toLocaleString() + ' 円')
    .join('\n');
}

/**
 * 日付を YYYY/MM/DD 形式の文字列に変換する。
 */
function formatDate_(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy/MM/dd');
}

/**
 * 動作確認用のテスト関数。
 * GASエディタから直接実行して、ログにサマリーが出力されることを確認できる。
 */
function testWeeklyReport() {
  const { startDate, endDate } = getReportingWindow_();
  Logger.log('集計対象期間: ' + formatDate_(startDate) + ' 〜 ' + formatDate_(endDate));
  const records = fetchRecordsInRange_(startDate, endDate);
  Logger.log('取得レコード数: ' + records.length);
  const summary = buildSummary_(records);
  Logger.log(JSON.stringify(summary, null, 2));
}
