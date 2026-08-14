#!/usr/bin/env node
// ============================================================
// くらし×AI活用の会 — スライドジェネレーター
// 使い方: node generator.js input.json [output.pptx]
// ============================================================

const pptxgen = require("pptxgenjs");
const fs      = require("fs");
const path    = require("path");
const tmpl    = require("./template");

// ── JSON 入力を読む ─────────────────────────────────────────
const inputFile  = process.argv[2];
const outputFile = process.argv[3] || "output.pptx";

if (!inputFile) {
  console.error("Usage: node generator.js input.json [output.pptx]");
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(inputFile, "utf8"));

// ブランド名の上書き（"brand": "" で非表示、省略でデフォルト）
if (data.brand !== undefined) tmpl.setBrand(data.brand);

// カスタムアイコン（PNG/JPGでブランドロゴを上書き可能）
// 例: { "Claude": "/Users/xxx/Desktop/claude-icon.png" }
if (data.customIcons) tmpl.setCustomIcons(data.customIcons);

// ── プレゼンテーション作成 ─────────────────────────────────
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10" × 5.625"

// ── スライドを順番に生成 ───────────────────────────────────
// 表紙
tmpl.addTitleSlide(pres, {
  title:    data.title,
  subtitle: data.subtitle,
  date:     data.date,
  speaker:  data.speaker
});

// 自己紹介（selfIntro フィールドがあれば表紙直後に自動挿入）
if (data.selfIntro) {
  tmpl.addSelfIntroSlide(pres, data.selfIntro);
}

// 各スライド
(data.slides || []).forEach(slide => {
  switch (slide.type) {
    case "agenda":
      tmpl.addAgendaSlide(pres, slide);
      break;
    case "section":
      tmpl.addSectionSlide(pres, slide);
      break;
    case "content":
      tmpl.addContentSlide(pres, slide);
      break;
    case "two-column":
      tmpl.addTwoColumnSlide(pres, slide);
      break;
    case "table":
      tmpl.addTableSlide(pres, slide);
      break;
    case "summary":
      tmpl.addSummarySlide(pres, slide);
      break;
    case "flow":
      tmpl.addFlowSlide(pres, slide);
      break;
    case "tool-cards":
      tmpl.addToolCardsSlide(pres, slide);
      break;
    case "image":
      tmpl.addImageSlide(pres, slide);
      break;
    case "steps":
      tmpl.addStepsSlide(pres, slide);
      break;
    case "prompt-boxes":
      tmpl.addPromptBoxesSlide(pres, slide);
      break;
    default:
      console.warn(`Unknown slide type: ${slide.type}`);
  }
});

// ── 出力 ──────────────────────────────────────────────────
pres.writeFile({ fileName: outputFile })
  .then(() => {
    const stat = fs.statSync(outputFile);
    console.log(`✓ Created: ${outputFile}`);
    console.log(`  Size: ${(stat.size / 1024).toFixed(1)} KB`);
    console.log(`  Base64 est.: ${(stat.size * 4 / 3 / 1024).toFixed(1)} KB`);
  })
  .catch(err => {
    console.error("Error:", err.message);
    process.exit(1);
  });
