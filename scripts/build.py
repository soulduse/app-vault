#!/usr/bin/env python3
"""app-vault static site builder.

Scans <vault>/*/app.md, parses frontmatter + body, and emits a fully
self-contained _site/index.html (JSON embedded — open directly via file://).
No dependencies beyond the Python standard library.

Usage:
    python3 build.py --vault <path> [--lang en|ko] [--open]
    APP_VAULT_DIR=<path> python3 build.py

Quickstart with the bundled demo vault:
    python3 scripts/build.py --vault examples/vault --open
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = (".png", ".webp", ".jpg", ".jpeg", ".gif")
STATUS_ORDER = {"released": 0, "dev": 1, "planning": 2, "archived": 3}

# "## Store Listing (en)" and the Korean alias "## 스토어 등록정보 (ko)"
LISTING_SECTION = re.compile(
    r"^(?:Store Listing|스토어 등록정보)\s*\((\w[\w-]*)\)$", re.IGNORECASE
)
LISTING_FIELDS = {
    "app name": "name", "앱 이름": "name",
    "short description": "short", "간단한 설명": "short",
    "full description": "full", "자세한 설명": "full",
}


def parse_frontmatter(text):
    """Minimal YAML subset: key: value, inline lists [a, b], block lists (- item)."""
    meta, body = {}, text
    if not text.startswith("---"):
        return meta, body
    end = text.find("\n---", 3)
    if end == -1:
        return meta, body
    raw = text[3:end].strip("\n")
    body = text[end + 4 :].lstrip("\n")

    current_key = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        block_item = re.match(r"^\s+-\s+(.*)$", line)
        if block_item and current_key:
            meta.setdefault(current_key, [])
            if isinstance(meta[current_key], list):
                meta[current_key].append(_scalar(block_item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if not kv:
            continue
        key, value = kv.group(1), kv.group(2).strip()
        current_key = key
        if value == "":
            meta[key] = []  # assume start of a block list
        elif value.startswith("[") and value.endswith("]"):
            items = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            meta[key] = [_scalar(v) for v in items]
        else:
            meta[key] = _scalar(value)
    return meta, body


def _scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def extract_listings(body):
    """Pull '## Store Listing (locale)' sections out of the body as structured
    {locale: {name, short, full}} data; return the remaining body."""
    sections = []  # (title|None, [lines])
    title, buf = None, []
    for line in body.split("\n"):
        m = re.match(r"^##\s+(.+)$", line)
        if m and not line.startswith("###"):
            sections.append((title, buf))
            title, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    sections.append((title, buf))

    listings, kept = {}, []
    for sec_title, lines in sections:
        lm = LISTING_SECTION.match(sec_title) if sec_title else None
        if lm:
            listings[lm.group(1).lower()] = _parse_listing_fields(lines)
        else:
            if sec_title is not None:
                kept.append(f"## {sec_title}")
            kept.extend(lines)
    return listings, "\n".join(kept).strip("\n")


def _parse_listing_fields(lines):
    fields, key, buf = {}, None, []
    for line in lines:
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            if key and buf:
                fields[key] = "\n".join(buf).strip()
            key = LISTING_FIELDS.get(m.group(1).strip().lower())
            buf = []
        elif key is not None:
            buf.append(line)
    if key and buf:
        fields[key] = "\n".join(buf).strip()
    return fields


def find_asset(app_dir, stem):
    """First match of assets/<stem>.{png,webp,jpg,...} (convention over config)."""
    assets = app_dir / "assets"
    if not assets.is_dir():
        return None
    for ext in IMAGE_EXTS:
        candidate = assets / f"{stem}{ext}"
        if candidate.is_file():
            return candidate
    return None


def find_screenshots(app_dir):
    shots_dir = app_dir / "assets" / "screenshots"
    if not shots_dir.is_dir():
        return []
    return sorted(
        p for p in shots_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS and p.is_file()
    )


def rel_from_site(path, vault):
    """Path relative to _site/index.html."""
    return "../" + str(path.relative_to(vault)).replace("\\", "/")


def load_app(app_dir, vault):
    md = app_dir / "app.md"
    if not md.is_file():
        return None
    text = md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    listings, body = extract_listings(body)

    icon = find_asset(app_dir, "icon")
    graphic = find_asset(app_dir, "feature-graphic")
    shots = find_screenshots(app_dir)

    updated = meta.get("updated") or datetime.date.fromtimestamp(
        md.stat().st_mtime
    ).isoformat()

    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "slug": app_dir.name,
        "appName": meta.get("appName", app_dir.name),
        "packageName": meta.get("packageName", ""),
        "platform": meta.get("platform", ""),
        "status": meta.get("status", "dev"),
        "shortDesc": meta.get("shortDesc", ""),
        "playUrl": meta.get("playUrl", ""),
        "appStoreUrl": meta.get("appStoreUrl", ""),
        "privacyPolicyUrl": meta.get("privacyPolicyUrl", ""),
        "termsUrl": meta.get("termsUrl", ""),
        "repo": meta.get("repo", ""),
        "projectDir": meta.get("projectDir", ""),
        "version": meta.get("version", ""),
        "created": meta.get("created", ""),
        "updated": updated,
        "tags": tags,
        "icon": rel_from_site(icon, vault) if icon else None,
        "featureGraphic": rel_from_site(graphic, vault) if graphic else None,
        "screenshots": [rel_from_site(s, vault) for s in shots],
        "listings": listings,
        "body": body,
    }


def resolve_vault(arg_vault):
    if arg_vault:
        return arg_vault
    env = os.environ.get("APP_VAULT_DIR")
    if env:
        return Path(env)
    sys.exit(
        "No vault directory given.\n"
        "Pass --vault <path> or set APP_VAULT_DIR.\n"
        "Try the demo:  python3 scripts/build.py --vault examples/vault --open"
    )


def build(vault, lang="en", open_after=False):
    vault = vault.expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"Vault directory not found: {vault}")

    apps = []
    for app_dir in sorted(vault.iterdir()):
        if not app_dir.is_dir() or app_dir.name.startswith(("_", ".")):
            continue
        app = load_app(app_dir, vault)
        if app:
            apps.append(app)

    apps.sort(key=lambda a: a["updated"] or "", reverse=True)
    apps.sort(key=lambda a: STATUS_ORDER.get(a["status"], 9))

    template_path = Path(__file__).parent / "template.html"
    template = template_path.read_text(encoding="utf-8")

    payload = json.dumps(apps, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")  # keep </script> safe

    built_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = (
        template.replace("__DATA_JSON__", payload)
        .replace("__BUILT_AT__", built_at)
        .replace("__LANG__", lang)
    )

    out_dir = vault / "_site"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")

    print(f"✓ {len(apps)} app(s) → {out}")
    for app in apps:
        marks = []
        if not app["icon"]:
            marks.append("icon✗")
        if not app["shortDesc"]:
            marks.append("shortDesc✗")
        missing_locales = [lo for lo in ("ko", "en", "ja") if lo not in app["listings"]]
        if missing_locales:
            marks.append("listing:" + ",".join(missing_locales) + "✗")
        suffix = f"  ({', '.join(marks)})" if marks else ""
        print(f"  - {app['appName']} [{app['status']}]{suffix}")

    if open_after:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.run([opener, str(out)], check=False)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=None,
                        help="vault directory (or set APP_VAULT_DIR)")
    parser.add_argument("--lang", choices=["en", "ko"], default="en",
                        help="viewer UI language (default: en)")
    parser.add_argument("--open", action="store_true",
                        help="open the built page in a browser")
    args = parser.parse_args()
    build(resolve_vault(args.vault), lang=args.lang, open_after=args.open)
