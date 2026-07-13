/**
 * sales-report-form
 * ---------------------------------------------
 * 現場スタッフがスマホからその場で接客実績を入力できる、
 * Google Apps Script製の実績報告フォーム。
 *
 * 想定シート構成:
 *   - 「回答ログ」シート: フォームから送信された実績データ
 *       A列: タイムスタンプ
 *       B列: スタッフ名
 *       C列: 獲得項目（カンマ区切り）
 *       D列: 金額
 *       E列: 追加商材A（件数）
 *       F列: 追加商材B（件数）
 *       G列: 報告者（送信者のGoogleアカウント、監査用）
 *
 * STAFF_LIST / ITEM_LIST を書き換えれば、業種を問わず流用できる。
 */

// ===== マスタ定義（フォーム側の値と必ず一致させること） =====
const STAFF_LIST = ['スタッフA', 'スタッフB', 'スタッフC', 'スタッフD'];

const ITEM_LIST = [
  // カテゴリA
  '商品A-1', '商品A-2', '商品A-3',
  // カテゴリB
  '商品B-1', '商品B-2', '商品B-3',
  // オプション商材
  'オプション-1', 'オプション-2', 'オプション-3',
  // 施策の実施率を測る例（実施数・対象数のペア。C列側でIFERROR(実施/対象,0)のように比率を出せる）
  '施策C(実施)', '施策C(対象)',
];

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('index')
      .setTitle('実績報告フォーム')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1.0');
}

function processForm(formObject) {
  const lock = LockService.getScriptLock();
  let locked = false;
  try {
    // ---- サーバー側バリデーション（クライアントの入力は信用しない） ----
    const staff = String(formObject.staff || '').trim();
    if (STAFF_LIST.indexOf(staff) === -1) {
      return { success: false, message: 'スタッフ名が不正です。ページを再読み込みしてやり直してください。' };
    }

    let items = formObject.item || [];
    if (!Array.isArray(items)) items = [items];
    const validItems = items.filter(function(v) {
      return ITEM_LIST.indexOf(String(v)) !== -1;
    });

    // 数値は範囲内に丸める（マイナス・巨大値・文字列対策）
    const clamp = function(v, max) {
      const n = Math.floor(Number(v));
      return (isNaN(n) || n < 0) ? 0 : Math.min(n, max);
    };
    const amount = clamp(formObject.amount, 9999999);       // 金額の上限
    const countA = clamp(formObject.countA, 3);             // 1回の接客での上限件数の例
    const countB = clamp(formObject.countB, 3);

    // 空送信ガード
    if (validItems.length === 0 && amount === 0 && countA === 0 && countB === 0) {
      return { success: false, message: '獲得項目が1つも入力されていません。選択してから送信してください。' };
    }

    // 報告者の記録（監査用：スタッフ名の選び間違い・なりすまし対策）
    let reporter = '';
    try { reporter = Session.getActiveUser().getEmail(); } catch (e2) {}

    // ---- 同時送信の競合防止 ----
    lock.waitLock(10000);
    locked = true;

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName('回答ログ');
    if (!sheet) {
      sheet = ss.insertSheet('回答ログ');
      sheet.appendRow(['タイムスタンプ', 'スタッフ名', '獲得項目', '金額', '追加商材A', '追加商材B', '報告者']);
      sheet.getRange('A1:G1').setFontWeight('bold').setBackground('#f3f3f3');
    }

    sheet.appendRow([
      new Date(),
      staff,
      validItems.join(', '),
      amount,   // Number型で保存（文字列だとSUMIFSが0になる事故を防ぐ）
      countA,
      countB,
      reporter
    ]);

    return { success: true, message: staff + 'さんの実績を登録しました。お疲れ様でした！' };

  } catch (error) {
    return { success: false, message: 'エラーが発生しました: ' + error.message };
  } finally {
    if (locked) {
      try { lock.releaseLock(); } catch (e3) {}
    }
  }
}
