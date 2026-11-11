// Контрольные суммы снимка прямо в Figma — чтобы проверить, что figma/snapshot/*.tsv
// перенесён без ошибок. Сравнивают с выводом `python3 scripts/checksum.py`.
// Для каждого файла: число строк и FNV-1a каждой строки (8 hex). Несовпавшая строка = ошибка переноса.
// Запуск: use_figma по файлу SU10 Design System (fileKey TLPll8pMMVWpHbJdWm6QVe).

const fnv = s => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); };
const hex = c => { const h = x => Math.round(x * 255).toString(16).padStart(2, "0"); return "#" + h(c.r) + h(c.g) + h(c.b) + (c.a !== undefined && c.a < 1 ? h(c.a) : ""); };
const cache = {};
const aliasName = async id => { if (!(id in cache)) { const v = await figma.variables.getVariableByIdAsync(id); if (!v) cache[id] = "?" + id; else { const col = await figma.variables.getVariableCollectionByIdAsync(v.variableCollectionId); cache[id] = "{" + (col ? col.name : "?") + "/" + v.name + "}"; } } return cache[id]; };

const files = {};
for (const col of await figma.variables.getLocalVariableCollectionsAsync()) {
  const lines = [["##", col.name, ...col.modes.map(m => m.name)].join("\t")];
  for (const vid of col.variableIds) {
    const v = await figma.variables.getVariableByIdAsync(vid);
    const vals = [];
    for (const m of col.modes) { const raw = v.valuesByMode[m.modeId]; if (raw && raw.type === "VARIABLE_ALIAS") vals.push(await aliasName(raw.id)); else if (raw && typeof raw === "object" && "r" in raw) vals.push(hex(raw)); else vals.push(String(raw)); }
    lines.push([v.name, v.resolvedType, v.scopes.join(","), ...vals].join("\t"));
  }
  files[col.name + ".tsv"] = lines;
}

const unit = u => (u === "PIXELS" ? "px" : "%");
const r = n => Math.round(n * 1000) / 1000;
const st = ["## text\tfamily\tstyle\tsize\tline-height\tletter-spacing\tvar:fontSize\tvar:fontStyle\tvar:lineHeight"];
for (const s of await figma.getLocalTextStylesAsync()) {
  const b = s.boundVariables || {};
  const a = async k => (b[k] && b[k].id ? await aliasName(b[k].id) : "-");
  st.push([s.name, s.fontName.family, s.fontName.style, s.fontSize, s.lineHeight.unit === "AUTO" ? "auto" : r(s.lineHeight.value) + unit(s.lineHeight.unit), r(s.letterSpacing.value) + unit(s.letterSpacing.unit), await a("fontSize"), await a("fontStyle"), await a("lineHeight")].join("\t"));
}
st.push("## effect\tlayers (type color x y blur spread)");
for (const s of await figma.getLocalEffectStylesAsync()) st.push([s.name, s.effects.map(e => e.type === "BACKGROUND_BLUR" || e.type === "LAYER_BLUR" ? e.type + " " + e.radius : [e.type, hex(e.color), e.offset.x, e.offset.y, e.radius, e.spread || 0].join(" ")).join("; ")].join("\t"));
st.push("## paint\tlayers (type stop:color ...)");
for (const s of await figma.getLocalPaintStylesAsync()) st.push([s.name, s.paints.map(p => p.type === "SOLID" ? "SOLID " + hex(p.color) : p.type + " " + p.gradientStops.map(g => r(g.position) + ":" + hex(g.color)).join(" ")).join("; ")].join("\t"));
files["styles.tsv"] = st;

const out = {};
for (const [name, lines] of Object.entries(files)) out[name] = { lines: lines.length, file: fnv(lines.join("\n")), rows: lines.map(fnv).join(" ") };
return out;
