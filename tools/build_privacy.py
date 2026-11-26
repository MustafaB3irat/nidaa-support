#!/usr/bin/env python3
"""Builds the privacy policy pages from content/privacy/<lang>.json.

Writes, for every language that has a JSON file:
  <prefix>privacy/ios/index.html      the iPhone and Apple Watch policy
  <prefix>privacy/android/index.html  the Android and Wear OS policy
  <prefix>privacy/index.html          a router that opens the right one
where <prefix> is "" for English and "<lang>/" for the others.

A language listed in LEGACY_ROUTERS keeps a router at its old URL even before
its JSON exists; that router sends readers to the English pages.

Python 3 standard library only. Run from anywhere:
  python3 tools/build_privacy.py
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "privacy"
SITE = "https://nidaaprayer.app/"
PLATFORMS = ("ios", "android")
STORAGE_KEY = "nidaa.lang"

# The app's 13 languages, in menu order: code, name in its own script, direction.
LANGUAGES = [
    ("en", "English", "ltr"),
    ("ar", "العربية", "rtl"),
    ("fr", "Français", "ltr"),
    ("es", "Español", "ltr"),
    ("tr", "Türkçe", "ltr"),
    ("ru", "Русский", "ltr"),
    ("de", "Deutsch", "ltr"),
    ("id", "Bahasa Indonesia", "ltr"),
    ("ms", "Bahasa Melayu", "ltr"),
    ("ur", "اردو", "rtl"),
    ("fa", "فارسی", "rtl"),
    ("bn", "বাংলা", "ltr"),
    ("ha", "Hausa", "ltr"),
]
LANG_NAME = {code: name for code, name, _ in LANGUAGES}
LANG_DIR = {code: d for code, _, d in LANGUAGES}

# Old URLs the apps already ship: they must keep routing.
LEGACY_ROUTERS = ["ar"]

GLOBE = (
    '<svg class="globe" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
    '<path d="M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>'
)
CHECK = (
    '<svg class="check" aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
)

# Menu behaviour shared by every page: save the chosen language, close on Escape or an outside click.
MENU_JS = (
    "(function(){var k=%s;document.querySelectorAll('.lang-menu a[hreflang]').forEach(function(a){"
    "a.addEventListener('click',function(){try{localStorage.setItem(k,a.getAttribute('hreflang'))}catch(e){}})});"
    "var m=document.querySelector('.lang-menu');if(!m)return;"
    "document.addEventListener('click',function(e){if(m.open&&!m.contains(e.target))m.open=false});"
    "document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m.open){m.open=false;"
    "m.querySelector('summary').focus()}})})();"
) % json.dumps(STORAGE_KEY)


class BuildError(Exception):
    pass


def esc(text: str) -> str:
    return html.escape(text, quote=True)


LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


BOLD = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str, rtl: bool) -> str:
    """Escapes text and turns [text](url) into links. Addresses and URLs stay left to right in RTL pages."""
    out, last = [], 0
    for m in LINK.finditer(text):
        out.append(esc(text[last:m.start()]))
        label, url = m.group(1), m.group(2)
        attrs = f' href="{esc(url)}"'
        if rtl and re.fullmatch(r"[\x00-\x7f]+", label) and ("@" in label or label.startswith("http")):
            attrs += ' dir="ltr"'
        out.append(f"<a{attrs}>{esc(label)}</a>")
        last = m.end()
    out.append(esc(text[last:]))
    return BOLD.sub(r"<strong>\1</strong>", "".join(out))


def pick(value, platform: str, where: str) -> str:
    """A text is a string, or {"ios": ..., "android": ...} when the platforms differ."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and set(value) <= set(PLATFORMS):
        if platform not in value:
            raise BuildError(f"{where}: no text for {platform}")
        return value[platform]
    raise BuildError(f"{where}: expected a string or an object with ios/android keys")


def load(code: str) -> dict:
    path = CONTENT / f"{code}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise BuildError(f"{path.name}: {e}") from e
    if data.get("lang") != code:
        raise BuildError(f"{path.name}: \"lang\" must be {code!r}")
    return data


def check_structure(code: str, data: dict, reference: dict) -> list[str]:
    """Warnings when a translation's sections differ from English's."""
    warnings = []
    ref = [(s["id"], tuple(s["platforms"])) for s in reference["sections"]]
    got = [(s.get("id"), tuple(s.get("platforms", ()))) for s in data.get("sections", [])]
    if ref != got:
        warnings.append(f"{code}: sections differ from en.json (ids, order or platforms)")
    missing = sorted(set(reference["ui"]) - set(data.get("ui", {})))
    if missing:
        warnings.append(f"{code}: ui keys missing: {', '.join(missing)} (English used)")
    return warnings


def prefix(code: str) -> str:
    return "" if code == "en" else f"{code}/"


def policy_path(code: str, platform: str) -> str:
    return f"{prefix(code)}privacy/{platform}/"


def router_path(code: str) -> str:
    return f"{prefix(code)}privacy/"


def rel(from_dir: str, to: str) -> str:
    """Relative link from a page directory (site-relative, ending in /) to a site-relative path."""
    depth = from_dir.count("/")
    return "../" * depth + to if to else "../" * depth or "./"


def home_and_support(code: str) -> tuple[str, str]:
    """This language's home and support pages when they exist, else English's."""
    p = prefix(code)
    home = p if (ROOT / p / "index.html").exists() else ""
    support = f"{p}support/" if (ROOT / p / "support" / "index.html").exists() else "support/"
    return home, support


def header(ui: dict, code: str, here: str, menu: str) -> str:
    home, support = home_and_support(code)
    r = lambda p: rel(here, p)  # noqa: E731
    return (
        f'<header><a class="brand" href="{r(home)}"><img src="{r("icon.png")}" alt="" width="44" height="44">'
        f'<span>{esc(ui["site_name"])}<small>{esc(ui["tagline"])}</small></span></a>'
        f'<nav aria-label="{esc(ui["nav_label"])}"><a href="{r(support)}">{esc(ui["nav_support"])}</a>'
        f'<a href="{r(router_path(code))}">{esc(ui["nav_privacy"])}</a>{menu}</nav></header>'
    )


def footer(ui: dict, code: str, here: str) -> str:
    _, support = home_and_support(code)
    return (
        f'<footer><span>{esc(ui["site_name"])}</span><a href="{rel(here, support)}">{esc(ui["footer_support"])}</a>'
        f'<a href="{rel(here, router_path(code))}">{esc(ui["footer_privacy"])}</a></footer>'
    )


def language_menu(ui: dict, current: str, here: str, target, available: list[str]) -> str:
    items = []
    for code in available:
        name, d = LANG_NAME[code], LANG_DIR[code]
        mark = ' aria-current="page"' if code == current else ""
        items.append(
            f'<li><a href="{rel(here, target(code))}" hreflang="{code}" lang="{code}"{mark}>'
            f'<span dir="{d}">{esc(name)}</span>'
            f"{CHECK if code == current else ''}</a></li>"
        )
    return (
        f'<details class="lang-menu"><summary>{GLOBE}<span class="sr">{esc(ui["language_label"])}: </span>'
        f'<span class="lang-name">{esc(LANG_NAME[current])}</span></summary>'
        f'<ul class="lang-list" aria-label="{esc(ui["language_label"])}">{"".join(items)}</ul></details>'
    )


def head(code: str, title: str, description: str, here: str, alternates: dict, extra: str = "") -> str:
    links = "".join(
        f'<link rel="alternate" hreflang="{c}" href="{SITE}{p}">' for c, p in alternates.items()
    )
    return (
        f'<!doctype html><html lang="{code}" dir="{LANG_DIR[code]}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{esc(description)}"><title>{esc(title)}</title>'
        f'<link rel="canonical" href="{SITE}{here}"><link rel="icon" href="{rel(here, "icon.png")}">'
        f'<link rel="stylesheet" href="{rel(here, "style.css")}">{links}{extra}</head><body>'
    )


def ui_of(data: dict, english: dict) -> dict:
    return {**english["ui"], **data.get("ui", {})}


def policy_page(code: str, data: dict, english: dict, platform: str, available: list[str]) -> str:
    ui = ui_of(data, english)
    rtl = LANG_DIR[code] == "rtl"
    here = policy_path(code, platform)
    other = "android" if platform == "ios" else "ios"
    alternates = {c: policy_path(c, platform) for c in available}
    alternates["x-default"] = policy_path("en", platform)
    menu = language_menu(ui, code, here, lambda c: policy_path(c, platform), available)
    platform_name = pick(ui["platform_name"], platform, "ui.platform_name")

    body = [f'<p class="updated">{esc(ui["effective_date"].replace("{date}", pick(data["effective_date"], platform, "effective_date")))}</p>']
    switch = pick(ui["platform_switch"], platform, "ui.platform_switch").replace("{url}", rel(here, policy_path(code, other)))
    body.append(f'<p class="platform-switch">{inline(switch, rtl)}</p>')
    if code != "en":
        note = ui["translation_note"].replace("{url}", rel(here, policy_path("en", platform)))
        body.append(f'<p class="translation-note">{inline(note, rtl)}</p>')

    for s in data["sections"]:
        sid = s.get("id", "?")
        if platform not in s.get("platforms", PLATFORMS):
            continue
        if "heading" in s:
            body.append(f'<h2 id="{esc(sid)}">{inline(pick(s["heading"], platform, sid + ".heading"), rtl)}</h2>')
        for i, p in enumerate(s.get("paragraphs", [])):
            where = f"{sid}.paragraphs[{i}]"
            attrs = ""
            if isinstance(p, dict) and "list" in p:
                items = []
                for j, item in enumerate(p["list"]):
                    if isinstance(item, dict) and "text" in item:
                        if platform not in item.get("platforms", PLATFORMS):
                            continue
                        item = item["text"]
                    items.append(f"<li>{inline(pick(item, platform, f'{where}.list[{j}]'), rtl)}</li>")
                body.append(f"<ul>{''.join(items)}</ul>")
                continue
            if isinstance(p, dict) and "text" in p:
                if platform not in p.get("platforms", PLATFORMS):
                    continue
                if p.get("lang") and p["lang"] != code:
                    attrs = f' lang="{esc(p["lang"])}" dir="{LANG_DIR.get(p["lang"], "ltr")}"'
                p = p["text"]
            text = pick(p, platform, where)
            body.append(f"<p{attrs}>{inline(text, rtl and not attrs)}</p>")

    return (
        head(code, f'{ui["title"]} · {platform_name} · {ui["site_name"]}', ui["description"], here, alternates)
        + header(ui, code, here, menu)
        + f'<main><section class="hero"><p class="eyebrow">{esc(pick(ui["eyebrow"], platform, "ui.eyebrow"))}</p>'
        f'<h1>{esc(ui["title"])}</h1><p>{esc(ui["description"])}</p></section>'
        f'<article>{"".join(body)}</article></main>'
        + footer(ui, code, here)
        + f'<script src="{rel(here, "lang-menu.js")}"></script></body></html>\n'
    )


def router_script(code: str, here: str, available: list[str], has_content: bool, auto_language: bool) -> str:
    """Picks the platform (and on the English URL the language) and opens that policy at once."""
    cfg = {
        "lang": code if has_content else "en",
        "auto": auto_language,
        "langs": available,
        "key": STORAGE_KEY,
        "base": rel(here, ""),
    }
    # The site's security policy allows no inline script, so the code lives in router.js and
    # each page passes its settings in a data attribute.
    return (
        f'<script src="{rel(here, "router.js")}" '
        f'data-config="{esc(json.dumps(cfg, ensure_ascii=False))}"></script>'
    )


ROUTER_JS = (
    "(function(c){var n=navigator,ua=n.userAgent||'',d=n.userAgentData,p=null;"
    "if(/Android/i.test(ua)||(d&&d.platform==='Android'))p='android';"
    "else if(/iPhone|iPad|iPod|Macintosh/i.test(ua))p='ios';"
    "var l=c.lang;if(c.auto){var s=null;try{s=localStorage.getItem(c.key)}catch(e){}"
    "if(c.langs.indexOf(s)<0){s=null;var w=n.languages||[n.language||''];"
    "for(var i=0;i<w.length&&!s;i++){var b=String(w[i]).toLowerCase().split('-')[0];"
    "if(c.langs.indexOf(b)>=0)s=b}}if(s)l=s}"
    "var f=l==='en'?'':l+'/';"
    "if(p)location.replace(c.base+f+'privacy/'+p+'/'+location.hash);"
    "else if(l!==c.lang)location.replace(c.base+f+'privacy/'+location.hash)"
    "})(JSON.parse(document.currentScript.dataset.config));\n"
)


def router_page(code: str, data: dict | None, english: dict, available: list[str]) -> str:
    has_content = data is not None
    shown = code if has_content else "en"
    ui = ui_of(data or english, english)
    here = router_path(code)
    page_lang = code if has_content else "en"
    alternates = {c: router_path(c) for c in available}
    alternates["x-default"] = router_path("en")
    menu = language_menu(ui, shown, here, router_path, available)
    choices = "".join(
        f'<li><a class="button" href="{rel(here, policy_path(shown, p))}">'
        f'{esc(pick(ui["router_choice"], p, "ui.router_choice"))} <span aria-hidden="true">'
        f'{"←" if LANG_DIR[page_lang] == "rtl" else "→"}</span></a></li>'
        for p in PLATFORMS
    )
    script = router_script(code, here, available, has_content, auto_language=(code == "en"))
    html_doc = (
        head(page_lang, f'{ui["router_title"]} · {ui["site_name"]}', ui["description"], here, alternates, script)
        + header(ui, shown, here, menu)
        + f'<main><section class="hero"><p class="eyebrow">{esc(ui["router_eyebrow"])}</p>'
        f'<h1>{esc(ui["title"])}</h1><p>{esc(ui["description"])}</p></section>'
        f'<article><h2>{esc(ui["router_title"])}</h2><p>{esc(ui["router_intro"])}</p>'
        f'<ul class="platform-choices">{choices}</ul></article></main>'
        + footer(ui, shown, here)
        + f'<script src="{rel(here, "lang-menu.js")}"></script></body></html>\n'
    )
    return html_doc


def write(path: str, text: str) -> None:
    out = ROOT / path / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


def main() -> int:
    try:
        english = load("en")
        datas = {"en": english}
        for code, _, _ in LANGUAGES[1:]:
            if (CONTENT / f"{code}.json").exists():
                datas[code] = load(code)
        available = [c for c, _, _ in LANGUAGES if c in datas]
        warnings = [w for c, d in datas.items() if c != "en" for w in check_structure(c, d, english)]

        (ROOT / "router.js").write_text(ROUTER_JS, encoding="utf-8")
        (ROOT / "lang-menu.js").write_text(MENU_JS + "\n", encoding="utf-8")
        print("wrote router.js, lang-menu.js")
        for code in available:
            for platform in PLATFORMS:
                write(policy_path(code, platform), policy_page(code, datas[code], english, platform, available))
        for code in [c for c, _, _ in LANGUAGES if c in datas or c in LEGACY_ROUTERS]:
            write(router_path(code), router_page(code, datas.get(code), english, available))
    except BuildError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"languages: {', '.join(available)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
