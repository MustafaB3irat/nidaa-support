#!/usr/bin/env python3
"""Checks content/privacy/<lang>.json against en.json: the same sections, platforms, paragraph shapes and list
lengths, the same link URLs and **bold** count in every text, no em or en dashes, every ui key present.
Usage: python3 tools/check_translation.py ar fr ...  (no arguments: every language)."""
import json, re, sys
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent / "content" / "privacy"
LINK = re.compile(r"\]\(([^)]+)\)")


def texts(node, path=""):
    """Every translatable string with its path, in order."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, list):
        for i, x in enumerate(node):
            yield from texts(x, f"{path}[{i}]")
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in ("id", "platforms", "lang"):
                continue
            yield from texts(v, f"{path}.{k}")


def shape(node):
    if isinstance(node, str):
        return "s"
    if isinstance(node, list):
        return [shape(x) for x in node]
    if isinstance(node, dict):
        return {k: (v if k in ("id", "platforms", "lang") else shape(v)) for k, v in node.items()}
    return node


def check(code: str, en: dict) -> list[str]:
    d = json.load(open(CONTENT / f"{code}.json", encoding="utf-8"))
    errs = []
    if shape(d["sections"]) != shape(en["sections"]):
        errs.append("sections: shape differs from en.json (ids, platforms, paragraphs, lists or keys)")
    else:
        for (p, t), (_, e) in zip(texts(d["sections"]), texts(en["sections"])):
            if LINK.findall(t) != LINK.findall(e):
                errs.append(f"{p}: link URLs differ")
            if t.count("**") != e.count("**"):
                errs.append(f"{p}: **bold** markers differ")
            if t.strip() == e.strip() and "lang" not in p and code != "en" and len(e) > 40:
                errs.append(f"{p}: still English")
    arcore = [x for s in d["sections"] for x in s.get("paragraphs", []) if isinstance(x, dict) and x.get("lang") == "en"]
    en_arcore = [x for s in en["sections"] for x in s.get("paragraphs", []) if isinstance(x, dict) and x.get("lang") == "en"]
    if arcore != en_arcore:
        errs.append("the ARCore notice must be copied from en.json unchanged")
    missing = set(en["ui"]) - set(d.get("ui", {}))
    if missing:
        errs.append(f"ui keys missing: {sorted(missing)}")
    for p, t in texts({"s": d["sections"], "u": d.get("ui", {}), "e": d["effective_date"]}):
        if "—" in t or "–" in t:
            errs.append(f"{p}: em or en dash")
    return errs


en = json.load(open(CONTENT / "en.json", encoding="utf-8"))
codes = sys.argv[1:] or sorted(p.stem for p in CONTENT.glob("*.json") if p.stem != "en")
bad = 0
for c in codes:
    e = check(c, en)
    bad += bool(e)
    print(f"{c}: " + ("ok" if not e else "\n  " + "\n  ".join(e)))
sys.exit(1 if bad else 0)
