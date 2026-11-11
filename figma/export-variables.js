// Выгрузка одной коллекции переменных Figma в TSV (снимок figma/snapshot/<Коллекция>.tsv).
// Запуск: use_figma по файлу SU10 Design System (fileKey TLPll8pMMVWpHbJdWm6QVe).
// Перед запуском задайте COLLECTION, FROM и TO. Лимит ответа use_figma — 48 КБ,
// поэтому Theme (376 переменных) выгружают в два вызова: 0–190 и 190–1000.
// Результат вставляют в файл как есть, части склеивают по порядку.

const COLLECTION = "Theme";
const FROM = 0;
const TO = 1000;

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

const col = (await figma.variables.getLocalVariableCollectionsAsync()).find(c => c.name === COLLECTION);
if (!col) throw new Error("Нет коллекции " + COLLECTION);
const modes = col.modes;
const lines = [];
if (FROM === 0) lines.push(["##", col.name, ...modes.map(m => m.name)].join("\t"));
for (const vid of col.variableIds.slice(FROM, TO)) {
  const v = await figma.variables.getVariableByIdAsync(vid);
  const vals = [];
  for (const m of modes) {
    const raw = v.valuesByMode[m.modeId];
    if (raw && raw.type === "VARIABLE_ALIAS") vals.push(await aliasName(raw.id));
    else if (raw && typeof raw === "object" && "r" in raw) vals.push(hex(raw));
    else vals.push(String(raw));
  }
  lines.push([v.name, v.resolvedType, v.scopes.join(","), ...vals].join("\t"));
}
return { total: col.variableIds.length, from: FROM, to: Math.min(TO, col.variableIds.length), tsv: lines.join("\n") };
