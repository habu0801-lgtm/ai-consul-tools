// ============================================================
// くらし×AI活用の会 — スライドデザインシステム v2
// 全スライド共通：白背景 + 上下ネイビーライン + 右上ブランド名
// ============================================================

const fs        = require("fs");
const path      = require("path");
const ICONS_DIR = path.join(__dirname, "icons");

const NAVY  = "1A3272"; // 青色（PowerPoint Dark Blue）
const TEAL  = "00897B";
const WHITE = "FFFFFF";
const LGRAY = "F5F7FA";
const MGRAY = "E5E7EB";
const DGRAY = "6B7280";
const BRAND = "くらし×AI活用の会";
const FONT  = "Meiryo";

// ブランド名は外部から上書き可能（generator.jsから setBrand() で設定）
let currentBrand = BRAND;
function setBrand(name) { currentBrand = (name !== undefined ? name : BRAND); }

// カスタムアイコン（PNG/JPGファイルパスでブランドアイコンを上書き可能）
let customIconsMap = {};
function setCustomIcons(map) { customIconsMap = map || {}; }

// PNG/JPGファイルをbase64データURLとして読み込む
function loadCustomImage(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  const ext  = path.extname(filePath).toLowerCase().replace(".", "");
  const mime = (ext === "jpg" || ext === "jpeg") ? "image/jpeg" : "image/png";
  return "data:" + mime + ";base64," + fs.readFileSync(filePath).toString("base64");
}

// スライドエリア定数（10" × 5.625"）
const TOP_TEXT_Y  = 0.06;   // ブランド名 Y
const TOP_LINE1_Y = 0.28;   // 上ライン（太） Y
const TOP_LINE1_H = 0.05;   // 上ライン（太） 高さ
const TOP_LINE2_Y = 0.34;   // 上ライン（細） Y
const TOP_LINE2_H = 0.018;  // 上ライン（細） 高さ
const BOT_LINE_Y  = 5.46;   // 下ライン（太） Y
const BOT_LINE_H  = 0.05;   // 下ライン（太） 高さ
const BOT_LINE2_Y = 5.52;   // 下ライン（細） Y
const BOT_LINE2_H = 0.018;  // 下ライン（細） 高さ
const CONTENT_Y   = 0.46;   // コンテンツ開始 Y
const CONTENT_BOT = 5.4;    // コンテンツ終了 Y
const MARGIN_X    = 0.45;   // 左右マージン

// ── SVGアイコンヘルパー ──────────────────────────────────────
// SVGを読み込み、指定カラーに変換してbase64データURLを返す
// isBrand=true: Simple Icons形式（fill属性をSVG要素に付与）
// isBrand=false: Heroicons形式（currentColor を置換）
function loadIcon(filename, hexColor, isBrand = false) {
  const fp = path.join(ICONS_DIR, filename);
  if (!fs.existsSync(fp)) return null;
  let svg = fs.readFileSync(fp, "utf8");
  if (isBrand) {
    svg = svg.replace("<svg ", `<svg fill="#${hexColor}" `);
  } else {
    svg = svg.replace(/stroke="currentColor"/g, `stroke="#${hexColor}"`);
    svg = svg.replace(/fill="currentColor"/g,   `fill="#${hexColor}"`);
  }
  return "data:image/svg+xml;base64," + Buffer.from(svg).toString("base64");
}

// ブランドロゴファイルマッピング
// PNG (アプリアイコン) はそのまま読み込む
// SVG はカラー変換してから読み込む
const BRAND_ICON = {
  "ChatGPT":          "chatgpt-app.png",
  "Claude":           "claude-app.png",
  "NotebookLM":       "notebooklm-app.png",
  "Gemini":           "gemini-app.png",
  "Perplexity":       "perplexity.svg",
  "GAS":              "gas-app.png",
  "Sheets":           "sheets-app.png",
  "Calendar":         "calendar-app.png",
  "Gmail":            "gmail-app.png",
};

// ツールアイコン取得（カスタム画像 → ブランドロゴ → Heroiconsの優先順）
function getToolIcon(toolName, hexColor) {
  if (customIconsMap[toolName]) return loadCustomImage(customIconsMap[toolName]);
  if (BRAND_ICON[toolName]) {
    const iconFile = BRAND_ICON[toolName];
    // PNGはそのまま読み込む（カラー変換不要）
    if (iconFile.endsWith(".png")) return loadCustomImage(path.join(ICONS_DIR, iconFile));
    // SVGはカラー変換
    return loadIcon(iconFile, hexColor, true);
  }
  if (TOOL_ICON[toolName])  return loadIcon(TOOL_ICON[toolName],  hexColor, false);
  return null;
}

// ツール名 → Heroiconsフォールバック
const TOOL_ICON = {
  "Perplexity": "magnifying-glass.svg",
  "ChatGPT":    "chat-bubble-left-right.svg",
  "Claude":     "document-text.svg",
  "Gemini":     "sparkles.svg",
  "NotebookLM": "microphone.svg",
};

// カテゴリ → アイコンファイルマッピング
const CATEGORY_ICON = {
  "Tool Guide": "wrench-screwdriver.svg",
  "Workflow":   "arrows-right-left.svg",
  "Minutes":    "microphone.svg",
  "Slides":     "presentation-chart-bar.svg",
};

// ── 全スライド共通ブランディングフレーム ─────────────────────
function addBranding(pres, slide) {
  slide.background = { color: WHITE };

  // ブランド名（右上）※空文字なら非表示
  if (currentBrand) {
    slide.addText(currentBrand, {
      x: 5.8, y: TOP_TEXT_Y, w: 4.1, h: 0.22,
      fontSize: 13, color: NAVY, bold: true, fontFace: FONT,
      align: "right", valign: "middle", margin: 0
    });
  }

  // 上ライン（太）
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: TOP_LINE1_Y, w: 10, h: TOP_LINE1_H,
    fill: { color: NAVY }, line: { color: NAVY }
  });

  // 上ライン（細）
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: TOP_LINE2_Y, w: 10, h: TOP_LINE2_H,
    fill: { color: NAVY }, line: { color: NAVY }
  });

  // 下ライン（太）
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: BOT_LINE_Y, w: 10, h: BOT_LINE_H,
    fill: { color: NAVY }, line: { color: NAVY }
  });

  // 下ライン（細）
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: BOT_LINE2_Y, w: 10, h: BOT_LINE2_H,
    fill: { color: NAVY }, line: { color: NAVY }
  });
}

// ── 1. 表紙スライド ─────────────────────────────────────────
// 白ベース。タイトルを大きく中央配置。左にティールのアクセントライン。
function addTitleSlide(pres, { title, subtitle, date, speaker }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // メインタイトル
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.2, w: 9.2, h: 2.0,
    fontSize: 40, color: NAVY, bold: true, fontFace: FONT,
    valign: "middle", margin: 0
  });

  // サブタイトル
  if (subtitle) {
    s.addText(subtitle, {
      x: MARGIN_X, y: CONTENT_Y + 2.25, w: 9.2, h: 0.45,
      fontSize: 15, color: DGRAY, bold: false, fontFace: FONT, margin: 0
    });
  }

  // 区切り線
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 2.82, w: 6.0, h: 0.02,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  // 日付・主催
  const info = [date, speaker].filter(Boolean).join("　");
  if (info) {
    s.addText(info, {
      x: MARGIN_X, y: CONTENT_Y + 2.95, w: 9.2, h: 0.3,
      fontSize: 11, color: DGRAY, bold: false, fontFace: FONT, margin: 0
    });
  }
  return s;
}

// ── 2. 自己紹介スライド ───────────────────────────────────────
// selfIntro: { name, furigana, bio[], photo, contact }
// 表紙の直後に自動挿入される。selfIntro フィールドがない場合はスキップ。
// デザイン：ネイビー背景・名前大・ふりがな・ティール区切り線・箇条書き・右に顔写真
function addSelfIntroSlide(pres, { name, furigana, bio, photo, contact }) {
  const s = pres.addSlide();

  // ネイビー背景（全面）
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: NAVY }, line: { color: NAVY }
  });

  const leftX  = 0.55;
  const leftW  = 5.4;
  const photoW = 3.4;
  const photoH = 3.4;
  const photoX = 6.2;
  const photoY = (5.625 - photoH) / 2;  // 垂直中央

  // ── 左エリア ──

  // 名前
  s.addText(name || "", {
    x: leftX, y: 0.55, w: leftW, h: 0.70,
    fontSize: 38, color: WHITE, bold: true, fontFace: FONT,
    valign: "middle", margin: 0
  });

  // ふりがな
  if (furigana) {
    s.addText(furigana, {
      x: leftX, y: 1.28, w: leftW, h: 0.28,
      fontSize: 12, color: "A0AEC0", fontFace: FONT,
      valign: "middle", margin: 0
    });
  }

  // ティール区切り線
  const lineY = furigana ? 1.62 : 1.32;
  s.addShape(pres.ShapeType.rect, {
    x: leftX, y: lineY, w: leftW, h: 0.045,
    fill: { color: TEAL }, line: { color: TEAL }
  });

  // 箇条書き（ティール ▶ マーカー付き）
  const bioArr    = Array.isArray(bio) ? bio : (bio ? [bio] : []);
  const arrowIco  = loadIcon("chevron-right.svg", TEAL);
  const bioStartY = lineY + 0.18;
  const bioRowH   = 0.50;
  bioArr.forEach((line, i) => {
    const by = bioStartY + i * bioRowH;
    if (arrowIco) {
      s.addImage({ data: arrowIco, x: leftX, y: by + 0.10, w: 0.20, h: 0.20 });
    }
    s.addText(line, {
      x: leftX + 0.28, y: by, w: leftW - 0.28, h: bioRowH,
      fontSize: 12, color: WHITE, fontFace: FONT,
      valign: "middle", margin: 0
    });
  });

  // SNS / 連絡先
  if (contact) {
    const contactY = bioStartY + bioArr.length * bioRowH + 0.12;
    s.addText(contact, {
      x: leftX, y: contactY, w: leftW, h: 0.28,
      fontSize: 10, color: "A0AEC0", fontFace: FONT,
      valign: "middle", margin: 0
    });
  }

  // ── 右エリア：顔写真 ──
  if (photo && fs.existsSync(photo)) {
    const ext  = path.extname(photo).toLowerCase().replace(".", "");
    const mime = ext === "jpg" || ext === "jpeg" ? "image/jpeg" : "image/png";
    const data = "data:" + mime + ";base64," + fs.readFileSync(photo).toString("base64");
    // 丸枠の背景（薄いティール）
    s.addShape(pres.ShapeType.ellipse, {
      x: photoX - 0.06, y: photoY - 0.06, w: photoW + 0.12, h: photoH + 0.12,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addImage({ data, x: photoX, y: photoY, w: photoW, h: photoH,
      rounding: true
    });
  }

  return s;
}

// ── 3. 目次・アジェンダスライド ──────────────────────────────
function addAgendaSlide(pres, { title, items }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // スライドタイトル
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.48,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });

  // タイトル下ライン
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.5, w: 9.1, h: 0.025,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  // アジェンダ項目
  const startY = CONTENT_Y + 0.6;
  const avail  = CONTENT_BOT - startY - 0.1;
  const rowH   = avail / Math.max(items.length, 1);

  items.forEach((item, i) => {
    const y = startY + i * rowH;

    // 番号バッジ（ティール）
    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: y + 0.05, w: 0.36, h: 0.36,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(String(i + 1).padStart(2, "0"), {
      x: MARGIN_X, y: y + 0.05, w: 0.36, h: 0.36,
      fontSize: 11, color: WHITE, bold: true, fontFace: "Arial",
      align: "center", valign: "middle", margin: 0
    });

    // ラベル
    s.addText(item.label, {
      x: MARGIN_X + 0.46, y: y + 0.02, w: 7.0, h: 0.28,
      fontSize: 14, color: NAVY, bold: true, fontFace: FONT, margin: 0
    });

    // 時間（右端）
    if (item.time) {
      s.addText(item.time, {
        x: 8.2, y: y + 0.02, w: 1.5, h: 0.28,
        fontSize: 12, color: TEAL, bold: false, fontFace: FONT,
        align: "right", margin: 0
      });
    }

    // サブテキスト
    if (item.sub) {
      s.addText(item.sub, {
        x: MARGIN_X + 0.46, y: y + 0.3, w: 8.5, h: 0.2,
        fontSize: 10, color: DGRAY, bold: false, fontFace: FONT, margin: 0
      });
    }
  });
  return s;
}

// ── 3. セクション区切りスライド ──────────────────────────────
// 白ベース。左にティールの縦帯、大きな番号、タイトル。
// icons: ツール名の配列を指定するとカテゴリアイコンの代わりにブランドロゴを表示
function addSectionSlide(pres, { num, category, title, subtitle, icons }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // セクション番号（大）
  s.addText(num, {
    x: MARGIN_X, y: CONTENT_Y + 0.05, w: 2.0, h: 1.2,
    fontSize: 72, color: MGRAY, bold: true, fontFace: "Arial",
    valign: "middle", margin: 0
  });

  // カテゴリラベル
  s.addText(category, {
    x: MARGIN_X, y: CONTENT_Y + 1.2, w: 9.2, h: 0.28,
    fontSize: 11, color: TEAL, bold: true, fontFace: FONT,
    charSpacing: 2, margin: 0
  });

  // タイトル
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 1.5, w: 9.2, h: 1.1,
    fontSize: 28, color: NAVY, bold: true, fontFace: FONT,
    valign: "top", margin: 0
  });

  // カテゴリアイコン or カスタムアイコン（右側に大きく）
  if (icons && icons.length > 0) {
    // ツール名配列が指定された場合：ブランドロゴを表示
    const iconSz  = icons.length > 1 ? 0.95 : 1.8;
    const gapX    = 0.20;
    const totalIconW = icons.length * iconSz + (icons.length - 1) * gapX;
    const startX  = 9.6 - totalIconW;
    icons.forEach((toolName, idx) => {
      const iconData = getToolIcon(toolName, MGRAY);
      if (iconData) {
        s.addImage({ data: iconData,
          x: startX + idx * (iconSz + gapX),
          y: CONTENT_Y + 0.45,
          w: iconSz, h: iconSz
        });
      }
    });
  } else {
    // カテゴリマッピングからHeroiconsを表示
    const catIconFile = CATEGORY_ICON[category];
    if (catIconFile) {
      const iconData = loadIcon(catIconFile, MGRAY);
      if (iconData) {
        s.addImage({ data: iconData, x: 7.6, y: CONTENT_Y + 0.2, w: 1.8, h: 1.8 });
      }
    }
  }

  // サブタイトル
  if (subtitle) {
    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: CONTENT_Y + 2.72, w: 4.0, h: 0.025,
      fill: { color: MGRAY }, line: { color: MGRAY }
    });
    s.addText(subtitle, {
      x: MARGIN_X, y: CONTENT_Y + 2.82, w: 9.2, h: 0.45,
      fontSize: 12, color: DGRAY, bold: false, fontFace: FONT, margin: 0
    });
  }
  return s;
}

// ── 4. コンテンツスライド（箇条書き） ─────────────────────────
function addContentSlide(pres, { num, category, title, bullets, note }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // カテゴリラベル（スライド番号付き）
  s.addText(`${num}　${category}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
    fontSize: 10, color: TEAL, bold: true, fontFace: FONT,
    charSpacing: 1, margin: 0
  });

  // タイトル
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.48,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });

  // タイトル下ライン
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.73, w: 9.1, h: 0.025,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  // 箇条書き
  const bStart = CONTENT_Y + 0.82;
  const bEnd   = note ? CONTENT_BOT - 0.38 : CONTENT_BOT - 0.05;
  const bAvail = bEnd - bStart;
  const bList  = bullets.map(b => typeof b === "string" ? { text: b, sub: null } : b);
  const rowH   = bAvail / Math.max(bList.length, 1);

  const bulletIcon = loadIcon("chevron-right.svg", TEAL);

  bList.forEach((b, i) => {
    const y = bStart + i * rowH;

    // 先頭アイコン判定:
    //   b.icon が ".svg" で終わる → Heroicons（loadIcon 直接）
    //   b.icon がツール名        → getToolIcon（ブランドロゴ優先）
    //   b.icon なし              → chevron
    const isSvgIcon  = b.icon && b.icon.endsWith(".svg");
    const isToolName = b.icon && !isSvgIcon;

    let lineIcon;
    if (isToolName)   lineIcon = getToolIcon(b.icon, NAVY);
    else if (isSvgIcon) lineIcon = loadIcon(b.icon, TEAL);
    else                lineIcon = bulletIcon;

    const iconSz = (isToolName && lineIcon) ? 0.30 : (isSvgIcon ? 0.26 : 0.22);
    const iconY  = y + (rowH - iconSz) / 2;

    if (lineIcon) {
      s.addImage({ data: lineIcon, x: MARGIN_X - 0.02, y: iconY, w: iconSz, h: iconSz });
    } else {
      s.addShape(pres.ShapeType.rect, {
        x: MARGIN_X, y: y + (rowH * 0.18), w: 0.07, h: 0.07,
        fill: { color: TEAL }, line: { color: TEAL }
      });
    }

    // テキストオフセット（アイコン幅に合わせる）
    const textOff = (isToolName && lineIcon) ? 0.40 : (isSvgIcon ? 0.34 : 0.24);
    s.addText(b.text, {
      x: MARGIN_X + textOff, y: y, w: 9.1 - textOff, h: rowH * (b.sub ? 0.52 : 0.9),
      fontSize: 16, color: NAVY, bold: false, fontFace: FONT,
      valign: "middle", margin: 0
    });

    // サブテキスト
    if (b.sub) {
      s.addText(b.sub, {
        x: MARGIN_X + textOff, y: y + rowH * 0.5, w: 9.1 - textOff, h: rowH * 0.44,
        fontSize: 10.5, color: DGRAY, bold: false, fontFace: FONT,
        valign: "middle", margin: 0
      });
    }
  });

  // フッターノート（ティール）
  if (note) {
    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: CONTENT_BOT - 0.32, w: 9.1, h: 0.02,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(note, {
      x: MARGIN_X, y: CONTENT_BOT - 0.28, w: 9.1, h: 0.26,
      fontSize: 11, color: TEAL, bold: false, fontFace: FONT, margin: 0
    });
  }
  return s;
}

// ── 5. 2カラムスライド ─────────────────────────────────────
function addTwoColumnSlide(pres, { num, category, title, left, right }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // カテゴリ + タイトル
  s.addText(`${num}　${category}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
    fontSize: 10, color: TEAL, bold: true, fontFace: FONT, charSpacing: 1, margin: 0
  });
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.48,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.73, w: 9.1, h: 0.025,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  const colY    = CONTENT_Y + 0.84;
  const headH   = 0.48;  // ヘッダー帯の高さ
  const lineH   = 0.54;  // 1行の高さ
  const padV    = 0.18;  // 上下内部パディング
  const colW    = 4.45;
  const rightX  = MARGIN_X + colW + 0.2;
  const rightW  = 9.55 - MARGIN_X - colW - 0.2;

  // 行をパース（\n 区切り → 配列）
  const parseLines = (body) => (body || "").split("\n").filter(l => l.trim());
  const leftLines  = parseLines(left.body);
  const rightLines = parseLines(right.body);
  const maxLines   = Math.max(leftLines.length, rightLines.length);

  // カラム高さをコンテンツに合わせる（最大 CONTENT_BOT まで）
  const colH = Math.min(headH + padV + maxLines * lineH + padV, CONTENT_BOT - colY);

  // カラム描画ヘルパー
  function renderCol(cx, cw, header, lines, headerColor, markOkColor, bgColor) {
    // カード背景
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: colY, w: cw, h: colH,
      fill: { color: bgColor }, line: { color: headerColor, pt: 1.2 }
    });
    // ヘッダー帯
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: colY, w: cw, h: headH,
      fill: { color: headerColor }, line: { color: headerColor }
    });
    s.addText(header, {
      x: cx + 0.14, y: colY, w: cw - 0.2, h: headH,
      fontSize: 13.5, color: WHITE, bold: true, fontFace: FONT,
      valign: "middle", margin: 0
    });

    // 各行を個別描画
    lines.forEach((line, i) => {
      const ly   = colY + headH + padV + i * lineH;
      const mark = line.startsWith("✗") ? "✗"
                 : line.startsWith("✓") ? "✓" : "•";
      const text = line.replace(/^[✗✓•]\s*/, "").trim();
      const markColor = mark === "✓" ? markOkColor
                      : mark === "✗" ? "9CAAB8" : markOkColor;

      // 記号（大きめ・色付き）
      s.addText(mark, {
        x: cx + 0.14, y: ly, w: 0.3, h: lineH,
        fontSize: 16, color: markColor, bold: true, fontFace: "Arial",
        align: "center", valign: "middle", margin: 0
      });
      // テキスト
      s.addText(text, {
        x: cx + 0.46, y: ly, w: cw - 0.58, h: lineH,
        fontSize: 14, color: "2D3748", bold: false, fontFace: FONT,
        valign: "middle", margin: 0
      });
    });
  }

  renderCol(MARGIN_X, colW,   left.header,  leftLines,  NAVY, NAVY,  "EEF2F7");
  renderCol(rightX,   rightW, right.header, rightLines, TEAL, TEAL,  "E8F5F3");

  return s;
}

// ── 6. 表スライド ─────────────────────────────────────────
function addTableSlide(pres, { num, category, title, headers, rows }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  s.addText(`${num}　${category}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
    fontSize: 10, color: TEAL, bold: true, fontFace: FONT, charSpacing: 1, margin: 0
  });
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.48,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });

  const totalW = 9.1;
  const colW   = totalW / headers.length;

  const tableD = [
    headers.map(h => ({
      text: h,
      options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "center", valign: "middle", fontSize: 11, fontFace: FONT }
    })),
    ...rows.map((row, ri) =>
      row.map(cell => ({
        text: cell,
        options: { fill: { color: ri % 2 === 0 ? "F0F4F8" : WHITE }, valign: "middle", fontSize: 10, fontFace: FONT, color: NAVY }
      }))
    )
  ];

  s.addTable(tableD, {
    x: MARGIN_X, y: CONTENT_Y + 0.8, w: totalW,
    colW: headers.map(() => colW),
    border: { pt: 0.5, color: "CCCCCC" }
  });
  return s;
}

// ── 7. まとめスライド ─────────────────────────────────────
// 全スライド一貫して白ベース。ティールのアクセントでポイントを強調。
function addSummarySlide(pres, { title, points, closing }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // タイトル
  s.addText(title || "まとめ", {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.48,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.5, w: 9.1, h: 0.025,
    fill: { color: TEAL }, line: { color: TEAL }
  });

  // ── 2×2 カードグリッド（pointsがオブジェクト配列の場合） ──
  const isCards = points.length > 0 && typeof points[0] === "object";

  if (isCards) {
    const gridStartY = CONTENT_Y + 0.62;
    const gridEndY   = closing ? CONTENT_BOT - 0.56 : CONTENT_BOT - 0.05;
    const gridH      = gridEndY - gridStartY;
    const rowGap     = 0.12;
    const colGap     = 0.15;
    const cols       = 2;
    const rows       = Math.ceil(points.length / cols);
    const cardW      = (9.1 - colGap * (cols - 1)) / cols;       // ~4.475"
    const cardH      = (gridH - rowGap * (rows - 1)) / rows;     // ~1.85"

    points.forEach((pt, i) => {
      const col  = i % cols;
      const row  = Math.floor(i / cols);
      const cx   = MARGIN_X + col * (cardW + colGap);
      const cy   = gridStartY + row * (cardH + rowGap);

      // カード背景
      s.addShape(pres.ShapeType.rect, {
        x: cx, y: cy, w: cardW, h: cardH,
        fill: { color: LGRAY }, line: { color: MGRAY, pt: 1 }
      });
      // 左アクセントバー（ティール）
      s.addShape(pres.ShapeType.rect, {
        x: cx, y: cy, w: 0.06, h: cardH,
        fill: { color: TEAL }, line: { color: TEAL }
      });

      // カテゴリアイコン（大）
      const catIcon = pt.icon ? loadIcon(pt.icon, TEAL) : null;
      if (catIcon) {
        s.addImage({ data: catIcon, x: cx + 0.16, y: cy + 0.16, w: 0.38, h: 0.38 });
      }

      // ラベル（太字）
      s.addText(pt.label, {
        x: cx + 0.65, y: cy + 0.14, w: cardW - 0.75, h: 0.42,
        fontSize: 17, color: NAVY, bold: true, fontFace: FONT,
        valign: "middle", margin: 0
      });

      // 説明テキスト
      s.addText(pt.desc || "", {
        x: cx + 0.16, y: cy + 0.60, w: cardW - 0.24, h: 0.38,
        fontSize: 10, color: DGRAY, fontFace: FONT, valign: "top", margin: 0
      });

      // ブランドロゴ行（カード下部）
      const logoSize = 0.30;
      const logoGap  = 0.10;
      const tools    = pt.tools || [];
      const logoRowY = cy + cardH - logoSize - 0.18;
      tools.forEach((toolName, ti) => {
        const lx = cx + 0.16 + ti * (logoSize + logoGap);
        const ico = getToolIcon(toolName, NAVY);
        if (ico) {
          s.addImage({ data: ico, x: lx, y: logoRowY, w: logoSize, h: logoSize });
        }
      });
    });

  } else {
    // フォールバック：旧来のシンプルリスト（文字列配列）
    const pStart = CONTENT_Y + 0.6;
    const pEnd   = closing ? CONTENT_BOT - 0.52 : CONTENT_BOT - 0.05;
    const pAvail = pEnd - pStart;
    const rowH   = pAvail / Math.max(points.length, 1);
    const checkIcon = loadIcon("check-circle.svg", TEAL);

    points.forEach((pt, i) => {
      const y = pStart + i * rowH;
      if (checkIcon) {
        s.addImage({ data: checkIcon, x: MARGIN_X, y: y + (rowH * 0.1), w: 0.32, h: 0.32 });
      }
      s.addText(String(pt), {
        x: MARGIN_X + 0.44, y: y, w: 9.0, h: rowH,
        fontSize: 14, color: NAVY, fontFace: FONT, valign: "middle", margin: 0
      });
    });
  }

  // クロージングメッセージ（ティール帯）
  if (closing) {
    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: CONTENT_BOT - 0.48, w: 9.1, h: 0.44,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(closing, {
      x: MARGIN_X, y: CONTENT_BOT - 0.48, w: 9.1, h: 0.44,
      fontSize: 14, color: WHITE, bold: true, fontFace: FONT,
      align: "center", valign: "middle", margin: 0
    });
  }
  return s;
}

// ── 8. プロンプトボックススライド ────────────────────────────────
// AIへの指示文をコピー可能なボックス形式で見せるスライド
function addPromptBoxesSlide(pres, { num, category, title, prompts, note }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // カテゴリ + タイトル
  s.addText(`${num}　${category}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
    fontSize: 10, color: TEAL, bold: true, fontFace: FONT, charSpacing: 1, margin: 0
  });
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.45,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.7, w: 9.1, h: 0.022,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  const boxX    = MARGIN_X;
  const boxW    = 9.1;
  const headH   = 0.44;
  const gapY    = 0.22;
  const headerColors = [TEAL, NAVY];

  // 各プロンプトの高さを行数で比例配分
  const lineHeights = prompts.map(p => (p.text.split("\n").length + 1));
  const totalLines  = lineHeights.reduce((a, b) => a + b, 0);
  const gapTotal    = gapY * (prompts.length - 1);

  // シングルプロンプトの場合はボックス高さを制限して下部余白をノートに活用
  const isOnePrompt = (prompts.length === 1);
  const maxBoxBodyH = isOnePrompt ? 1.6 : 9999;  // 1プロンプト時は最大1.6"
  const totalH  = CONTENT_BOT - (CONTENT_Y + 0.82);
  const bodyPool = totalH - headH * prompts.length - gapTotal;

  let curY = CONTENT_Y + 0.82;

  prompts.forEach((p, i) => {
    const rawBodyH = (lineHeights[i] / totalLines) * bodyPool;
    const bodyH   = Math.min(rawBodyH, maxBoxBodyH);
    const boxH    = headH + bodyH;
    const hColor  = headerColors[i % headerColors.length];
    const iconData = getToolIcon(p.tool, WHITE);

    // ボックス外枠（薄い背景）
    s.addShape(pres.ShapeType.rect, {
      x: boxX, y: curY, w: boxW, h: boxH,
      fill: { color: "F8FAFC" }, line: { color: hColor, pt: 1.2 }
    });

    // ヘッダー帯
    s.addShape(pres.ShapeType.rect, {
      x: boxX, y: curY, w: boxW, h: headH,
      fill: { color: hColor }, line: { color: hColor }
    });

    // ヘッダー: ツールアイコン
    if (iconData) {
      s.addImage({ data: iconData, x: boxX + 0.16, y: curY + (headH - 0.28) / 2, w: 0.28, h: 0.28 });
    }

    // ヘッダー: ステップラベル
    s.addText(p.step || `${i + 1}回目の指示`, {
      x: boxX + (iconData ? 0.52 : 0.18), y: curY, w: boxW - 0.6, h: headH,
      fontSize: 14, color: WHITE, bold: true, fontFace: FONT,
      valign: "middle", margin: 0
    });

    // プロンプト本文（コード感のある表示）
    s.addText(`「${p.text}」`, {
      x: boxX + 0.22, y: curY + headH + 0.12, w: boxW - 0.44, h: bodyH - 0.2,
      fontSize: 14, color: "2D3748", bold: false, fontFace: FONT,
      valign: "top", margin: 0
    });

    curY += boxH + gapY;
  });

  // フッターノート（余白に応じてフォントサイズを動的に決定）
  if (note) {
    const noteStartY  = curY + 0.04;          // 最後のボックスの直後
    const noteAvailH  = CONTENT_BOT - noteStartY - 0.05;
    // 余白が多いほど大きいフォント
    const noteFontSz  = noteAvailH > 1.4 ? 22
                      : noteAvailH > 1.0 ? 18
                      : noteAvailH > 0.7 ? 15
                      : noteAvailH > 0.5 ? 13
                      : 11;
    const noteBold    = noteAvailH > 0.6;

    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: noteStartY, w: 9.1, h: 0.022,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(note, {
      x: MARGIN_X, y: noteStartY + 0.08, w: 9.1, h: noteAvailH - 0.1,
      fontSize: noteFontSz, color: TEAL, bold: noteBold, fontFace: FONT,
      align: "center", valign: "middle", margin: 0
    });
  }
  return s;
}

// ── 9. 画像スライド ────────────────────────────────────────────
// PNGヘッダーから画像サイズを読み取る
function getPngSize(filePath) {
  try {
    const buf = fs.readFileSync(filePath);
    // PNG: magic bytes + IHDR chunk, width@16, height@20
    if (buf[0] === 0x89 && buf[1] === 0x50) {
      return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
    }
  } catch (e) {}
  return null;
}

// 画像をアスペクト比維持・中央配置でスライドに追加
// imageScale: 1未満で縮小（省略時は領域いっぱいにfit）。縦長の画像で余白が潰れるときに使う
function addImageSlide(pres, { num, category, title, imagePath, caption, imageScale }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // タイトル（省略可）
  if (title) {
    s.addText(`${num}　${category}`, {
      x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
      fontSize: 10, color: TEAL, bold: true, fontFace: FONT, charSpacing: 1, margin: 0
    });
    s.addText(title, {
      x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.45,
      fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
    });
  }

  // 使用できる領域
  const areaX = MARGIN_X;
  const areaY = title ? CONTENT_Y + 0.75 : CONTENT_Y + 0.1;
  const areaW = 9.1;
  const areaH = caption ? CONTENT_BOT - areaY - 0.42 : CONTENT_BOT - areaY - 0.05;

  if (imagePath && fs.existsSync(imagePath)) {
    // アスペクト比を維持してfitサイズを計算
    const dim = getPngSize(imagePath);
    let imgW = areaW;
    let imgH = areaH;
    if (dim && dim.w && dim.h) {
      const ratio = dim.w / dim.h;
      if (areaW / areaH > ratio) {
        // 高さ基準
        imgH = areaH;
        imgW = areaH * ratio;
      } else {
        // 幅基準
        imgW = areaW;
        imgH = areaW / ratio;
      }
    }
    // 縮小指定（省略時は等倍）
    const scale = (typeof imageScale === "number" && imageScale > 0) ? imageScale : 1;
    imgW *= scale;
    imgH *= scale;
    // 中央配置
    const imgX = areaX + (areaW - imgW) / 2;
    const imgY = areaY + (areaH - imgH) / 2;
    s.addImage({ path: imagePath, x: imgX, y: imgY, w: imgW, h: imgH });
  } else {
    s.addShape(pres.ShapeType.rect, {
      x: areaX, y: areaY, w: areaW, h: areaH,
      fill: { color: LGRAY }, line: { color: MGRAY }
    });
    s.addText("画像が見つかりません:\n" + imagePath, {
      x: areaX, y: areaY, w: areaW, h: areaH,
      fontSize: 11, color: DGRAY, align: "center", valign: "middle", margin: 0
    });
  }

  // キャプション
  if (caption) {
    s.addText(caption, {
      x: MARGIN_X, y: CONTENT_BOT - 0.36, w: 9.1, h: 0.28,
      fontSize: 10, color: TEAL, bold: false, fontFace: FONT, margin: 0
    });
  }
  return s;
}

// ── 9. ツールカードスライド（2×2グリッド）──────────────────────
function addToolCardsSlide(pres, { num, category, title, tools }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // カテゴリ + タイトル
  s.addText(`${num}　${category}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
    fontSize: 10, color: TEAL, bold: true, fontFace: FONT, charSpacing: 1, margin: 0
  });
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.45,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.7, w: 9.1, h: 0.022,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  // 2×2 カードグリッド
  const gridY  = CONTENT_Y + 0.82;
  const cols   = 2;
  const rows   = Math.ceil(tools.length / cols);
  const gapX   = 0.22;
  const gapY   = 0.18;
  const cardW  = (9.1 - gapX * (cols - 1)) / cols;  // ~4.44"
  const cardH  = (CONTENT_BOT - gridY - gapY * (rows - 1)) / rows;
  const iconSz = 0.48;
  const accW   = 0.07; // 左アクセントバー幅

  tools.forEach((tool, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const cx  = MARGIN_X + col * (cardW + gapX);
    const cy  = gridY + row * (cardH + gapY);

    // カード背景（薄グレー・ネイビーボーダー）
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: cy, w: cardW, h: cardH,
      fill: { color: LGRAY }, line: { color: MGRAY, pt: 1 }
    });

    // 左アクセントバー（ティール）
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: cy, w: accW, h: cardH,
      fill: { color: TEAL }, line: { color: TEAL }
    });

    // ブランドアイコン（左寄せ・縦中央）
    const iconData = getToolIcon(tool.name, NAVY);
    const iconX    = cx + accW + 0.18;
    const iconY    = cy + (cardH - iconSz) / 2;
    if (iconData) {
      s.addImage({ data: iconData, x: iconX, y: iconY, w: iconSz, h: iconSz });
    }

    // テキストエリア
    const textX = iconX + iconSz + 0.18;
    const textW = cardW - accW - 0.18 - iconSz - 0.18 - 0.1;

    // ツール名
    s.addText(tool.name, {
      x: textX, y: cy + 0.14, w: textW, h: 0.38,
      fontSize: 16, color: NAVY, bold: true, fontFace: FONT, valign: "middle", margin: 0
    });

    // 使い所タグ（ティール枠線）
    if (tool.tag) {
      const tagW = Math.min(textW, 1.8);
      s.addShape(pres.ShapeType.rect, {
        x: textX, y: cy + 0.56, w: tagW, h: 0.26,
        fill: { color: "E8F5F3" }, line: { color: TEAL, pt: 0.8 }
      });
      s.addText(tool.tag, {
        x: textX, y: cy + 0.56, w: tagW, h: 0.26,
        fontSize: 9, color: TEAL, bold: true, fontFace: FONT,
        align: "center", valign: "middle", margin: 0
      });
    }

    // 説明文
    const descY = cy + (tool.tag ? 0.88 : 0.58);
    s.addText(tool.desc, {
      x: textX, y: descY, w: textW, h: cy + cardH - descY - 0.1,
      fontSize: 11, color: DGRAY, bold: false, fontFace: FONT,
      valign: "top", margin: 0
    });
  });

  return s;
}

// ── 9. フロー図スライド ────────────────────────────────────
// ステップボックスを横に並べ、矢印で繋ぐ図解スライド
function addFlowSlide(pres, { num, category, title, steps, note }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // カテゴリ + タイトル
  s.addText(`${num}　${category}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.2, h: 0.22,
    fontSize: 10, color: TEAL, bold: true, fontFace: FONT, charSpacing: 1, margin: 0
  });
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.23, w: 9.2, h: 0.45,
    fontSize: 22, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });
  s.addShape(pres.ShapeType.rect, {
    x: MARGIN_X, y: CONTENT_Y + 0.7, w: 9.1, h: 0.022,
    fill: { color: MGRAY }, line: { color: MGRAY }
  });

  // ボックスレイアウト計算
  const n      = steps.length;
  const arrowW = 0.5;
  const totalW = 9.1;
  const boxW   = (totalW - arrowW * (n - 1)) / n;
  const boxY   = CONTENT_Y + 0.82;
  const boxH   = 2.6;  // アイコン込みの高さ
  const headH  = 0.72; // ヘッダー帯の高さ

  steps.forEach((step, i) => {
    const x = MARGIN_X + i * (boxW + arrowW);

    // ボックス本体（薄グレー背景 + ネイビーボーダー）
    s.addShape(pres.ShapeType.rect, {
      x, y: boxY, w: boxW, h: boxH,
      fill: { color: "F0F4FB" }, line: { color: NAVY, pt: 0.8 }
    });

    // ヘッダー帯（ネイビー）
    s.addShape(pres.ShapeType.rect, {
      x, y: boxY, w: boxW, h: headH,
      fill: { color: NAVY }, line: { color: NAVY }
    });

    // STEPラベル（ティール、小さく）
    s.addText(`STEP  ${String(i + 1).padStart(2, "0")}`, {
      x: x + 0.08, y: boxY + 0.05, w: boxW - 0.12, h: 0.22,
      fontSize: 9, color: "5BB8A8", bold: true, fontFace: "Arial",
      align: "center", margin: 0
    });

    // ツール名（白・大きく）
    s.addText(step.tool, {
      x: x + 0.06, y: boxY + 0.26, w: boxW - 0.1, h: 0.4,
      fontSize: 17, color: WHITE, bold: true, fontFace: FONT,
      align: "center", valign: "middle", margin: 0
    });

    // ツールアイコン（ボックス本体上部、中央）ブランドロゴ優先
    const toolIconData = getToolIcon(step.tool, TEAL);
    if (toolIconData) {
      const iconSize = 0.38;
      s.addImage({ data: toolIconData, x: x + (boxW - iconSize) / 2, y: boxY + headH + 0.1, w: iconSize, h: iconSize });
    }

    // アクションラベル（ティール・太字）
    s.addText(step.action || "", {
      x: x + 0.06, y: boxY + headH + (toolIconData ? 0.52 : 0.1), w: boxW - 0.1, h: 0.30,
      fontSize: 13, color: TEAL, bold: true, fontFace: FONT,
      align: "center", margin: 0
    });

    // 説明文
    s.addText(step.desc || step.description || "", {
      x: x + 0.1, y: boxY + headH + (toolIconData ? 0.86 : 0.44), w: boxW - 0.18, h: boxH - headH - (toolIconData ? 0.92 : 0.5),
      fontSize: 12, color: "374151", bold: false, fontFace: FONT,
      align: "left", valign: "top", margin: 0
    });

    // 矢印（最後のボックス以外）
    if (i < n - 1) {
      const arrowX    = x + boxW;
      const arrowMidY = boxY + boxH / 2;
      s.addText("→", {
        x: arrowX, y: arrowMidY - 0.22, w: arrowW, h: 0.44,
        fontSize: 26, color: TEAL, bold: true, fontFace: "Arial",
        align: "center", valign: "middle", margin: 0
      });
    }
  });

  // フッターノート（ボックス下に配置）
  if (note) {
    const noteY = boxY + boxH + 0.18;
    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: noteY - 0.06, w: 9.1, h: 0.02,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(note, {
      x: MARGIN_X, y: noteY, w: 9.1, h: 0.28,
      fontSize: 10, color: TEAL, bold: false, fontFace: FONT, margin: 0
    });
  }
  return s;
}

// ── 10. ステップスライド ─────────────────────────────────────
// 画像なしで操作フローを番号付きカードで表現するスライド
// steps: [{ num, title, desc, icon, tool }] ← icon はHeroicons名、tool はツール名
function addStepsSlide(pres, { num, category, title, steps, note }) {
  const s = pres.addSlide();
  addBranding(pres, s);

  // カテゴリ + タイトル
  s.addText(`${num || ""}　${category || ""}`, {
    x: MARGIN_X, y: CONTENT_Y, w: 9.1, h: 0.22,
    fontSize: 9, color: TEAL, bold: true, fontFace: "Arial", margin: 0
  });
  s.addText(title, {
    x: MARGIN_X, y: CONTENT_Y + 0.22, w: 9.1, h: 0.38,
    fontSize: 20, color: NAVY, bold: true, fontFace: FONT, margin: 0
  });

  const n       = steps.length;
  const noteH   = note ? 0.38 : 0;
  const arrowW  = 0.25;
  // カード枚数に応じて動的フォントサイズ設定
  const titleFontSz = n >= 4 ? 12 : (n >= 3 ? 14 : 15);
  const descFontSz  = n >= 4 ?  9 : (n >= 3 ? 11 : 12);
  const totalW  = 9.1;
  const cardW   = (totalW - arrowW * (n - 1)) / n;
  const cardStartY = CONTENT_Y + 0.72;
  const cardEndY   = note ? CONTENT_BOT - noteH - 0.14 : CONTENT_BOT - 0.1;
  const cardH      = cardEndY - cardStartY;

  steps.forEach((step, i) => {
    const cx = MARGIN_X + i * (cardW + arrowW);

    // カード背景
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: cardStartY, w: cardW, h: cardH,
      fill: { color: LGRAY }, line: { color: MGRAY, pt: 1 }
    });
    // 上部ティール帯
    s.addShape(pres.ShapeType.rect, {
      x: cx, y: cardStartY, w: cardW, h: 0.06,
      fill: { color: TEAL }, line: { color: TEAL }
    });

    // 番号バッジ
    const badgeSize = 0.36;
    const badgeX = cx + cardW / 2 - badgeSize / 2;
    const badgeY = cardStartY + 0.14;
    s.addShape(pres.ShapeType.ellipse, {
      x: badgeX, y: badgeY, w: badgeSize, h: badgeSize,
      fill: { color: TEAL }, line: { color: TEAL }
    });
    s.addText(step.num || String(i + 1).padStart(2, "0"), {
      x: badgeX, y: badgeY, w: badgeSize, h: badgeSize,
      fontSize: 11, color: WHITE, bold: true, fontFace: "Arial",
      align: "center", valign: "middle", margin: 0
    });

    // アイコン（ツールロゴ優先、次にHeroicons）
    const iconSize = 0.42;
    const iconX = cx + cardW / 2 - iconSize / 2;
    const iconY = cardStartY + 0.60;
    let ico = null;
    if (step.tool) ico = getToolIcon(step.tool, NAVY);
    if (!ico && step.icon) ico = loadIcon(step.icon, TEAL);
    if (ico) {
      s.addImage({ data: ico, x: iconX, y: iconY, w: iconSize, h: iconSize });
    }

    // ステップタイトル
    s.addText(step.title || "", {
      x: cx + 0.10, y: iconY + iconSize + 0.08, w: cardW - 0.20, h: 0.40,
      fontSize: titleFontSz, color: NAVY, bold: true, fontFace: FONT,
      align: "center", valign: "top", margin: 0
    });

    // 説明テキスト
    if (step.desc) {
      s.addText(step.desc, {
        x: cx + 0.10, y: iconY + iconSize + 0.52, w: cardW - 0.20,
        h: cardH - (iconY + iconSize + 0.52 - cardStartY) - 0.12,
        fontSize: descFontSz, color: DGRAY, fontFace: FONT,
        align: "center", valign: "top", margin: 0
      });
    }

    // 矢印（最後のカード以外）
    if (i < n - 1) {
      const arrowX = cx + cardW;
      const arrowY = cardStartY + cardH / 2 - 0.18;
      s.addText("→", {
        x: arrowX, y: arrowY, w: arrowW, h: 0.36,
        fontSize: 22, color: TEAL, bold: true, fontFace: "Arial",
        align: "center", valign: "middle", margin: 0
      });
    }
  });

  // フッターノート
  if (note) {
    const noteY = CONTENT_BOT - noteH - 0.04;
    s.addShape(pres.ShapeType.rect, {
      x: MARGIN_X, y: noteY, w: 9.1, h: noteH,
      fill: { color: LGRAY }, line: { color: MGRAY, pt: 1 }
    });
    s.addText(note, {
      x: MARGIN_X + 0.15, y: noteY, w: 8.8, h: noteH,
      fontSize: 10, color: TEAL, bold: false, fontFace: FONT,
      valign: "middle", margin: 0
    });
  }
  return s;
}

// ── エクスポート ───────────────────────────────────────────
module.exports = {
  NAVY, TEAL, WHITE, LGRAY, MGRAY, DGRAY, BRAND, FONT,
  setBrand, setCustomIcons,
  CONTENT_Y, CONTENT_BOT, MARGIN_X,
  addBranding,
  addTitleSlide,
  addSelfIntroSlide,
  addAgendaSlide,
  addSectionSlide,
  addContentSlide,
  addTwoColumnSlide,
  addTableSlide,
  addSummarySlide,
  addPromptBoxesSlide,
  addImageSlide,
  addToolCardsSlide,
  addFlowSlide,
  addStepsSlide
};
