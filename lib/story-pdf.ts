import { PDFDocument, PDFFont, PDFImage, PDFPage, StandardFonts, rgb } from "pdf-lib";
import { getArtBucket } from "./app-db";
import type { ArtAsset, Story } from "./types";

const PAGE_WIDTH = 432;
const PAGE_HEIGHT = 648;
const MARGIN_X = 54;
const TOP = 58;
const BOTTOM = 48;
const BODY_SIZE = 11.5;
const BODY_LEADING = 17.8;

export async function buildStoryPdf(story: Story) {
  const pdf = await PDFDocument.create();
  const bodyFont = await pdf.embedFont(StandardFonts.TimesRoman);
  const boldFont = await pdf.embedFont(StandardFonts.TimesRomanBold);
  const italicFont = await pdf.embedFont(StandardFonts.TimesRomanItalic);
  pdf.setTitle(safe(story.title));
  pdf.setAuthor(safe(story.authorSnapshot.displayName));
  pdf.setSubject("A living-fiction story compiled from kotoba-no-kaijiba");
  pdf.setCreator("kotoba-no-kaijiba");

  const readyArt = (story.art || []).filter((asset) => asset.status === "Ready" && asset.imageReference);
  const cover = readyArt.find((asset) => asset.type === "cover");
  const coverImage = cover ? await loadImage(pdf, cover).catch(() => null) : null;
  drawTitlePage(pdf.addPage([PAGE_WIDTH, PAGE_HEIGHT]), story, bodyFont, boldFont, italicFont, coverImage);

  for (const turn of story.turns || []) {
    let page = pdf.addPage([PAGE_WIDTH, PAGE_HEIGHT]);
    let y = PAGE_HEIGHT - TOP;
    page.drawText(`SECTION ${turn.turnNumber}`, { x: MARGIN_X, y, size: 8, font: boldFont, color: rgb(0.47, 0.25, 0.22) });
    y -= 27;
    const sectionArt = readyArt.find((asset) => asset.turnNumber === turn.turnNumber && asset.type !== "cover");
    if (sectionArt) {
      const image = await loadImage(pdf, sectionArt).catch(() => null);
      if (image) {
        const size = fitImage(image, PAGE_WIDTH - MARGIN_X * 2, 210);
        page.drawImage(image, { x: (PAGE_WIDTH - size.width) / 2, y: y - size.height, width: size.width, height: size.height });
        y -= size.height + 10;
        page.drawText(safe(sectionArt.caption), { x: MARGIN_X, y, size: 8.5, font: italicFont, color: rgb(0.42, 0.41, 0.37), maxWidth: PAGE_WIDTH - MARGIN_X * 2 });
        y -= 24;
      }
    }

    for (const paragraph of splitParagraphs(turn.prose)) {
      const lines = wrap(safe(paragraph), bodyFont, BODY_SIZE, PAGE_WIDTH - MARGIN_X * 2);
      for (const line of lines) {
        if (y < BOTTOM + BODY_LEADING) {
          page = pdf.addPage([PAGE_WIDTH, PAGE_HEIGHT]);
          y = PAGE_HEIGHT - TOP;
        }
        page.drawText(line, { x: MARGIN_X, y, size: BODY_SIZE, font: bodyFont, color: rgb(0.15, 0.16, 0.14) });
        y -= BODY_LEADING;
      }
      y -= 7;
    }
  }

  const pages = pdf.getPages();
  pages.forEach((page, index) => {
    if (index === 0) return;
    const label = String(index);
    page.drawText(label, { x: (PAGE_WIDTH - bodyFont.widthOfTextAtSize(label, 8)) / 2, y: 24, size: 8, font: bodyFont, color: rgb(0.48, 0.47, 0.43) });
  });
  return pdf.save();
}

function drawTitlePage(page: PDFPage, story: Story, body: PDFFont, bold: PDFFont, italic: PDFFont, image: PDFImage | null) {
  page.drawRectangle({ x: 0, y: 0, width: PAGE_WIDTH, height: PAGE_HEIGHT, color: rgb(0.96, 0.94, 0.89) });
  let y = PAGE_HEIGHT - 88;
  if (image) {
    const size = fitImage(image, PAGE_WIDTH - 108, 255);
    page.drawImage(image, { x: (PAGE_WIDTH - size.width) / 2, y: y - size.height, width: size.width, height: size.height });
    y -= size.height + 37;
  } else {
    page.drawRectangle({ x: 54, y: y - 150, width: PAGE_WIDTH - 108, height: 150, color: rgb(0.43, 0.25, 0.22) });
    page.drawText("A  L I V I N G  S T O R Y", { x: 75, y: y - 128, size: 8, font: bold, color: rgb(0.96, 0.91, 0.82) });
    y -= 190;
  }
  const titleLines = wrap(safe(story.title), bold, 28, PAGE_WIDTH - 108);
  for (const line of titleLines) { page.drawText(line, { x: 54, y, size: 28, font: bold, color: rgb(0.14, 0.15, 0.13) }); y -= 33; }
  y -= 8;
  page.drawText(`by ${safe(story.authorSnapshot.displayName)}`, { x: 54, y, size: 13, font: italic, color: rgb(0.47, 0.25, 0.22) });
  y -= 36;
  for (const line of wrap(safe(story.shortDescription), body, 10.5, PAGE_WIDTH - 108)) { page.drawText(line, { x: 54, y, size: 10.5, font: body, color: rgb(0.36, 0.36, 0.33) }); y -= 15; }
  page.drawText(`Compiled through Section ${story.latestAcceptedTurnNumber}`, { x: 54, y: 34, size: 8.5, font: body, color: rgb(0.48, 0.47, 0.43) });
}

async function loadImage(pdf: PDFDocument, asset: ArtAsset) {
  const ref = asset.imageReference || "";
  let bytes: Uint8Array;
  if (ref.startsWith("r2:")) {
    const object = await getArtBucket()?.get(ref.slice(3));
    if (!object) throw new Error("Art asset not found");
    bytes = new Uint8Array(await new Response(object.body).arrayBuffer());
  } else {
    const response = await fetch(ref, { signal: AbortSignal.timeout(10 * 60 * 1000) });
    if (!response.ok) throw new Error(`Art fetch failed (${response.status})`);
    bytes = new Uint8Array(await response.arrayBuffer());
  }
  return asset.mimeType?.includes("png") || ref.toLowerCase().endsWith(".png") ? pdf.embedPng(bytes) : pdf.embedJpg(bytes);
}

function fitImage(image: PDFImage, maxWidth: number, maxHeight: number) {
  const scale = Math.min(maxWidth / image.width, maxHeight / image.height);
  return { width: image.width * scale, height: image.height * scale };
}

function splitParagraphs(prose: string) {
  return prose.replace(/\r/g, "").split(/\n\s*\n/).map((paragraph) => paragraph.replace(/\s+/g, " ").trim()).filter(Boolean);
}

function wrap(text: string, font: PDFFont, size: number, maxWidth: number) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (font.widthOfTextAtSize(candidate, size) <= maxWidth || !line) line = candidate;
    else { lines.push(line); line = word; }
  }
  if (line) lines.push(line);
  return lines;
}

function safe(value: string) {
  return String(value || "")
    .replace(/[\u2018\u2019]/g, "'").replace(/[\u201C\u201D]/g, '"')
    .replace(/[\u2013\u2014]/g, "-").replace(/\u2026/g, "...")
    .replace(/[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]/g, "?");
}
