#!/usr/bin/env python3
"""Контрольные суммы снимка figma/snapshot/*.tsv.

Сравнивают с результатом figma/checksum.js, запущенного в Figma.
  python3 scripts/checksum.py              — сумма файла и число строк
  python3 scripts/checksum.py --rows       — плюс сумма каждой строки
  python3 scripts/checksum.py --compare figma.json — сверка с ответом checksum.js
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "figma" / "snapshot"


def fnv(s: str) -> str:
    """FNV-1a по UTF-16 — так же, как charCodeAt в figma/checksum.js."""
    h = 0x811C9DC5
    data = s.encode("utf-16-le")
    for i in range(0, len(data), 2):
        h ^= data[i] | (data[i + 1] << 8)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def local():
    out = {}
    for p in sorted(SNAP.glob("*.tsv")):
        lines = p.read_text(encoding="utf-8").rstrip("\n").split("\n")
        out[p.name] = {"lines": len(lines), "file": fnv("\n".join(lines)), "rows": [fnv(l) for l in lines], "text": lines}
    return out


def main():
    loc = local()
    if "--compare" in sys.argv:
        remote = json.loads(pathlib.Path(sys.argv[sys.argv.index("--compare") + 1]).read_text())
        bad = 0
        for name in sorted(set(loc) | set(remote)):
            if name not in loc or name not in remote:
                print(f"✗ {name}: есть только {'в Figma' if name in remote else 'в репозитории'}")
                bad += 1
                continue
            a, b = loc[name], remote[name]
            if a["file"] == b["file"]:
                print(f"✓ {name}: {a['lines']} строк")
                continue
            bad += 1
            rrows = b["rows"].split()
            print(f"✗ {name}: строк {a['lines']} у нас, {b['lines']} в Figma")
            for i, h in enumerate(a["rows"]):
                if i >= len(rrows) or rrows[i] != h:
                    print(f"   строка {i + 1}: {a['text'][i][:120]}")
        sys.exit(1 if bad else 0)
    for name, d in loc.items():
        print(f"{name}\t{d['lines']}\t{d['file']}" + ("\t" + " ".join(d["rows"]) if "--rows" in sys.argv else ""))


if __name__ == "__main__":
    main()
