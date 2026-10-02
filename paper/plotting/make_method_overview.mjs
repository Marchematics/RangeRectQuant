/**
 * Reference-matched, native editable RangeRectQuant method figure.
 * One declarative layout drives the PPTX and text-preserving SVG.
 * Run with the Codex bundled Node runtime. No manuscript source is changed.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL, fileURLToPath } from 'node:url';

const PAPER = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(PAPER, '.method-overview-build');
const OUT = path.join(PAPER, 'figures');
const STEM = process.env.ARTIFACT_BASENAME || 'range_rect_quant_method';
const SKILL = process.env.SKILL_DIR || '/Users/nathmath/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const MODULES = process.env.RUNTIME_NODE_MODULES || '/Users/nathmath/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(MODULES, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL, 'container_tools/artifact_tool_utils.mjs')).href);

await fs.mkdir(BUILD, { recursive: true });
await fs.mkdir(path.join(OUT, 'specs'), { recursive: true });

const suppliedSpec = process.env.SPEC_PATH ? JSON.parse(await fs.readFile(path.resolve(process.env.SPEC_PATH), 'utf8')) : null;
const W = suppliedSpec?.canvas.width ?? 1500, H = suppliedSpec?.canvas.height ?? 560;
const PRINT_WIDTH_CM = suppliedSpec?.canvas.width_cm ?? 18;
const SCALE = PRINT_WIDTH_CM / 2.54 * 96 / W;
const FONT = suppliedSpec?.font ?? 'Times New Roman';
let spec = {
  schema: 'range-rect-quant-method-layout-v1',
  canvas: { width: W, height: H, width_cm: PRINT_WIDTH_CM, height_cm: PRINT_WIDTH_CM * H / W },
  font: FONT,
  source: {
    pdf: path.join(PAPER, 'main.pdf'),
    pdf_sha256: crypto.createHash('sha256').update(await fs.readFile(path.join(PAPER, 'main.pdf'))).digest('hex'),
    relevant_pages: [3, 4, 5],
    manuscript: 'sections/method.tex',
    reference: '/var/folders/w2/s4nzxrcs4rsfpz8rnzmb7n8r0000gn/T/codex-clipboard-05b7e83e-096e-4a17-9b33-d1299843d3b2.png',
  },
  semantics: [
    'Only the construction phase changes the source X to a quantized field Y.',
    'Backward remaining-row feasibility precedes forward coarse-first selection, repeated for each row.',
    'Protected choices stay exact and can retain nonzero remainders.',
    'The two quotient/remainder coding paths are lossless with respect to Y, not X.',
    'Decoding recombines Y directly and does not invert the lossy construction.',
    'Sum and valid-count prefix tables use decoded Y and the exact missing mask.',
    'The figure does not depict the finite-rank coding bound as the implemented LZMA format.',
  ],
  backgrounds: [], boxes: [], texts: [], arrows: [], dividers: [],
};
const rect = (array, id, x, y, w, h, fill = '#FFFFFF', stroke = '#202020', radius = 12) =>
  array.push({ id, x, y, w, h, fill, stroke, radius });
const text = (id, label, x, y, w, h, size = 26, extra = {}) =>
  spec.texts.push({ id, label, x, y, w, h, size, color: '#111111', ...extra });
const arrow = (id, x1, y1, x2, y2, extra = {}) =>
  spec.arrows.push({ id, x1, y1, x2, y2, ...extra });

// The reference's grammar: a gray construction area, hatched lossless areas,
// serif type, dashed phase boundaries, and a reverse lower decoding route.
rect(spec.backgrounds, 'construction-region', 222, 134, 446, 167, '#DEDEDE', 'none', 14);
rect(spec.backgrounds, 'query-region', 222, 365, 446, 124, '#E8E8E8', 'none', 14);
rect(spec.backgrounds, 'lossless-encoder-region', 820, 134, 434, 171, '#FFFFFF', 'none', 0);
spec.backgrounds.at(-1).pattern = 'upwardDiagonal';
rect(spec.backgrounds, 'lossless-decoder-region', 820, 337, 434, 152, '#FFFFFF', 'none', 0);
spec.backgrounds.at(-1).pattern = 'downwardDiagonal';
rect(spec.backgrounds, 'persistent-storage', 1421, 134, 57, 355, '#DEDEDE', 'none', 14);
for (const x of [210, 808, 1398]) spec.dividers.push({ x, y1: 28, y2: 504 });

text('construction-heading', 'RangeRectQuant', 222, 24, 573, 40, 33);
text('construction-subheading', 'Field construction (lossy)', 222, 66, 573, 31, 25);
text('encoder-heading', 'Encoding phase', 820, 24, 434, 40, 33);
text('encoder-subheading', 'lossless', 820, 66, 434, 31, 25);
text('parameters', 'B = ⌊ε/4⌋,  q,  U,  protected set P', 227, 102, 436, 30, 24);
text('decoder-heading', 'Source-free decoding', 820, 306, 434, 31, 27);
text('query-heading', 'Queries after decoding', 222, 328, 446, 33, 27);

rect(spec.boxes, 'source-field', 30, 158, 160, 126);
text('source-title', 'Original\nfield X', 40, 170, 140, 70, 30);
text('source-body', 'bounded integers', 36, 248, 148, 24, 21);

rect(spec.boxes, 'backward-pass', 240, 147, 180, 140);
text('backward-title', 'Backward\nfeasibility', 248, 153, 164, 60, 28);
text('backward-body', 'Remaining-row\nfeasible intervals', 247, 228, 166, 50, 22);
rect(spec.boxes, 'forward-pass', 466, 147, 184, 140);
text('forward-title', 'Forward\nselection', 474, 153, 168, 60, 28);
text('forward-body', 'Coarse if feasible\nfine otherwise\nExact on P', 474, 219, 168, 64, 21.5);
text('row-scans', 'Per row: right-to-left scan, then left-to-right scan', 222, 301, 446, 25, 20.5);

rect(spec.boxes, 'quantized-field', 700, 134, 95, 355);
text('field-title', 'Quantized field Y', 582, 294, 300, 36, 30, { rotation: 270 });
text('field-body', 'bounded integer pixels', 610, 298, 300, 28, 23, { rotation: 270 });

rect(spec.boxes, 'split-field', 835, 161, 142, 120);
text('split-title', 'Split', 842, 176, 128, 37, 30);
text('split-equation', 'Y = qZ + r', 840, 226, 132, 32, 25);
for (const [id, y] of [['quotient-encoder', 144], ['remainder-encoder', 228]]) {
  rect(spec.boxes, id, 1060, y, 176, 70);
  text(`${id}-text`, 'Byte shuffle\nLZMA encoder', 1065, y + 7, 166, 56, 25);
}
text('quotient-label', 'Z', 988, 148, 60, 27, 25, { italic: true });
text('remainder-label', 'r', 988, 232, 60, 27, 25, { italic: true });

rect(spec.boxes, 'compressed-file', 1275, 134, 103, 355);
text('file-title', 'Compressed file', 1158, 294, 300, 36, 30, { rotation: 270 });
text('file-components', 'streams, masks, metadata', 1183, 298, 300, 28, 22, { rotation: 270 });
text('file-config', 'config. and integrity checks', 1206, 300, 300, 24, 20, { rotation: 270 });
text('storage-title', 'Persistent storage', 1299.5, 294, 300, 35, 28, { rotation: 270 });

rect(spec.boxes, 'recombine-field', 835, 352, 142, 122);
text('recombine-title', 'Recombine', 839, 365, 134, 35, 27);
text('recombine-equation', 'Y = qZ + r', 840, 424, 132, 32, 25);
for (const [id, y] of [['quotient-decoder', 340], ['remainder-decoder', 422]]) {
  rect(spec.boxes, id, 1060, y, 176, 64);
  text(`${id}-text`, 'LZMA decoder\nByte unshuffle', 1065, y + 5, 166, 54, 25);
}
text('decoded-quotient-label', 'Z', 988, 340, 60, 27, 25, { italic: true });
text('decoded-remainder-label', 'r', 988, 422, 60, 27, 25, { italic: true });

rect(spec.boxes, 'prefix-tables', 466, 381, 184, 96);
text('prefix-title', 'Prefix tables', 474, 390, 168, 37, 29);
text('prefix-body', 'sum / valid count', 472, 440, 172, 28, 23);
rect(spec.boxes, 'four-corner-query', 240, 381, 180, 96);
text('query-title', 'Four-corner\nqueries', 248, 396, 164, 64, 29);
rect(spec.boxes, 'regional-output', 30, 381, 160, 96);
text('regional-title', 'Regional\nsum / count', 36, 387, 148, 59, 28);
text('regional-body', 'any rectangle', 36, 450, 148, 22, 21);
text('exact-mask-note', 'Exact missing mask supplies valid-sample counts', 222, 490, 446, 25, 21);

// Straight, row-aligned routes reproduce the reference without suggesting
// that the lossy quantizer has an inverse on the decoding route.
arrow('input-to-backward', 190, 220, 240, 220);
arrow('backward-to-forward', 420, 220, 466, 220);
arrow('forward-to-field', 650, 220, 700, 220);
arrow('field-to-split', 795, 220, 835, 220);
arrow('quotient-to-encoder', 977, 179, 1060, 179);
arrow('remainder-to-encoder', 977, 263, 1060, 263);
arrow('quotient-to-file', 1236, 179, 1275, 179);
arrow('remainder-to-file', 1236, 263, 1275, 263);
arrow('file-to-storage', 1378, 220, 1421, 220);
arrow('storage-to-file', 1421, 429, 1378, 429);
arrow('file-to-quotient-decoder', 1275, 372, 1236, 372);
arrow('file-to-remainder-decoder', 1275, 454, 1236, 454);
arrow('quotient-to-recombine', 1060, 372, 977, 372);
arrow('remainder-to-recombine', 1060, 454, 977, 454);
arrow('recombine-to-field', 835, 429, 795, 429);
arrow('field-to-prefix', 700, 429, 650, 429);
arrow('prefix-to-queries', 466, 429, 420, 429);
arrow('queries-to-measurements', 240, 429, 190, 429);

text('joint-guarantee', '0 ≤ Y ≤ U,   Y = X on P,   |prefix error| ≤ B  ⇒  every rectangular sum error ≤ ε', 30, 524, 1448, 30, 25);

if (suppliedSpec) spec = suppliedSpec;

// All geometry uses one virtual canvas so print dimensions stay independent
// of the preview resolution. The stored layout is the editable source.
await fs.writeFile(path.join(OUT, 'specs', `${STEM}.json`), JSON.stringify(spec, null, 2) + '\n');

const presentation = Presentation.create({ slideSize: { width: W * SCALE, height: H * SCALE } });
const slide = presentation.slides.add();
slide.background.fill = '#FFFFFF';
const p = (o) => ({ left: o.x * SCALE, top: o.y * SCALE, width: o.w * SCALE, height: o.h * SCALE, rotation: o.rotation || 0 });
const addRect = o => slide.shapes.add({
  name: o.id,
  geometry: 'roundRect', position: p(o),
  fill: o.pattern ? { type: 'solid', color: o.fill, pattern: { type: o.pattern, color: '#B9B9B9' } } : o.fill,
  line: { style: 'solid', fill: o.stroke, width: o.stroke === 'none' ? 0 : 1.35 * SCALE },
  borderRadius: o.radius * SCALE,
});
for (const o of spec.backgrounds) addRect(o);
for (const d of spec.dividers) slide.shapes.add({
  geometry: 'line', name: `phase-divider-${d.x}`,
  position: { left: d.x * SCALE, top: d.y1 * SCALE, width: 0, height: (d.y2 - d.y1) * SCALE },
  fill: 'none', line: { style: 'dashed', fill: '#444444', width: 1.5 * SCALE },
});
for (const o of spec.boxes) addRect(o);

// Tiny transparent endpoint shapes make exact multi-port row routing native
// and independently editable in PowerPoint, including each arrowhead.
for (const a of spec.arrows) {
  const endpoint = (x, y, suffix) => slide.shapes.add({
    geometry: 'rect', name: `${a.id}-${suffix}`,
    position: { left: (x - 0.15) * SCALE, top: (y - 0.15) * SCALE, width: 0.3 * SCALE, height: 0.3 * SCALE },
    fill: 'none', line: { fill: 'none', width: 0 },
  });
  const from = endpoint(a.x1, a.y1, 'from');
  const to = endpoint(a.x2, a.y2, 'to');
  const connector = slide.shapes.connect(from, to, {
    kind: 'straight', fromSide: a.x2 > a.x1 ? 'right' : 'left', toSide: a.x2 > a.x1 ? 'left' : 'right',
    line: { style: 'solid', fill: '#505050', width: 1.5 * SCALE },
    // OpenXML head is the start endpoint, while tail is the destination.
    tail: { type: 'arrow', width: 'sm', length: 'sm' },
  });
  connector.bringToFront();
}
for (const o of spec.texts) {
  const lines = o.label.split('\n');
  // Explicit line boxes avoid renderer-dependent paragraph spacing and keep
  // the PPTX leading identical to the text-preserving SVG export.
  const lineHeight = o.size * 1.04;
  for (const [i, label] of lines.entries()) {
    const line = lines.length === 1 ? o : {
      ...o, h: lineHeight,
      y: o.y + o.h / 2 + (i - (lines.length - 1) / 2) * lineHeight - lineHeight / 2,
    };
    const t = slide.shapes.add({ geometry: 'textbox', name: `${o.id}${lines.length > 1 ? `-line-${i+1}` : ''}`, position: p(line), fill: 'none', line: { fill: 'none', width: 0 } });
    t.text = label;
    t.text.style = {
      typeface: FONT, fontSize: o.size * SCALE, color: o.color,
      alignment: 'center', verticalAlignment: 'middle', autoFit: 'none', wrap: 'none',
      italic: !!o.italic,
      insets: { top: 0, right: 0, bottom: 0, left: 0 },
    };
  }
}
slide.speakerNotes.textFrame.setText([
  'RangeRectQuant method overview. Source: ' + spec.source.pdf + ', pages 3–5, and ' + path.join(PAPER, 'sections/method.tex') + '.',
  'Source PDF SHA-256: ' + spec.source.pdf_sha256,
  'Gray upper region: the lossy, row-wise backward–forward construction. Gray lower region: ordinary queries after decoding. Hatched regions: lossless coding and decoding of the constructed Y.',
  'B=floor(epsilon/4). q is the positive integer coarse step. U is the physical upper bound. P includes missing samples and designated exact samples.',
  'Z=floor(Y/q), r=Y mod q. Both arrays use 16-bit low-byte/high-byte shuffle and LZMA preset 6. Bit-packed masks use zlib. The file also contains configuration, geospatial metadata, reconstruction digest, and checksum.',
  'Decoding never reruns or reverses the quantizer and needs neither X nor query-specific corrections. The full missing mask enters the valid-count prefix table.',
  'Arrow endpoints are separate native transparent port shapes. Text, rectangles, patterns, arrows and arrowheads are editable. No raster images are embedded.',
].join('\n\n'));

const candidate = path.join(BUILD, 'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidate);
const preview = await presentation.export({ slide, format: 'png', scale: 2.4 });
await fs.writeFile(path.join(BUILD, 'artifact-preview.png'), new Uint8Array(await preview.arrayBuffer()));
const layout = await slide.export({ format: 'layout' });
await fs.writeFile(path.join(BUILD, 'layout.json'), await layout.text());
await fs.writeFile(path.join(BUILD, 'presentation.json'), JSON.stringify(presentation.toProto()));

// A parallel vector export keeps journal-facing labels as searchable text,
// rather than flattening the PPTX or outlining its font glyphs.
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&apos;' }[c]));
const svgRect = o => `<rect id="${o.id}" x="${o.x}" y="${o.y}" width="${o.w}" height="${o.h}" rx="${o.radius}" fill="${o.pattern ? `url(#${o.pattern})` : o.fill}" stroke="${o.stroke}" stroke-width="1.35"/>`;
const svgText = o => {
  const lines = o.label.split('\n');
  const lh = o.size * 1.04;
  const cy = o.y + o.h / 2;
  const cx = o.x + o.w / 2;
  const transform = o.rotation ? ` transform="rotate(-90 ${cx} ${cy})"` : '';
  return `<text id="${o.id}" x="${cx}" text-anchor="middle" font-size="${o.size}" font-style="${o.italic ? 'italic' : 'normal'}" fill="${o.color}"${transform}>` +
    lines.map((s, i) => `<tspan x="${cx}" y="${cy + (i - (lines.length - 1) / 2) * lh + o.size * 0.32}">${esc(s)}</tspan>`).join('') + '</text>';
};
const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${PRINT_WIDTH_CM}cm" height="${PRINT_WIDTH_CM * H / W}cm" viewBox="0 0 ${W} ${H}">
<title>RangeRectQuant method overview</title>
<desc>${esc(spec.semantics.join(' '))}</desc>
<defs>
<pattern id="upwardDiagonal" patternUnits="userSpaceOnUse" width="9" height="9"><rect width="9" height="9" fill="white"/><path d="M-2 2L2-2 M0 9L9 0 M7 11L11 7" stroke="#BBBBBB" stroke-width="1.1"/></pattern>
<pattern id="downwardDiagonal" patternUnits="userSpaceOnUse" width="9" height="9"><rect width="9" height="9" fill="white"/><path d="M-2 7L2 11 M0 0L9 9 M7-2L11 2" stroke="#BBBBBB" stroke-width="1.1"/></pattern>
<marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M1 1L7 4L1 7" fill="none" stroke="#505050" stroke-width="1.1"/></marker>
</defs>
<rect width="${W}" height="${H}" fill="white"/>
<g font-family="${FONT},Times,serif">
${spec.backgrounds.map(svgRect).join('\n')}
${spec.dividers.map(d => `<path d="M${d.x} ${d.y1}V${d.y2}" stroke="#444444" stroke-width="1.5" stroke-dasharray="10 10" fill="none"/>`).join('\n')}
${spec.boxes.map(svgRect).join('\n')}
${spec.arrows.map(a => `<path id="${a.id}" d="M${a.x1} ${a.y1}L${a.x2} ${a.y2}" fill="none" stroke="#505050" stroke-width="1.5" marker-end="url(#arrowhead)"/>`).join('\n')}
${spec.texts.map(svgText).join('\n')}
</g></svg>\n`;
await fs.writeFile(path.join(OUT, `${STEM}.svg`), svg);

if (process.env.FINALIZE === '1') {
  const result = await finalizePresentation({
    workspaceDir: PAPER, candidatePath: candidate,
    finalPath: path.join(OUT, process.env.FINAL_PPTX_NAME || `${STEM}_editable.pptx`),
    pythonExecutable: process.env.RUNTIME_PYTHON || '/Users/nathmath/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
    integrityValidatorPath: path.join(SKILL, 'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath: path.join(SKILL, 'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs: ['--expected-slide-size-emu', `${Math.round(W*SCALE*9525)},${Math.round(H*SCALE*9525)}`, '--validate-heading-fit'],
    explicitTotalSlideCount: 1,
    requiredNativeTableOwnerSlides: [], requiredNativeChartOwnerSlides: [],
    fontPolicy: { basis: 'design', families: [FONT] },
    verifyArtifactToolImport: true,
    receiptPath: path.join(BUILD, `${STEM}.validation.json`),
  });
  console.log(JSON.stringify(result, null, 2));
}
console.log(JSON.stringify({ candidate, svg: path.join(OUT, `${STEM}.svg`), print_cm: spec.canvas }, null, 2));
