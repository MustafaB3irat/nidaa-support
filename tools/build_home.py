#!/usr/bin/env python3
"""Builds the home page in every language from content/home/<lang>.json.

Writes <prefix>index.html, where <prefix> is "" for English and "<lang>/" for the
others. The header and footer words (tagline, Support, Privacy, Language) come
from content/privacy/<lang>.json, so every page of a language says them the same way.

Run tools/build_privacy.py after this one when a language gets its first home
page: the privacy pages then link their logo to it.

Python 3 standard library only. Run from anywhere:
  python3 tools/build_home.py
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_privacy import (  # noqa: E402
    COPYRIGHT,
    LANG_DIR,
    LANGUAGES,
    ROOT,
    SITE,
    BuildError,
    home_and_support,
    language_menu,
    prefix,
    rel,
    router_path,
)

CONTENT = ROOT / "content" / "home"
PRIVACY = ROOT / "content" / "privacy"

APP_ID = "6818994960"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.mustafabirat.nidaa"
# App Store Connect campaign tags, so App Analytics counts downloads that came from the site.
# PROVIDER_TOKEN is the "pt" value of a campaign link made in App Store Connect
# (App Analytics, Campaigns). Empty: the links carry no tag.
PROVIDER_TOKEN = "126337634"
CAMPAIGN = "website"
# The QR code opens nidaaprayer.app/qr, which _redirects sends to the App Store with its
# own campaign tag, so the printed code never has to change.
QR_IMAGE = "img/qr-app-store.svg"


def app_store_url(campaign: str) -> str:
    url = f"https://apps.apple.com/app/id{APP_ID}"
    return f"{url}?pt={PROVIDER_TOKEN}&ct={campaign}&mt=8" if PROVIDER_TOKEN else url


def banner_meta() -> str:
    """Safari's Smart App Banner; affiliate-data carries the campaign tag (ct=banner)."""
    content = f"app-id={APP_ID}"
    if PROVIDER_TOKEN:
        content += f", affiliate-data=pt={PROVIDER_TOKEN}&amp;ct=banner"
    return content


# Store badges drawn for a language; the others use the English ones.
BADGES = {"en", "ar"}

# The link preview shown when the site is shared (WhatsApp, iMessage, X, Instagram).
OG_IMAGE = "img/og.png"
OG_SIZE = (1200, 630)
OG_LOCALE = {
    "en": "en_US", "ar": "ar_AR", "fr": "fr_FR", "es": "es_ES", "tr": "tr_TR", "ru": "ru_RU",
    "de": "de_DE", "id": "id_ID", "ms": "ms_MY", "ur": "ur_PK", "fa": "fa_IR", "bn": "bn_BD", "ha": "ha_NG",
}

# Real App Store reviews, quoted as written, shown with a first name and last initial.
# A page shows the reviews in its own language first. "country" is in the review's language.
REVIEWS = [
    {"lang": "en", "title": "Great app",
     "text": "The athan is clear and beautiful, the prayer times are accurate, and the reminders arrive right when I need them. Everything is clean and intuitive, with no clutter or confusing menus.",
     "by": "Hiba B.", "country": "United States"},
    {"lang": "en", "title": "Neat design, no ads",
     "text": "It’s nice to hear the Athan here in Mountain View, even if it’s from my phone. I really liked the map view of nearby mosques.",
     "by": "Mohammad M.", "country": "United States"},
    {"lang": "en", "title": "Excellent app",
     "text": "Simple, user-friendly, and very helpful for keeping track of prayer times. Highly recommended.",
     "by": "Hamzah A.", "country": "United States"},
    {"lang": "ar", "title": "برنامج أكثر من رائع!",
     "text": "أول برنامج مجاني بدون إعلانات. خلفية مريحة جدا ومواقيت صلاة دقيقة.",
     "by": "نور الهدى", "country": "الولايات المتحدة"},
]

# One bare line icon per item of "Everything around the five prayers", in the same order.
def icon(body: str) -> str:
    return (
        '<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


MORE_ICONS = [
    # offline: a signal arc, struck through
    icon('<path d="M4.5 9.5a11 11 0 0 1 15 0"/><path d="M7.5 12.8a6.5 6.5 0 0 1 9 0"/><circle cx="12" cy="16.5" r="1"/><path d="M4 4l16 16"/>'),
    # the times your mosque keeps: a dome with a minaret
    icon('<path d="M4 20h16"/><path d="M6 20v-6a6 6 0 0 1 12 0v6"/><path d="M12 8V5.5"/><path d="M10 20v-3a2 2 0 0 1 4 0v3"/>'),
    # the month on one page
    icon('<rect x="3.5" y="5" width="17" height="15" rx="2.5"/><path d="M3.5 9.5h17"/><path d="M8 3v4M16 3v4"/><path d="M7.5 13h2M11 13h2M14.5 13h2M7.5 16.5h2M11 16.5h2"/>'),
    # Sunnah days: a bell
    icon('<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>'),
    # widgets
    icon('<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>'),
    # Siri and Shortcuts: a voice wave
    icon('<path d="M4 12h1.5M8 8.5v7M12 5v14M16 8.5v7M18.5 12H20"/>'),
    # the Hijri date: a crescent
    icon('<path d="M19 14.5A7.5 7.5 0 1 1 10.5 5a6 6 0 0 0 8.5 9.5z"/>'),
    # in your language
    icon('<path d="M3.5 6h9M8 4v2M10.5 6c-.8 4-3.2 7-6.5 8.5"/><path d="M6 10c1.2 2 3 3.5 5 4.3"/><path d="M12.5 20l4-9 4 9M14 17h5"/>'),
]


STARS = "★★★★★"
RATING = "5.0"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise BuildError(f"{path.relative_to(ROOT)}: {e}") from e


def merged(base: dict, over: dict) -> dict:
    """The translation's values over English's, so a missing string shows in English, not as a hole."""
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            out[k] = merged(base[k], v)
        elif isinstance(v, list) and isinstance(base.get(k), list) and len(v) == len(base[k]):
            out[k] = [merged(b, o) if isinstance(b, dict) and isinstance(o, dict) else o for b, o in zip(base[k], v)]
        else:
            out[k] = v
    return out


def shape(value) -> object:
    if isinstance(value, dict):
        return {k: shape(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [shape(v) for v in value]
    return None


def check_text(code: str, value, where: str = "") -> None:
    """Values go into the page as HTML: allow entities like &nbsp; but no tags or straight double quotes."""
    if isinstance(value, dict):
        for k, v in value.items():
            if not k.startswith("_"):
                check_text(code, v, f"{where}.{k}" if where else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            check_text(code, v, f"{where}[{i}]")
    elif isinstance(value, str) and ("<" in value or '"' in value):
        raise BuildError(f"content/home/{code}.json {where}: no < or straight double quotes (use “ ” instead)")


def check_structure(code: str, data: dict, english: dict) -> list[str]:
    a, b = shape({k: v for k, v in english.items() if k != "lang"}), shape({k: v for k, v in data.items() if k != "lang"})
    return [] if a == b else [f"content/home/{code}.json has different keys or list lengths than en.json"]


def store_badges(code: str, here: str, d: dict, lazy: bool) -> str:
    badge = code if code in BADGES else "en"
    eager = "" if not lazy else ' loading="lazy"'
    return (
        '<div class="stores">\n'
        f'      <a class="store" href="{app_store_url(CAMPAIGN)}"><img src="{rel(here, f"img/app-store-badge-{badge}.svg")}" alt="{d["store"]["app_store_alt"]}" width="150" height="50"{eager}></a>\n'
        f'      <a class="store play" href="{PLAY_URL}"><img src="{rel(here, f"img/google-play-badge-{badge}.png")}" alt="{d["store"]["play_alt"]}" width="168" height="50" loading="lazy"></a>\n'
        f'      <img class="qr" src="{rel(here, QR_IMAGE)}" alt="{d["store"]["qr_alt"]}" width="100" height="100" loading="lazy">\n'
        "    </div>"
    )


def review_cards(code: str) -> str:
    ordered = [r for r in REVIEWS if r["lang"] == code] + [r for r in REVIEWS if r["lang"] != code]
    cards = []
    for r in ordered:
        attrs = "" if r["lang"] == code else f' lang="{r["lang"]}" dir="{LANG_DIR[r["lang"]]}"'
        cards.append(
            f'    <li class="rv"{attrs}><blockquote><p class="praise-head">{esc(r["title"])}</p><p>{esc(r["text"])}</p></blockquote>'
            f'<p class="praise-by">{esc(r["by"])} · {esc(r["country"])}</p></li>'
        )
    return "\n".join(cards)


def page(code: str, d: dict, ui: dict, available: list[str]) -> str:
    here = prefix(code)
    r = lambda p: rel(here, p)  # noqa: E731
    _, support = home_and_support(code)
    en = "" if code == "en" else ' lang="en"'  # the drawn Lock Screen is in English, like the screenshots
    menu = language_menu(ui, code, here, prefix, available)
    alternates = "\n".join(f'<link rel="alternate" hreflang="{c}" href="{SITE}{prefix(c)}">' for c in available)
    s, n, c, w, m = d["screens"], d["notes"], d["calls"], d["wrist"], d["more"]
    watch_files = [("", "watch-today.webp"), (" sand", "watch-face.webp"), (" sage", "watch-qibla.webp")]
    watches = "\n".join(
        f'    <li class="{"lead " if i == 1 else ""}rv"><figure class="watch{cls}"><div class="strap top"></div><div class="case"><div class="screen">'
        f'<img src="{r("img/" + f)}" alt="{item["alt"]}" width="416" height="496" loading="lazy"></div></div>'
        f'<div class="strap bot"><i></i><i></i><i></i></div></figure><div><h3>{item["title"]}</h3><p>{item["text"]}</p></div></li>'
        for i, ((cls, f), item) in enumerate(zip(watch_files, w["watches"]))
    )
    more = "\n".join(
        f'    <li class="rv">{svg}<div><h3>{i["title"]}</h3><p>{i["text"]}</p></div></li>' for svg, i in zip(MORE_ICONS, m["items"])
    )
    chapters = "\n".join(
        f'    <div class="chapter" data-step="{i}"><h3>{ch["title"]}</h3><p>{ch["text"]}</p></div>'
        for i, ch in enumerate(c["chapters"], 1)
    )
    ow, oh = OG_SIZE
    return f"""<!doctype html>
<html lang="{code}" dir="{LANG_DIR[code]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-itunes-app" content="{banner_meta()}">
<title>{d["title"]}</title>
<meta name="description" content="{d["description"]}">
<link rel="canonical" href="{SITE}{here}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Nidaa">
<meta property="og:title" content="{d["title"]}">
<meta property="og:description" content="{d["description"]}">
<meta property="og:url" content="{SITE}{here}">
<meta property="og:image" content="{SITE}{OG_IMAGE}">
<meta property="og:image:width" content="{ow}">
<meta property="og:image:height" content="{oh}">
<meta property="og:image:alt" content="{s["today"]}">
<meta property="og:locale" content="{OG_LOCALE[code]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r("icon.png")}">
<link rel="stylesheet" href="{r("style.css")}">
<link rel="stylesheet" href="{r("home.css")}">
{alternates}
<link rel="alternate" hreflang="x-default" href="{SITE}">
<script src="{r("home.js")}"></script>
</head>
<body class="home">
<header><a class="brand" href="./"><img src="{r("icon.png")}" alt="" width="44" height="44"><span>{esc(ui["site_name"])}<small>{esc(ui["tagline"])}</small></span></a><nav aria-label="{esc(ui["nav_label"])}"><a href="{r(support)}">{esc(ui["nav_support"])}</a><a href="{r(router_path(code))}">{esc(ui["nav_privacy"])}</a>{menu}</nav></header>

<main>
<section class="stage" aria-labelledby="title">
  <div class="stage-copy">
    <h1 id="title">{d["hero"]["title"]}</h1>
    <p>{d["hero"]["lede"]}</p>
    {store_badges(code, here, d, lazy=False)}
  </div>

  <div class="trio">
    <figure class="phone side first"><div class="screen" dir="ltr"><img src="{r("img/mosques.webp")}" alt="{s["mosques"]}" width="600" height="1304" loading="lazy"></div></figure>
    <figure class="phone mid"><div class="screen" dir="ltr" data-countdown="7860"><img src="{r("img/today.webp")}" alt="{s["today"]}" width="600" height="1304" fetchpriority="high"></div></figure>
    <figure class="phone side last"><div class="screen" dir="ltr"><img src="{r("img/qibla-ar.webp")}" alt="{s["qibla"]}" width="600" height="1305" loading="lazy"></div></figure>
  </div>

  <ul class="trio-notes">
{chr(10).join(f'    <li><h2>{x["title"]}</h2><p>{x["text"]}</p></li>' for x in n)}
  </ul>
</section>

<section class="tour">
  <ul>
    <li><figure class="phone"><div class="screen" dir="ltr"><img src="{r("img/mosques.webp")}" alt="{s["mosques"]}" width="600" height="1304" loading="lazy"></div></figure><h2>{n[0]["title"]}</h2><p>{n[0]["text"]}</p></li>
    <li><figure class="phone"><div class="screen" dir="ltr"><img src="{r("img/qibla-ar.webp")}" alt="{s["qibla"]}" width="600" height="1305" loading="lazy"></div></figure><h2>{n[2]["title"]}</h2><p>{n[2]["text"]}</p></li>
  </ul>
</section>

<section class="praise" aria-labelledby="praise-title">
  <h2 id="praise-title" class="rv">{d["praise"]["title"]}</h2>
  <p class="praise-score rv"><b>{RATING}</b><span aria-hidden="true">{STARS}</span></p>
  <ul>
{review_cards(code)}
  </ul>
</section>

<section class="calls" aria-labelledby="calls-title">
  <div class="calls-text">
    <h2 id="calls-title" class="section-title rv">{c["title"]}</h2>
{chapters}
  </div>
  <div class="calls-device">
    <figure class="phone lock" dir="ltr" data-step="3" aria-label="{c["lock_label"]}">
      <div class="screen">
        <div class="lock-top"{en}><p class="lock-date">Thursday 26 November</p><p class="lock-time">7:30</p></div>
        <div class="lock-stack">
          <div class="live s3"{en}>
            <div class="live-row">
              <div><p class="live-name"><img src="{r("img/icon.webp")}" alt="" width="192" height="192" loading="lazy">Isha <span lang="ar">العشاء</span></p><p class="live-at">at 7:57 PM</p></div>
              <p class="live-left" data-live="1632">27:12</p>
            </div>
            <div class="live-bar"><span></span></div>
            <div class="live-ends"><span>Maghrib 6:41</span><span>Isha 7:57</span></div>
          </div>
          <div class="note s2">
            <img src="{r("img/icon.webp")}" alt="" width="192" height="192" loading="lazy">
            <div{en}><p class="note-head"><b>Maghrib ends soon</b><span>3m ago</span></p><p>30 min left in Maghrib time. Pray if you haven’t yet.</p></div>
          </div>
          <div class="note s1">
            <img src="{r("img/icon.webp")}" alt="" width="192" height="192" loading="lazy">
            <div{en}><p class="note-head"><b>Maghrib prayer</b><span>49m ago</span></p><p>It’s time for Maghrib prayer.</p></div>
          </div>
        </div>
      </div>
    </figure>
  </div>
</section>

<section class="wrist" aria-labelledby="wrist-title">
  <div class="wrist-copy rv">
    <h2 id="wrist-title" class="section-title">{w["title"]}</h2>
    <p>{w["lede"]}</p>
  </div>
  <ul class="watches">
{watches}
  </ul>
</section>

<section class="more" aria-labelledby="more-title">
  <h2 id="more-title" class="section-title rv">{m["title"]}</h2>
  <ul class="grid">
{more}
  </ul>
</section>

<section class="quiet rv" aria-labelledby="quiet-title">
  <h2 id="quiet-title">{d["quiet"]["title"]}</h2>
  <p>{d["quiet"]["text"]}</p>
  <a href="{r(router_path(code))}">{d["quiet"]["link"]}</a>
</section>

<section class="get rv" aria-labelledby="get-title">
  <img class="get-icon" src="{r("img/icon.webp")}" alt="" width="192" height="192" loading="lazy">
  <h2 id="get-title">{d["get"]["title"]}</h2>
  {store_badges(code, here, d, lazy=True)}
</section>
</main>

<footer><span dir="ltr">{esc(COPYRIGHT)}</span><a href="{r(support)}">{esc(ui["footer_support"])}</a><a href="{r(router_path(code))}">{esc(ui["footer_privacy"])}</a></footer>
<script src="{r("lang-menu.js")}"></script>
</body>
</html>
"""


def main() -> int:
    try:
        english = load(CONTENT / "en.json")
        privacy_en = load(PRIVACY / "en.json")
        datas = {"en": english}
        for code, _, _ in LANGUAGES[1:]:
            if (CONTENT / f"{code}.json").exists():
                datas[code] = load(CONTENT / f"{code}.json")
        available = [c for c, _, _ in LANGUAGES if c in datas]
        for code, d in datas.items():
            check_text(code, d)
        warnings = [w for code, d in datas.items() if code != "en" for w in check_structure(code, d, english)]
        for code in available:
            p = PRIVACY / f"{code}.json"
            ui = {**privacy_en["ui"], **(load(p).get("ui", {}) if p.exists() else {})}
            d = merged(english, datas[code])
            out = ROOT / prefix(code) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(page(code, d, ui, available), encoding="utf-8")
            print(f"wrote {out.relative_to(ROOT)}")
    except BuildError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"languages: {', '.join(available)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
