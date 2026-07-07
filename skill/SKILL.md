---
name: app-vault
description: Manage a unified app store metadata catalog (Obsidian vault + local static viewer). Save/update/delete the current app project's name, package name, short/full descriptions, icon, feature graphic, screenshots, and privacy policy into the vault, generate missing assets (store screenshots, icon, feature graphic), and rebuild the searchable static catalog page. Triggers - "/app-vault", "app-vault generate", "save this app to the vault", "open the app catalog", "list my apps", "take store screenshots", "capture app screenshots for the store", "generate a feature graphic", "generate an app icon for the vault". When asked to "take screenshots" inside an app project, offer the store-capture pipeline (generate screenshots).
---

# app-vault — unified app store metadata catalog

Accumulates every app's store listing assets (name, package name, descriptions,
icon, graphics, screenshots, policy URLs) in **one place** (an Obsidian-compatible
markdown vault) and browses them through a **local static page**.

## Paths

| Item | Path |
|------|------|
| Vault (source of truth) | set via `APP_VAULT_DIR` or `--vault` (e.g. `~/Documents/obsidian-vault/apps/`) |
| Per-app data | `<vault>/<slug>/app.md` + `<vault>/<slug>/assets/` |
| Generated viewer | `<vault>/_site/index.html` (build artifact — never edit directly) |
| Build script | `<this skill dir>/scripts/build.py` |

## Subcommands

When invoked with no arguments, infer from context: if working inside an app
project, run `save`; otherwise `list`.

### save (default) — save/update the current project into the vault

1. **Detect the project**: collect identifiers from cwd (or a user-specified project) per stack:
   - Flutter: `pubspec.yaml` (name/version) + `android/app/build.gradle*` (applicationId)
   - Native Android: `applicationId`/`versionName` in `app/build.gradle*`
   - Capacitor: `capacitor.config.*` (appId, appName) + `android/app/build.gradle`
   - React Native/Expo: `app.json` / `app.config.*`
2. **Collect assets** (conventional paths first; ask the user for anything not found):
   - Store copy: `docs/store/`, `docs/branding/`, `docs/PLAN.md`, `fastlane/metadata/`
   - Policy/terms: `docs/legal/`, deployed URLs
   - Icon: the 512px store artifact (or a 1024px master to resize)
   - Feature graphic: `*feature*graphic*` (1024×500)
   - Screenshots: the final store-submission set
3. **Generate listings in 3 locales by default**: fill all of
   `## Store Listing (en)`, `(ja)`, `(ko)` (adjust the default locale set to your
   markets). If source copy exists in only one locale, translate drafts for the
   rest and note "translated draft (date) — review before publishing" under `## Notes`.
   Respect Play limits: name ≤ 30 chars, short description ≤ 80, full description ≤ 4000.
4. **Decide the slug**: brand-based kebab-case (e.g. `aurora-notes`). Reuse an existing directory if present.
5. **Diff-first rule (mandatory)**: if `<vault>/<slug>/app.md` already exists,
   **summarize the changes against the existing content and show the user before
   overwriting**. Preserve vault-only manual edits. Merge frontmatter field-by-field;
   replace only the body sections that changed.
6. **Copy assets**: icon → `assets/icon.png`, graphic → `assets/feature-graphic.png`,
   screenshots → `assets/screenshots/01-*.png…` (numeric prefix keeps order).
7. **Rebuild**: `python3 <skill dir>/scripts/build.py --vault <vault>`
8. **Report**: saved/updated fields, copied asset count, and anything missing
   (no icon, missing locales — `listing:xx✗` marks in the build output).

### list — print a catalog summary

Read frontmatter from `<vault>/*/app.md` and print a table (name, package, status, updated).

### show <app> — print one app in detail

Show the `app.md` content plus an asset inventory (icon / graphic / screenshot count).

### delete <app> — remove an entry

**Always confirm with the user first** (show the directory path + asset count),
then delete `<vault>/<slug>/` and rebuild.

### generate <slug> <icon|feature-graphic|screenshots> — create missing assets

The `⚡ Copy generate request` button on empty asset slots in the viewer puts this
command on the clipboard (the user pastes it back into Claude Code — the
"reverse call" loop). If slug is omitted, infer from the current project.
**Always read the target app's `app.md` (listings + notes) first** to absorb
brand tone and feature context.

**icon** (512×512):
1. Generate a 1024² master with your image-generation tooling — ⚠️ avoid the words
   "icon" / "app icon" in the prompt (models tend to draw a duplicated framed icon
   inside the canvas). Describe it as "flat vector artwork filling the entire square
   canvas edge to edge" plus the app concept/brand colors.
2. Show candidates to the user and let them pick.
3. Resize to 512 → `<vault>/<slug>/assets/icon.png`

**feature-graphic** (1024×500):
1. ⚠️ Some models (e.g. Gemini) don't support 2:1 — generate a wider ratio (16:9)
   and center-crop to 1024×500.
2. If a title/tagline overlay is needed, generate with text or composite afterwards.
3. Confirm with the user → `<vault>/<slug>/assets/feature-graphic.png`

**screenshots** (1080×2400 recommended, min. 2) — branch by app type:
- Native Android/Flutter: install a debug build on an emulator (or device),
  navigate screens, capture via `adb exec-out screencap -p > NN-name.png`
- Capacitor/webview: open the dev server or build in headless Chrome with
  `--window-size=1080,2400 --screenshot`
- Screen list: prefer one recorded under `## Notes` in `app.md`; otherwise propose
  core screens (home / 2-3 key features / settings) and confirm with the user
- File names `01-home.png` style (numeric prefix) → `<vault>/<slug>/assets/screenshots/`

Wrap-up for all: rebuild → report generated files and **remaining missing assets**.

### open / build — rebuild / open the viewer

```bash
python3 <skill dir>/scripts/build.py --vault <vault> --open   # build + open in browser
python3 <skill dir>/scripts/build.py --vault <vault>          # build only
```

Add `--lang ko` for the Korean viewer UI.

## app.md data model

```markdown
---
appName: Aurora Notes
packageName: com.example.auroranotes
platform: android          # android / ios / android+ios / web
status: released           # planning / dev / released / archived
shortDesc: One-liner shown on the catalog card
playUrl: https://play.google.com/store/apps/details?id=...
appStoreUrl:               # optional
privacyPolicyUrl: https://...
termsUrl: https://...
repo: owner/repo
projectDir: projects/aurora-notes
version: 2.1.0 (34)
created: 2026-01-15
updated: 2026-07-07
tags: [productivity, notes]
---

## Store Listing (en)

### App Name
(Play display name, ≤ 30 chars)

### Short Description
(≤ 80 chars)

### Full Description
(≤ 4000 chars — multiple paragraphs fine)

## Store Listing (ja)
(same 3 fields)

## Store Listing (ko)
(same 3 fields)

## Privacy Policy
(URLs + summary or data-collection notes)

## Release Notes
### 2.1.0 (2026-07-01)
- ...

## Notes
(manual-edit area — save must never overwrite this section)
```

Rules:
- Frontmatter is parsed by build.py's mini YAML parser — **no nested maps**;
  scalars and lists only.
- **`## Store Listing (locale)` sections are parsed structurally** by build.py and
  rendered as the viewer's "Play Store Listing" tabs (locale switch + per-field
  clipboard copy + character-count checks). Keep the exact heading format —
  `Store Listing (en)` (Korean alias `스토어 등록정보 (ko)` also accepted) with
  `### App Name / ### Short Description / ### Full Description` subheadings.
  Field bodies contain **only the raw text** to paste into Play Console
  (comments/source notes go under `## Notes`).
- Frontmatter `appName`/`shortDesc` are for the catalog card (one representative locale).
- Never put image assets in frontmatter — they are **auto-discovered by convention**:
  `assets/icon.*`, `assets/feature-graphic.*`, `assets/screenshots/*`
- `## Notes` is the user's manual-edit area — never modify it during save.

## Viewer features (reference)

- Detail panel: package-name copy button; per-locale tabs with copy buttons for
  app name / short / full description + live Play limit counters (30/80/4000,
  red when exceeded)
- Asset downloads: individual (hover ↓ on each screenshot) and bulk
  (`slug-filename` prefix); the browser asks once to allow multiple downloads
- Missing-asset reverse call: cards show missing badges (`icon ✗` etc.), empty
  detail slots show placeholders with `⚡ Copy generate request` →
  `/app-vault generate <slug> <asset>` lands on the clipboard

## Boundaries

- The vault is the single source of truth. Never overwrite an existing entry
  without a diff summary.
- `_site/` is a build artifact — edit `scripts/template.html` instead and rebuild.
- New frontmatter fields are fine — the viewer ignores unknown keys. To surface
  one in the UI, edit `scripts/template.html` and rebuild.
- This skill is for **accumulation/browsing only**. Copywriting, screenshot
  production, and icon generation belong to your own tooling — their outputs
  flow into the vault through `save`/`generate`.
