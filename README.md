# Nidaa support site

Static pages for Nidaa, served by GitHub Pages at https://mustafab3irat.github.io/nidaa-support/. No build step for Pages: every page is committed as HTML, styled by `style.css`.

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
