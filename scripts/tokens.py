#!/usr/bin/env python3
"""Токены SU10: репозиторий — источник правды, Figma — копия.

  python3 scripts/tokens.py build     tokens/*.json → dist/tokens.css
  python3 scripts/tokens.py diff      чем Figma (figma/snapshot) отличается от репозитория
  python3 scripts/tokens.py import    принять Figma: figma/snapshot → tokens/*.json
  python3 scripts/tokens.py push      репозиторий → Figma: пишет figma/push.generated.js для use_figma
  python3 scripts/tokens.py check     круговая проверка: tokens → TSV совпадает со снимком

Только стандартная библиотека Python 3.9+.
"""
import json
import pathlib
import re
import sys
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "figma" / "snapshot"
TOKENS = ROOT / "tokens"
DIST = ROOT / "dist"

COLLECTIONS = ["Colors", "Spacing", "Platform", "Theme"]  # порядок важен для CSS
TYPE_TO_DTCG = {"COLOR": "color", "FLOAT": "number", "STRING": "string"}
DTCG_TO_TYPE = {v: k for k, v in TYPE_TO_DTCG.items()}
WEIGHTS = {"Thin": 100, "Light": 300, "Regular": 400, "Medium": 500, "Semi Bold": 600, "Bold": 700, "Extra Bold": 800, "Black": 900}
DESKTOP_MIN_WIDTH = "1024px"  # с какой ширины действует режим Platform/Desktop
PREFIX = "su10"


# ---------- снимок Figma (TSV) ----------

def read_snapshot_collection(name):
    lines = (SNAP / f"{name}.tsv").read_text(encoding="utf-8").rstrip("\n").split("\n")
    head = lines[0].split("\t")
    assert head[0] == "##" and head[1] == name, f"{name}.tsv: неверный заголовок"
    modes = head[2:]
    rows = OrderedDict()
    for line in lines[1:]:
        cells = line.split("\t")
        rows[cells[0]] = {"type": cells[1], "scopes": cells[2], "values": OrderedDict(zip(modes, cells[3:]))}
    return modes, rows


def read_snapshot_styles():
    sections = {"text": OrderedDict(), "effect": OrderedDict(), "paint": OrderedDict()}
    heads = {}
    cur = None
    for line in (SNAP / "styles.tsv").read_text(encoding="utf-8").rstrip("\n").split("\n"):
        if line.startswith("## "):
            cur = line[3:].split("\t")[0]
            heads[cur] = line
            continue
        cells = line.split("\t")
        sections[cur][cells[0]] = cells[1:]
    return heads, sections


# ---------- токены (DTCG JSON) ----------

def alias_to_dtcg(v):
    m = re.fullmatch(r"\{([^/]+)/(.+)\}", v)
    return "{" + m.group(1) + "." + m.group(2).replace("/", ".") + "}" if m else v


def alias_from_dtcg(v):
    if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
        parts = v[1:-1].split(".")
        return "{" + parts[0] + "/" + "/".join(parts[1:]) + "}"
    return v


def to_json_value(v, ftype):
    if v.startswith("{"):
        return alias_to_dtcg(v)
    if ftype == "FLOAT":
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def from_json_value(v):
    if isinstance(v, str):
        return alias_from_dtcg(v)
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v)


def set_path(tree, path, leaf):
    node = tree
    for p in path[:-1]:
        node = node.setdefault(p, OrderedDict())
    node[path[-1]] = leaf


def walk(tree, path=()):
    for k, v in tree.items():
        if k.startswith("$"):
            continue
        if isinstance(v, dict) and "$value" in v:
            yield path + (k,), v
        elif isinstance(v, dict):
            yield from walk(v, path + (k,))


def snapshot_to_tokens(name):
    modes, rows = read_snapshot_collection(name)
    tree = OrderedDict()
    tree["$extensions"] = {"su10": {"modes": modes}}
    for vname, r in rows.items():
        vals = OrderedDict((m, to_json_value(v, r["type"])) for m, v in r["values"].items())
        leaf = OrderedDict([("$type", TYPE_TO_DTCG[r["type"]]), ("$value", vals[modes[0]])])
        ext = OrderedDict([("scopes", r["scopes"].split(","))])
        if len(modes) > 1:
            ext["modes"] = vals
        leaf["$extensions"] = {"su10": ext}
        set_path(tree, vname.split("/"), leaf)
    return {name: tree}


def styles_to_tokens():
    heads, s = read_snapshot_styles()
    text, effect, paint = OrderedDict(), OrderedDict(), OrderedDict()
    for name, c in s["text"].items():
        family, style, size, lh, ls, vsize, vstyle, vlh = c
        value = OrderedDict([("fontFamily", family), ("fontStyle", style), ("fontWeight", WEIGHTS.get(style, 400)),
                             ("fontSize", int(float(size)) if float(size).is_integer() else float(size)),
                             ("lineHeight", lh), ("letterSpacing", ls)])
        bound = OrderedDict((k, alias_to_dtcg(v)) for k, v in (("fontSize", vsize), ("fontStyle", vstyle), ("lineHeight", vlh)) if v != "-")
        set_path(text, name.split("/"), OrderedDict([("$type", "typography"), ("$value", value),
                                                     ("$extensions", {"su10": {"variables": bound}})]))
    for name, c in s["effect"].items():
        layers = []
        for part in c[0].split("; "):
            bits = part.split(" ")
            if bits[0] == "DROP_SHADOW" or bits[0] == "INNER_SHADOW":
                layers.append(OrderedDict([("type", bits[0]), ("color", bits[1]), ("offsetX", num(bits[2])), ("offsetY", num(bits[3])),
                                           ("blur", num(bits[4])), ("spread", num(bits[5]))]))
            else:
                layers.append(OrderedDict([("type", bits[0]), ("blur", num(bits[1]))]))
        set_path(effect, name.split("/"), OrderedDict([("$type", "effect"), ("$value", layers)]))
    for name, c in s["paint"].items():
        layers = []
        for part in c[0].split("; "):
            bits = part.split(" ")
            if bits[0] == "SOLID":
                layers.append(OrderedDict([("type", "SOLID"), ("color", bits[1])]))
            else:
                stops = [OrderedDict([("position", num(b.split(":")[0])), ("color", b.split(":")[1])]) for b in bits[1:]]
                layers.append(OrderedDict([("type", bits[0]), ("stops", stops)]))
        set_path(paint, name.split("/"), OrderedDict([("$type", "gradient" if layers[0]["type"] != "SOLID" else "color"), ("$value", layers)]))
    return {"text": text, "effect": effect, "paint": paint}, heads


def num(x):
    f = float(x)
    return int(f) if f.is_integer() else f


def load_tokens(name):
    return json.loads((TOKENS / f"{name}.json").read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


# ---------- токены → TSV (для сверки со снимком) ----------

def tokens_to_rows(name):
    tree = load_tokens(name)[name]
    modes = tree["$extensions"]["su10"]["modes"]
    rows = OrderedDict()
    for path, leaf in walk(tree):
        ext = leaf.get("$extensions", {}).get("su10", {})
        vals = ext.get("modes") or {modes[0]: leaf["$value"]}
        rows["/".join(path)] = {"type": DTCG_TO_TYPE[leaf["$type"]], "scopes": ",".join(ext.get("scopes", [])),
                                "values": OrderedDict((m, from_json_value(vals[m])) for m in modes)}
    return modes, rows


def fmt_num(x):
    return str(int(x)) if float(x).is_integer() else str(x)


def styles_rows():
    st = load_tokens("styles")
    out = {"text": OrderedDict(), "effect": OrderedDict(), "paint": OrderedDict()}
    for path, leaf in walk(st["text"]):
        v, b = leaf["$value"], leaf["$extensions"]["su10"]["variables"]
        out["text"]["/".join(path)] = [v["fontFamily"], v["fontStyle"], fmt_num(v["fontSize"]), v["lineHeight"], v["letterSpacing"],
                                       alias_from_dtcg(b.get("fontSize", "-")), alias_from_dtcg(b.get("fontStyle", "-")),
                                       alias_from_dtcg(b.get("lineHeight", "-"))]
    for path, leaf in walk(st["effect"]):
        parts = []
        for l in leaf["$value"]:
            if "color" in l:
                parts.append(" ".join([l["type"], l["color"], fmt_num(l["offsetX"]), fmt_num(l["offsetY"]), fmt_num(l["blur"]), fmt_num(l["spread"])]))
            else:
                parts.append(l["type"] + " " + fmt_num(l["blur"]))
        out["effect"]["/".join(path)] = ["; ".join(parts)]
    for path, leaf in walk(st["paint"]):
        parts = []
        for l in leaf["$value"]:
            if l["type"] == "SOLID":
                parts.append("SOLID " + l["color"])
            else:
                parts.append(l["type"] + " " + " ".join(fmt_num(s["position"]) + ":" + s["color"] for s in l["stops"]))
        out["paint"]["/".join(path)] = ["; ".join(parts)]
    return out


# ---------- команды ----------

def cmd_import():
    TOKENS.mkdir(exist_ok=True)
    for name in COLLECTIONS:
        (TOKENS / f"{name}.json").write_text(json.dumps(snapshot_to_tokens(name), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    st, heads = styles_to_tokens()
    st["$extensions"] = {"su10": {"heads": heads}}
    (TOKENS / "styles.json").write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("tokens/ обновлены из figma/snapshot. Дальше: python3 scripts/tokens.py check && python3 scripts/tokens.py build")


def collect_diff():
    """Возвращает список изменений: (раздел, имя, что, в репозитории, в Figma)."""
    changes = []
    for name in COLLECTIONS:
        fmodes, frows = read_snapshot_collection(name)
        rmodes, rrows = tokens_to_rows(name)
        if fmodes != rmodes:
            changes.append((name, "(режимы)", "изменено", " | ".join(rmodes), " | ".join(fmodes)))
        for k in rrows:
            if k not in frows:
                changes.append((name, k, "нет в Figma", fmt_vals(rrows[k]), ""))
        for k, f in frows.items():
            r = rrows.get(k)
            if r is None:
                changes.append((name, k, "нет в репозитории", "", fmt_vals(f)))
            elif r != f:
                what = []
                if r["type"] != f["type"]:
                    what.append("тип")
                if r["scopes"] != f["scopes"]:
                    what.append("scopes")
                if r["values"] != f["values"]:
                    what.append("значение")
                changes.append((name, k, ", ".join(what), fmt_vals(r), fmt_vals(f)))
    _, fs = read_snapshot_styles()
    rs = styles_rows()
    for sec in ("text", "effect", "paint"):
        for k in rs[sec]:
            if k not in fs[sec]:
                changes.append((f"styles/{sec}", k, "нет в Figma", " ".join(rs[sec][k]), ""))
        for k, f in fs[sec].items():
            r = rs[sec].get(k)
            if r is None:
                changes.append((f"styles/{sec}", k, "нет в репозитории", "", " ".join(f)))
            elif r != f:
                changes.append((f"styles/{sec}", k, "значение", " ".join(r), " ".join(f)))
    return changes


def fmt_vals(r):
    return " | ".join(r["values"].values()) + ("" if r["scopes"] in ("", "ALL_SCOPES") else f"  ({r['scopes']})")


def cmd_diff():
    changes = collect_diff()
    if not changes:
        print("Figma и репозиторий совпадают.")
        return 0
    print(f"# Расхождения Figma и репозитория: {len(changes)}\n")
    print("| Раздел | Токен | Что | В репозитории | В Figma |")
    print("|---|---|---|---|---|")
    for sec, name, what, repo, fig in changes:
        print(f"| {sec} | `{name}` | {what} | {md(repo)} | {md(fig)} |")
    print("\nПринять Figma: `python3 scripts/tokens.py import`. Вернуть Figma к репозиторию: `python3 scripts/tokens.py push`.")
    return 1


def md(s):
    return s.replace("|", "\\|") if s else "—"


def cmd_check():
    changes = collect_diff()
    if changes:
        print(f"✗ tokens/ и снимок расходятся в {len(changes)} местах — запустите diff")
        return 1
    print("✓ tokens/ → TSV совпадает со снимком Figma")
    return 0


# ---------- CSS ----------

def css_name(*parts):
    s = "-".join(parts).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return f"--{PREFIX}-{s}"


def var_name(collection, path):
    if collection == "Colors":
        return css_name("colors", *path)
    return css_name(*path)


def css_value(v, ftype, scopes, collection_of):
    if isinstance(v, str) and v.startswith("{"):
        parts = v[1:-1].split(".")
        return f"var({var_name(parts[0], parts[1:])})"
    if ftype == "number":
        if "FONT_STYLE" in scopes:
            return str(WEIGHTS.get(v, 400))
        return f"{fmt_num(v)}px"
    if ftype == "string":
        if "FONT_STYLE" in scopes:
            return str(WEIGHTS.get(v, 400))
        if "FONT_FAMILY" in scopes:
            return f'"{v}", system-ui, sans-serif'
        return v
    return v


def cmd_build():
    blocks = OrderedDict([(":root", []), ("desktop", []), ("dark", []), ("mobile", [])])
    seen = {}
    for name in COLLECTIONS:
        tree = load_tokens(name)[name]
        modes = tree["$extensions"]["su10"]["modes"]
        for path, leaf in walk(tree):
            ext = leaf.get("$extensions", {}).get("su10", {})
            scopes = ext.get("scopes", [])
            vals = ext.get("modes") or {modes[0]: leaf["$value"]}
            vn = var_name(name, path)
            if vn in seen:
                sys.exit(f"Конфликт имён CSS: {vn} — {seen[vn]} и {name}/{'/'.join(path)}")
            seen[vn] = f"{name}/{'/'.join(path)}"
            first = css_value(vals[modes[0]], leaf["$type"], scopes, name)
            blocks[":root"].append(f"  {vn}: {first};")
            if len(modes) > 1:
                second = css_value(vals[modes[1]], leaf["$type"], scopes, name)
                if second != first:
                    blocks["desktop" if name == "Platform" else "dark"].append(f"  {vn}: {second};")
                    if name == "Platform":
                        blocks["mobile"].append(f"  {vn}: {first};")
    st = load_tokens("styles")
    for path, leaf in walk(st["effect"]):
        shadows = [f"{fmt_num(l['offsetX'])}px {fmt_num(l['offsetY'])}px {fmt_num(l['blur'])}px {fmt_num(l['spread'])}px {l['color']}"
                   for l in leaf["$value"] if "color" in l]
        blurs = [l for l in leaf["$value"] if "color" not in l]
        if shadows:
            blocks[":root"].append(f"  {css_name('effect', *path)}: {', '.join(shadows)};")
        for l in blurs:
            blocks[":root"].append(f"  {css_name('effect', *path)}: {fmt_num(l['blur'])}px;")
    for path, leaf in walk(st["paint"]):
        l = leaf["$value"][0]
        if l["type"] == "SOLID":
            blocks[":root"].append(f"  {css_name('paint', *path)}: {l['color']};")
        else:
            stops = ", ".join(f"{s['color']} {round(s['position'] * 100, 1):g}%" for s in l["stops"])
            blocks[":root"].append(f"  {css_name('paint', *path)}: linear-gradient(180deg, {stops});")
    classes = []
    for path, leaf in walk(st["text"]):
        b = leaf["$extensions"]["su10"]["variables"]
        v = leaf["$value"]
        cls = "." + css_name("text", path[-1])[2:]
        size = css_value(b["fontSize"], "number", [], "") if "fontSize" in b else f"{fmt_num(v['fontSize'])}px"
        weight = css_value(b["fontStyle"], "string", ["FONT_STYLE"], "") if "fontStyle" in b else str(v["fontWeight"])
        lh = css_value(b["lineHeight"], "number", [], "") if "lineHeight" in b else v["lineHeight"]
        classes.append(f"{cls} {{\n  font-family: var({css_name('typo', 'family', 'Inter')});\n  font-size: {size};\n"
                       f"  font-weight: {weight};\n  line-height: {lh};\n  letter-spacing: {'0' if v['letterSpacing'] in ('0%', '0px') else v['letterSpacing']};\n}}")
    dark = "\n".join(blocks["dark"])
    css = [
        "/* SU10 tokens — собрано scripts/tokens.py из tokens/*.json. Руками не править. */",
        "/* Тема: светлая по умолчанию; тёмная — data-theme=\"dark\" на <html> или системная настройка. */",
        f"/* Платформа: Mobile по умолчанию; Desktop — от {DESKTOP_MIN_WIDTH}. */",
        "",
        ":root {\n" + "\n".join(blocks[":root"]) + "\n}",
        "",
        f"@media (min-width: {DESKTOP_MIN_WIDTH}) {{\n  :root {{\n" + "\n".join("  " + l for l in blocks["desktop"]) + "\n  }\n}",
        "",
        "/* Принудительный режим Platform для блока: макет телефона на широком экране и наоборот. */",
        ".su10-mobile {\n" + "\n".join(blocks["mobile"]) + "\n}",
        "",
        ".su10-desktop {\n" + "\n".join(blocks["desktop"]) + "\n}",
        "",
        ":root[data-theme=\"dark\"] {\n" + dark + "\n}",
        "",
        "@media (prefers-color-scheme: dark) {\n  :root:not([data-theme=\"light\"]) {\n" + "\n".join("  " + l for l in blocks["dark"]) + "\n  }\n}",
        "",
        "\n\n".join(classes),
        "",
    ]
    DIST.mkdir(exist_ok=True)
    (DIST / "tokens.css").write_text("\n".join(css), encoding="utf-8")
    print(f"dist/tokens.css: {len(seen)} переменных, {len(classes)} текстовых стилей")
    return 0


# ---------- push: репозиторий → Figma ----------

PUSH_HEAD = r"""// Сгенерировано scripts/tokens.py push. Запускать через use_figma по файлу SU10 Design System
// (fileKey TLPll8pMMVWpHbJdWm6QVe). Ставит в Figma значения из репозитория.
// Удаление переменных скрипт не делает — список лишних в комментарии ниже.
const CHANGES = __CHANGES__;
const parseColor = h => { const n = h.slice(1); const c = i => parseInt(n.slice(i, i + 2), 16) / 255; return { r: c(0), g: c(2), b: c(4), a: n.length === 8 ? c(6) : 1 }; };
const cols = await figma.variables.getLocalVariableCollectionsAsync();
const all = await figma.variables.getLocalVariablesAsync();
const find = (colName, name) => { const col = cols.find(c => c.name === colName); return col && all.find(v => v.variableCollectionId === col.id && v.name === name); };
const touched = [], errors = [];
for (const ch of CHANGES) {
  try {
    const col = cols.find(c => c.name === ch.collection);
    if (!col) throw new Error("нет коллекции " + ch.collection);
    let v = find(ch.collection, ch.name);
    if (!v) { v = figma.variables.createVariable(ch.name, col, ch.type); all.push(v); }
    v.scopes = ch.scopes;
    for (const [modeName, raw] of Object.entries(ch.values)) {
      const mode = col.modes.find(m => m.name === modeName);
      if (!mode) throw new Error("нет режима " + modeName);
      let val;
      if (raw.startsWith("{")) { const m = raw.slice(1, -1); const i = m.indexOf("/"); const target = find(m.slice(0, i), m.slice(i + 1)); if (!target) throw new Error("нет алиаса " + raw); val = figma.variables.createVariableAlias(target); }
      else if (ch.type === "COLOR") val = parseColor(raw);
      else if (ch.type === "FLOAT") val = Number(raw);
      else val = raw;
      v.setValueForMode(mode.modeId, val);
    }
    touched.push(v.id);
  } catch (e) { errors.push(ch.collection + "/" + ch.name + ": " + e.message); }
}
return { mutatedVariableIds: touched, errors };
"""


def cmd_push():
    changes = []
    extra = []
    for name in COLLECTIONS:
        _, frows = read_snapshot_collection(name)
        _, rrows = tokens_to_rows(name)
        for k, r in rrows.items():
            if frows.get(k) != r:
                changes.append({"collection": name, "name": k, "type": r["type"], "scopes": r["scopes"].split(","), "values": r["values"]})
        extra += [f"{name}/{k}" for k in frows if k not in rrows]
    if not changes and not extra:
        print("Figma уже совпадает с репозиторием — пушить нечего.")
        return 0
    # Сначала переменные без алиасов на новые переменные: простая сортировка — примитивы раньше Theme
    changes.sort(key=lambda c: COLLECTIONS.index(c["collection"]))
    js = PUSH_HEAD.replace("__CHANGES__", json.dumps(changes, ensure_ascii=False, indent=1))
    if extra:
        js += "\n// Есть в Figma, нет в репозитории (удалить вручную или принять через import):\n" + "\n".join("//   " + e for e in extra) + "\n"
    out = ROOT / "figma" / "push.generated.js"
    out.write_text(js, encoding="utf-8")
    print(f"figma/push.generated.js: {len(changes)} переменных к записи, {len(extra)} лишних в Figma. Стили этот скрипт не трогает.")
    return 0


def main():
    cmds = {"build": cmd_build, "diff": cmd_diff, "import": cmd_import, "push": cmd_push, "check": cmd_check}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(2)
    sys.exit(cmds[sys.argv[1]]() or 0)


if __name__ == "__main__":
    main()
