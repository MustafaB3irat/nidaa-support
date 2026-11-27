# Nidaa support site

Static pages for Nidaa, served by Cloudflare Workers as static files (`wrangler.jsonc`), deployed from `main`. GitHub Pages at https://mustafab3irat.github.io/nidaa-support/ stays up for apps that still link it. No build step for either: every page is committed as HTML, styled by `style.css`.

- `_headers` sets the security headers. Its policy allows no inline script or style, so scripts live in files: `router.js` and `lang-menu.js` are written by `tools/build_privacy.py`, `home.js` is written by hand.
- `.assetsignore` keeps the repository's own files (`tools/`, `content/`, this README) off the site.

## Privacy policy pages

The privacy policy is generated, one page per platform per language:

| URL | What |
|---|---|
| `/privacy/ios/`, `/privacy/android/` | English policy for iPhone and Apple Watch, and for Android and Wear OS |
| `/<lang>/privacy/ios/`, `/<lang>/privacy/android/` | The same in another app language (`ar`, `fr`, `es`, `tr`, `ru`, `de`, `id`, `ms`, `ur`, `fa`, `bn`, `ha`) |
| `/privacy/`, `/<lang>/privacy/` | Routers: open the policy for the reader's device (Android, or iPhone, iPad and Mac). On `/privacy/` the language is the one chosen in the globe menu, else the browser's, else English. Without JavaScript, or on other devices, they show both choices. Shipped apps and the App Store listing link these URLs. |

Content lives in `content/privacy/<lang>.json` (`en.json` is the reference and explains the format to translators in `_translators`). To change the policy or add a language:

```bash
python3 tools/build_privacy.py          # writes every page from the JSON files
python3 -m http.server 8000 &           # from the repo root
python3 tools/check_links.py            # every internal link must answer 200
kill %1
```

Commit the JSON and the generated pages together. Never edit the generated `privacy/` pages by hand. A language appears in the globe menu once its JSON exists; the build warns when a translation's sections differ from English. When the policy text changes, update `effective_date` for that platform in every language.

## Home pages

The home page is generated too, one per language that has `content/home/<lang>.json` (`en.json` is the reference; its `_translators` note explains the format). The header and footer words come from `content/privacy/<lang>.json`, so a language needs both files. Values are inserted as HTML: `&nbsp;` is fine, `<` and straight double quotes are refused.

```bash
python3 tools/build_home.py             # writes /index.html and /<lang>/index.html
python3 tools/build_privacy.py          # rerun when a language gets its first home page, so its privacy pages link to it
```

Never edit the generated `index.html` files by hand. The App Store reviews quoted on the page, the rating, and the feature icons live in `tools/build_home.py`.

**Download tracking.** The site tracks nothing. To count downloads that came from it, App Store Connect's App Analytics reads a campaign tag on the App Store link:

- `PROVIDER_TOKEN` in `tools/build_home.py` is the `pt` value of the account's campaign links (App Store Connect, App Analytics, Campaigns). Campaigns: `website` (store buttons), `banner` (Safari's Smart App Banner), `qr` (desktop QR code, via `/qr`), `get` (`/get`, for bios and posts). A campaign appears in App Analytics only after installs come through it.
- The QR code shown beside the App Store badge on desktop (`img/qr-app-store.svg`) opens `nidaaprayer.app/qr`. `/qr` and `/get` are redirects in `_redirects`: add the same `pt` there with `ct=qr` and `ct=get`. Use `nidaaprayer.app/get` in social bios and reel captions.
- To redraw the QR code (only if `/qr` itself changes): `python3 -m pip install segno`, then `segno.make("https://nidaaprayer.app/qr", error="m").save("img/qr-app-store.svg", border=2, dark="#102634", light="#ffffff", xmldecl=False, omitsize=True)`.

**Link preview.** `img/og.png` (1200×630) is what WhatsApp, iMessage, X and others show when the site is shared. It is drawn by `tools/og-card.html` with the site's own CSS: serve the repo root, open that page at 1200×630 in Chrome (device toolbar, 2× scale) and capture a screenshot, then scale it to 1200×630.
