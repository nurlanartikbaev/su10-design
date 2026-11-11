// Выгрузка текстовых стилей, эффектов и градиентов Figma в TSV (снимок figma/snapshot/styles.tsv).
// Запуск: use_figma по файлу SU10 Design System (fileKey TLPll8pMMVWpHbJdWm6QVe).

const hex = c => {
  const h = x => Math.round(x * 255).toString(16).padStart(2, "0");
  return "#" + h(c.r) + h(c.g) + h(c.b) + (c.a !== undefined && c.a < 1 ? h(c.a) : "");
};
const cache = {};
const aliasName = async id => {
  if (!(id in cache)) {
    const v = await figma.variables.getVariableByIdAsync(id);
    if (!v) cache[id] = "?" + id;
    else {
      const col = await figma.variables.getVariableCollectionByIdAsync(v.variableCollectionId);
      cache[id] = "{" + (col ? col.name : "?") + "/" + v.name + "}";
    }
  }
  return cache[id];
};
const unit = u => (u === "PIXELS" ? "px" : "%");
const r = n => Math.round(n * 1000) / 1000;

const lines = ["## text\tfamily\tstyle\tsize\tline-height\tletter-spacing\tvar:fontSize\tvar:fontStyle\tvar:lineHeight"];
for (const s of await figma.getLocalTextStylesAsync()) {
  const b = s.boundVariables || {};
  const a = async k => (b[k] && b[k].id ? await aliasName(b[k].id) : "-");
  lines.push([
    s.name, s.fontName.family, s.fontName.style, s.fontSize,
    s.lineHeight.unit === "AUTO" ? "auto" : r(s.lineHeight.value) + unit(s.lineHeight.unit),
    r(s.letterSpacing.value) + unit(s.letterSpacing.unit),
    await a("fontSize"), await a("fontStyle"), await a("lineHeight"),
  ].join("\t"));
}
lines.push("## effect\tlayers (type color x y blur spread)");
for (const s of await figma.getLocalEffectStylesAsync()) {
  lines.push([s.name, s.effects.map(e =>
    e.type === "BACKGROUND_BLUR" || e.type === "LAYER_BLUR"
      ? e.type + " " + e.radius
      : [e.type, hex(e.color), e.offset.x, e.offset.y, e.radius, e.spread || 0].join(" ")
  ).join("; ")].join("\t"));
}
lines.push("## paint\tlayers (type stop:color ...)");
for (const s of await figma.getLocalPaintStylesAsync()) {
  lines.push([s.name, s.paints.map(p =>
    p.type === "SOLID"
      ? "SOLID " + hex(p.color)
      : p.type + " " + p.gradientStops.map(g => r(g.position) + ":" + hex(g.color)).join(" ")
  ).join("; ")].join("\t"));
}
return lines.join("\n");
