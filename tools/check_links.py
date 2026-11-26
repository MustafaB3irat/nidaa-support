#!/usr/bin/env python3
"""Checks that every internal link on the site resolves.

Crawls a running copy of the site (default http://localhost:8000/, start one with
`python3 -m http.server 8000` from the repo root) from every index.html in the repo,
follows href and src values that stay on the site, and reports any that do not answer 200.
Absolute links to the published site (canonical, hreflang) are checked against the local copy.
External links are listed, not fetched.

  python3 tools/check_links.py [base-url]
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED = "https://nidaaprayer.app/"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.found.append(value)


def fetch(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            body = r.read().decode("utf-8", "replace") if "html" in r.headers.get("Content-Type", "") else ""
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/"
    if not base.endswith("/"):
        base += "/"
    pages = []
    for p in ROOT.rglob("index.html"):
        if ".git" in p.parts:
            continue
        where = p.parent.relative_to(ROOT).as_posix()
        pages.append("" if where == "." else where + "/")
    queue = [urljoin(base, p) for p in pages]
    seen, broken, external = set(), [], set()
    while queue:
        url = queue.pop()
        if url in seen:
            continue
        seen.add(url)
        status, body = fetch(url)
        if status != 200:
            broken.append((url, status))
            continue
        parser = Links()
        parser.feed(body)
        for href in parser.found:
            if href.startswith(PUBLISHED):
                href = base + href[len(PUBLISHED):]
            target = urljoin(url, href).split("#")[0]
            if target.startswith(base):
                if target not in seen:
                    queue.append(target)
            elif urlsplit(target).scheme in ("http", "https", "mailto"):
                external.add(target)
    for url, status in broken:
        print(f"BROKEN {status} {url}")
    print(f"checked {len(seen)} local URLs, {len(broken)} broken")
    for url in sorted(external):
        print(f"external (not fetched): {url}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
