import { getArtBucket, getImageTransformer } from "./app-db";
import type { ArtAsset, Story } from "./types";

const PAGE_WIDTH = 432;
const PAGE_HEIGHT = 648;
const MARGIN_X = 54;
const TOP = 58;
const BOTTOM = 48;
const BODY_SIZE = 11.5;
const BODY_LEADING = 17.8;

type PreparedImage = { bytes: Uint8Array; width: number; height: number; components: number };
type PageDraft = { commands: string[]; images: Set<string> };

export async function buildStoryPdf(story: Story) {
  const readyArt = (story.art || []).filter((asset) => asset.status === "Ready" && asset.imageReference);
  const prepared = new Map<string, PreparedImage>();
  await Promise.all(readyArt.map(async (asset) => {
    const image = await loadJpeg(asset).catch(() => null);
    if (image) prepared.set(asset.id, image);
  }));

  const drafts: PageDraft[] = [];
  const titlePage = pageDraft();
  titlePage.commands.push(rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, "0.96 0.94 0.89"));
  let titleY = PAGE_HEIGHT - 88;
  const cover = readyArt.find((asset) => asset.type === "cover" && prepared.has(asset.id));
  if (cover) {
    const image = prepared.get(cover.id)!;
    const size = fitImage(image, PAGE_WIDTH - 108, 255);
    titlePage.commands.push(drawImage(cover.id, (PAGE_WIDTH - size.width) / 2, titleY - size.height, size.width, size.height));
    titlePage.images.add(cover.id);
    titleY -= size.height + 37;
  } else {
    titlePage.commands.push(rect(54, titleY - 150, PAGE_WIDTH - 108, 150, "0.43 0.25 0.22"));
    titlePage.commands.push(drawText("A  L I V I N G  S T O R Y", 75, titleY - 128, 8, "F2", "0.96 0.91 0.82"));
    titleY -= 190;
  }
  for (const line of wrap(safe(story.title), 28, PAGE_WIDTH - 108)) {
    titlePage.commands.push(drawText(line, 54, titleY, 28, "F2"));
    titleY -= 33;
  }
  titleY -= 8;
  titlePage.commands.push(drawText(`by ${safe(story.authorSnapshot.displayName)}`, 54, titleY, 13, "F3", "0.47 0.25 0.22"));
  titleY -= 36;
  for (const line of wrap(safe(story.shortDescription), 10.5, PAGE_WIDTH - 108)) {
    titlePage.commands.push(drawText(line, 54, titleY, 10.5, "F1", "0.36 0.36 0.33"));
    titleY -= 15;
  }
  titlePage.commands.push(drawText(`Compiled through Section ${story.latestAcceptedTurnNumber}`, 54, 34, 8.5, "F1", "0.48 0.47 0.43"));
  drafts.push(titlePage);

  for (const turn of story.turns || []) {
    let page = pageDraft();
    let y = PAGE_HEIGHT - TOP;
    page.commands.push(drawText(`SECTION ${turn.turnNumber}`, MARGIN_X, y, 8, "F2", "0.47 0.25 0.22"));
    y -= 27;
    const sectionArt = readyArt.find((asset) => asset.turnNumber === turn.turnNumber && asset.type !== "cover" && prepared.has(asset.id));
    if (sectionArt) {
      const image = prepared.get(sectionArt.id)!;
      const size = fitImage(image, PAGE_WIDTH - MARGIN_X * 2, 210);
      page.commands.push(drawImage(sectionArt.id, (PAGE_WIDTH - size.width) / 2, y - size.height, size.width, size.height));
      page.images.add(sectionArt.id);
      y -= size.height + 12;
      for (const line of wrap(safe(sectionArt.caption), 8.5, PAGE_WIDTH - MARGIN_X * 2)) {
        page.commands.push(drawText(line, MARGIN_X, y, 8.5, "F3", "0.42 0.41 0.37"));
        y -= 12;
      }
      y -= 10;
    }

    for (const paragraph of splitParagraphs(turn.prose)) {
      for (const line of wrap(safe(paragraph), BODY_SIZE, PAGE_WIDTH - MARGIN_X * 2)) {
        if (y < BOTTOM + BODY_LEADING) {
          drafts.push(page);
          page = pageDraft();
          y = PAGE_HEIGHT - TOP;
        }
        page.commands.push(drawText(line, MARGIN_X, y, BODY_SIZE));
        y -= BODY_LEADING;
      }
      y -= 7;
    }
    drafts.push(page);
  }

  drafts.slice(1).forEach((page, index) => page.commands.push(drawText(String(index + 1), PAGE_WIDTH / 2 - 2, 24, 8, "F1", "0.48 0.47 0.43")));
  return assemblePdf(drafts, prepared, story);
}

function assemblePdf(drafts: PageDraft[], images: Map<string, PreparedImage>, story: Story) {
  const pdf = new PdfObjects();
  const catalogId = pdf.reserve();
  const pagesId = pdf.reserve();
  const bodyFontId = pdf.add("<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>");
  const boldFontId = pdf.add("<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>");
  const italicFontId = pdf.add("<< /Type /Font /Subtype /Type1 /BaseFont /Times-Italic /Encoding /WinAnsiEncoding >>");
  const infoId = pdf.add(`<< /Title (${pdfString(story.title)}) /Author (${pdfString(story.authorSnapshot.displayName)}) /Subject (A living-fiction story compiled from kotoba-no-kaijiba) /Creator (kotoba-no-kaijiba) >>`);
  const imageIds = new Map<string, number>();
  for (const [assetId, image] of images) {
    imageIds.set(assetId, pdf.addStream(`/Type /XObject /Subtype /Image /Width ${image.width} /Height ${image.height} /ColorSpace /${image.components === 1 ? "DeviceGray" : "DeviceRGB"} /BitsPerComponent 8 /Filter /DCTDecode`, image.bytes));
  }

  const pageIds: number[] = [];
  for (const draft of drafts) {
    const contentId = pdf.addStream("", ascii(draft.commands.join("\n")));
    const xObjects = [...draft.images].map((assetId) => `/${imageName(assetId)} ${imageIds.get(assetId)} 0 R`).join(" ");
    const resources = `<< /Font << /F1 ${bodyFontId} 0 R /F2 ${boldFontId} 0 R /F3 ${italicFontId} 0 R >>${xObjects ? ` /XObject << ${xObjects} >>` : ""} >>`;
    pageIds.push(pdf.add(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${PAGE_WIDTH} ${PAGE_HEIGHT}] /Resources ${resources} /Contents ${contentId} 0 R >>`));
  }
  pdf.set(pagesId, `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`);
  pdf.set(catalogId, `<< /Type /Catalog /Pages ${pagesId} 0 R >>`);
  return pdf.build(catalogId, infoId);
}

class PdfObjects {
  private objects: Array<Uint8Array | null> = [null];
  reserve() { this.objects.push(null); return this.objects.length - 1; }
  add(value: string) { const id = this.reserve(); this.set(id, value); return id; }
  set(id: number, value: string | Uint8Array) { this.objects[id] = typeof value === "string" ? ascii(value) : value; }
  addStream(dictionary: string, bytes: Uint8Array) {
    const id = this.reserve();
    this.objects[id] = concat([ascii(`<< ${dictionary} /Length ${bytes.length} >>\nstream\n`), bytes, ascii("\nendstream")]);
    return id;
  }
  build(rootId: number, infoId: number) {
    const chunks: Uint8Array[] = [ascii("%PDF-1.4\n%KOTOBA\n")];
    const offsets = [0];
    let length = chunks[0].length;
    for (let id = 1; id < this.objects.length; id += 1) {
      offsets[id] = length;
      const object = concat([ascii(`${id} 0 obj\n`), this.objects[id] || ascii("<<>>"), ascii("\nendobj\n")]);
      chunks.push(object); length += object.length;
    }
    const xrefOffset = length;
    const rows = ["0000000000 65535 f ", ...offsets.slice(1).map((offset) => `${String(offset).padStart(10, "0")} 00000 n `)];
    chunks.push(ascii(`xref\n0 ${this.objects.length}\n${rows.join("\n")}\ntrailer\n<< /Size ${this.objects.length} /Root ${rootId} 0 R /Info ${infoId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`));
    return concat(chunks);
  }
}

async function loadJpeg(asset: ArtAsset): Promise<PreparedImage> {
  let bytes = await loadAssetBytes(asset);
  let info = jpegInfo(bytes);
  if (!info) {
    const transformer = getImageTransformer();
    if (!transformer) throw new Error("A non-JPEG illustration could not be converted for PDF embedding.");
    const stream = new Response(bytes).body;
    if (!stream) throw new Error("Illustration stream unavailable.");
    const converted = await transformer.input(stream).transform({ fit: "scale-down" }).output({ format: "image/jpeg", quality: 88 });
    bytes = new Uint8Array(await (await converted.response()).arrayBuffer());
    info = jpegInfo(bytes);
  }
  if (!info) throw new Error("Illustration is not a supported JPEG.");
  return { bytes, ...info };
}

async function loadAssetBytes(asset: ArtAsset) {
  const ref = asset.imageReference || "";
  if (ref.startsWith("r2:")) {
    const object = await getArtBucket()?.get(ref.slice(3));
    if (!object) throw new Error("Art asset not found.");
    return new Uint8Array(await new Response(object.body).arrayBuffer());
  }
  const response = await fetch(ref, { signal: AbortSignal.timeout(10 * 60 * 1000) });
  if (!response.ok) throw new Error(`Art fetch failed (${response.status}).`);
  return new Uint8Array(await response.arrayBuffer());
}

function jpegInfo(bytes: Uint8Array) {
  if (bytes[0] !== 0xff || bytes[1] !== 0xd8) return null;
  const sof = new Set([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]);
  for (let i = 2; i + 9 < bytes.length;) {
    if (bytes[i] !== 0xff) { i += 1; continue; }
    while (bytes[i] === 0xff) i += 1;
    const marker = bytes[i++];
    if (marker === 0xd8 || marker === 0xd9) continue;
    if (i + 1 >= bytes.length) break;
    const length = (bytes[i] << 8) | bytes[i + 1];
    if (sof.has(marker) && i + 7 < bytes.length) return {
      height: (bytes[i + 3] << 8) | bytes[i + 4], width: (bytes[i + 5] << 8) | bytes[i + 6], components: bytes[i + 7],
    };
    if (length < 2) break;
    i += length;
  }
  return null;
}

function pageDraft(): PageDraft { return { commands: [], images: new Set<string>() }; }
function drawText(value: string, x: number, y: number, size: number, font = "F1", color = "0.15 0.16 0.14") { return `BT /${font} ${num(size)} Tf ${color} rg 1 0 0 1 ${num(x)} ${num(y)} Tm (${pdfString(value)}) Tj ET`; }
function rect(x: number, y: number, width: number, height: number, color: string) { return `q ${color} rg ${num(x)} ${num(y)} ${num(width)} ${num(height)} re f Q`; }
function drawImage(assetId: string, x: number, y: number, width: number, height: number) { return `q ${num(width)} 0 0 ${num(height)} ${num(x)} ${num(y)} cm /${imageName(assetId)} Do Q`; }
function imageName(assetId: string) { return `Im_${assetId.replace(/[^a-z0-9_-]/gi, "_")}`; }

function fitImage(image: { width: number; height: number }, maxWidth: number, maxHeight: number) {
  const scale = Math.min(maxWidth / image.width, maxHeight / image.height);
  return { width: image.width * scale, height: image.height * scale };
}
function splitParagraphs(prose: string) { return prose.replace(/\r/g, "").split(/\n\s*\n/).map((paragraph) => paragraph.replace(/\s+/g, " ").trim()).filter(Boolean); }
function wrap(text: string, size: number, maxWidth: number) {
  const maxChars = Math.max(12, Math.floor(maxWidth / (size * 0.49)));
  const words = text.split(/\s+/).filter(Boolean); const lines: string[] = []; let line = "";
  for (const word of words) { const candidate = line ? `${line} ${word}` : word; if (candidate.length <= maxChars || !line) line = candidate; else { lines.push(line); line = word; } }
  if (line) lines.push(line); return lines;
}
function safe(value: string) { return String(value || "").replace(/[\u2018\u2019]/g, "'").replace(/[\u201C\u201D]/g, '"').replace(/[\u2013\u2014]/g, "-").replace(/\u2026/g, "...").replace(/[^\x09\x0A\x0D\x20-\x7E]/g, "?"); }
function pdfString(value: string) { return safe(value).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)"); }
function num(value: number) { return Number(value.toFixed(2)); }
function ascii(value: string) { return new TextEncoder().encode(value); }
function concat(chunks: Uint8Array[]) { const length = chunks.reduce((total, chunk) => total + chunk.length, 0); const output = new Uint8Array(length); let offset = 0; for (const chunk of chunks) { output.set(chunk, offset); offset += chunk.length; } return output; }
