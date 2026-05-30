#!/usr/bin/env python3
"""
Update pl.macos-arm64.json for the Nextpad++ v1.0.6 rebrand cycle.

For each plugin entry:
  - bump `version`, `id` (zip sha256), `dylib-id`, `dylib-built` to today
  - set `npp-min-version` to "1.0.6"  (.nextpad++/ path is host-side change)
  - rewrite `repository` URL: notepad-plus-plus-mac → nextpad-plus-plus, new
    version-tagged filename `<folder-name>v<version>.zip`
  - rewrite the macOS Homepage line inside `description`:
        notepad-plus-plus-mac → nextpad-plus-plus
  - rewrite plugin-level `homepage` field only for macOS-only projects
    (NppBeads): notepad-plus-plus-mac → nextpad-plus-plus

Reads fresh sha256s + sizes from /tmp/plugin-rebuilds/*.zip rather than the
build-time log so a stale log can't corrupt the catalog. Idempotent.
"""
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "pl.macos-arm64.json"
STAGE   = Path("/tmp/plugin-rebuilds")
TODAY   = date.today().isoformat()
NEW_ORG = "nextpad-plus-plus"
OLD_ORG = "notepad-plus-plus-mac"
NPP_MIN = "1.0.6"

# folder-name → (new_version, github_repo_name)
# repo name differs from folder-name only for JSON-Viewer/NppJsonViewer.
PLUGINS = [
    ("nppURLPlugin",        "1.0.2", "nppURLPlugin"),
    ("ComparePlus",         "1.0.2", "ComparePlus"),
    ("DoxyIt",              "1.0.1", "DoxyIt"),
    ("indentbyfold",        "1.0.2", "indentbyfold"),
    ("qkNppReverseLines",   "1.0.2", "qkNppReverseLines"),
    ("FoldingLineHider",    "1.0.1", "FoldingLineHider"),
    ("pork2sausage",        "1.0.1", "pork2sausage"),
    ("NppPluginOpenHost",   "1.0.1", "NppPluginOpenHost"),
    ("SelectToClipboard",   "1.0.1", "SelectToClipboard"),
    ("NPP_ExportPlugin",    "1.0.1", "NPP_ExportPlugin"),
    ("nppfavorites",        "1.0.1", "nppfavorites"),
    ("nppAutoDetectIndent", "1.0.1", "nppAutoDetectIndent"),
    ("selectquotedtext",    "1.0.1", "selectquotedtext"),
    ("notepadpp_rpc",       "1.0.1", "notepadpp_rpc"),
    ("nppQuickText",        "1.0.1", "nppQuickText"),
    ("NppMarkdownPanel",    "1.0.3", "NppMarkdownPanel"),
    ("ElasticTabstops",     "1.0.1", "ElasticTabstops"),
    ("XmlNavigator",        "1.0.1", "XmlNavigator"),
    ("NppJsonViewer",       "1.0.1", "JSON-Viewer"),
    ("NppLLM",              "1.0.1", "NppLLM"),
    ("NppAIAssistant",      "1.0.1", "NppAIAssistant"),
    ("NppBeads",            "0.9.1", "NppBeads"),
    ("AnalysePlugin",       "1.0.0", "AnalysePlugin"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def dylib_sha_from_zip(zip_path: Path, folder: str) -> str:
    # Extract the dylib to a temp dir and hash it. The zip names it
    # <folder>/<DylibName>.dylib at the top level.
    import tempfile
    import zipfile
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(zip_path) as zf:
            dylib_entries = [n for n in zf.namelist()
                             if n.endswith(".dylib") and n.startswith(folder + "/")
                             and "/" not in n[len(folder) + 1:]]
            if not dylib_entries:
                raise RuntimeError(f"No dylib in {zip_path}")
            zf.extract(dylib_entries[0], td)
            return sha256(Path(td) / dylib_entries[0])


def main():
    with CATALOG.open() as f:
        catalog = json.load(f)

    by_folder = {p["folder-name"]: p for p in catalog["npp-plugins"]}

    for folder, new_ver, repo in PLUGINS:
        if folder not in by_folder:
            print(f"SKIP: catalog missing {folder}", file=sys.stderr)
            continue
        entry = by_folder[folder]
        zip_path = STAGE / f"{folder}v{new_ver}.zip"
        if not zip_path.exists():
            print(f"SKIP: missing zip {zip_path}", file=sys.stderr)
            continue

        zip_hash = sha256(zip_path)
        dylib_hash = dylib_sha_from_zip(zip_path, folder)

        entry["version"]         = new_ver
        entry["id"]               = zip_hash
        entry["dylib-id"]         = dylib_hash
        entry["dylib-built"]      = TODAY
        entry["npp-min-version"]  = NPP_MIN
        entry["repository"] = (
            f"https://github.com/{NEW_ORG}/{repo}/releases/download/"
            f"v{new_ver}/{folder}v{new_ver}.zip"
        )

        # macOS Homepage URL inside the description text.
        entry["description"] = entry["description"].replace(
            f"github.com/{OLD_ORG}/",
            f"github.com/{NEW_ORG}/",
        )

        # Plugin-level homepage — only flip for macOS-only repos (NppBeads).
        # Upstream Windows plugins keep their original homepage pointer.
        if entry.get("homepage", "").startswith(f"https://github.com/{OLD_ORG}/"):
            entry["homepage"] = entry["homepage"].replace(
                f"github.com/{OLD_ORG}/",
                f"github.com/{NEW_ORG}/",
            )

        print(f"  ✓ {folder} v{new_ver} ({zip_path.name}, {zip_path.stat().st_size // 1024} KB)")

    with CATALOG.open("w") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"\nCatalog: {CATALOG}")


if __name__ == "__main__":
    main()
