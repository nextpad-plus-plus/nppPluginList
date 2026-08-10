#!/usr/bin/env python3
"""
Regenerate pl.linux-x86.json and pl.linux-arm64.json from build manifests.

Inputs
  ~/npp-plugin-dist/versions.tsv          repo <tab> folder <tab> version
  ~/npp-plugin-dist/<arch>/manifest.jsonl one record per packaged plugin

Metadata precedence for each entry:
  1. the existing Linux catalog entry (preserves anything hand-tuned)
  2. the macOS catalog entry for the same folder-name, Linux-ified
  3. a hand-written fallback (plugins that never shipped on macOS)

Hashes always come from the manifest — never carried over — so a stale
catalog can't survive a rebuild.
"""
import json
import re
import sys
from pathlib import Path

LIST_REPO = Path(__file__).resolve().parents[1]
DIST = Path.home() / "npp-plugin-dist"
ORG = "https://github.com/nextpad-plus-plus-plugins"
NPP_MIN = "1.1.0"

# Plugins with no macOS catalog entry — authored from their README.
FALLBACK = {
    "CSVLint": {
        "display-name": "CSV Lint",
        "author": "Bas de Reuver",
        "description": (
            "Check syntax, validate data, reformat and convert CSV and "
            "fixed-width text files inside Nextpad++.\n\n"
            "Features:\n"
            "- CSV Lint docked panel: automatic column detection or manual "
            "parameters, editable schema.ini metadata\n"
            "- Syntax highlighting per column, and error highlighting for "
            "values that do not match the column datatype\n"
            "- Validate data against the inferred or declared schema\n"
            "- Reformat: change separator, quote style, alignment\n"
            "- Convert to SQL, XML, JSON, HTML and fixed-width output\n"
            "- Column-level analysis and record counts\n\n"
            "Linux port of Bas de Reuver's CSV Lint plug-in for Notepad++."
        ),
    },
    "LuaScript": {
        "display-name": "LuaScript",
        "author": "Justin Dailey",
        "description": (
            "Lua 5.3 scripting for Nextpad++.\n\n"
            "Features:\n"
            "- `editor` and `npp` objects exposing the full Scintilla and "
            "Notepad++ message surfaces, with properties, methods and events\n"
            "- Interactive console with command history and output capture, "
            "themed to follow the host editor\n"
            "- Run scripts on startup, bind them to menu entries and "
            "shortcuts\n"
            "- Callbacks on editor and application events\n\n"
            "Linux port of Justin Dailey's LuaScript plug-in for Notepad++."
        ),
    },
}


def linuxize(text, repo):
    """Rewrite macOS-specific wording in a description for the Linux build."""
    if not text:
        return text

    # Drop whole paragraphs that advertise macOS-only artifacts (standalone
    # .app shells, DMG downloads) — there is no Linux equivalent to ship.
    paras = [p for p in text.split("\n\n")
             if not re.search(r"\bDMG\b|\.app\b", p)]
    text = "\n\n".join(paras)

    subs = [
        (r"Universal binary \(Apple Silicon \+ Intel\)\.?", "Builds for arm64 and x86_64."),
        (r"Universal arm64\+x86_64\.?", "Builds for arm64 and x86_64."),
        (r"macOS Port Author:", "Port Author:"),
        (r"macOS Homepage:\s*\S+", f"Homepage: {ORG}/{repo}"),
        # Plugin-declared keyboard shortcuts do not exist on Linux: the
        # Linux FuncItem carries no shortcut field, so every command is
        # menu-only. Translating Cmd- to Ctrl- would document keys that do
        # nothing, so strip the claim instead.
        (r"\s*\((?:Cmd|Opt|Ctrl|Alt)[A-Za-z0-9+-]*(?:-[A-Za-z0-9]+)*\)", ""),
        (r"\bmacOS port\b", "Linux port"),
        (r"\bmacOS\b", "Linux"),
    ]
    for pat, rep in subs:
        text = re.sub(pat, rep, text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_catalog(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {e["folder-name"]: e for e in data.get("npp-plugins", [])}


def main():
    versions = {}
    for line in (DIST / "versions.tsv").read_text().splitlines():
        if not line.strip():
            continue
        repo, folder, ver = line.split("\t")
        versions[folder] = (repo, ver)

    macos = load_catalog(LIST_REPO / "pl.macos-arm64.json")
    warnings = []

    for arch in ("x86", "arm64"):
        manifest_path = DIST / arch / "manifest.jsonl"
        if not manifest_path.exists():
            print(f"!! no manifest for {arch}: {manifest_path}", file=sys.stderr)
            continue
        built = {}
        for line in manifest_path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                built[rec["folder"]] = rec

        cat_path = LIST_REPO / f"pl.linux-{arch}.json"
        existing = load_catalog(cat_path)

        entries = []
        for folder in sorted(built, key=str.lower):
            rec = built[folder]
            repo, version = versions[folder]
            old = existing.get(folder, {})
            mac = macos.get(folder, {})
            fb = FALLBACK.get(folder, {})

            display = old.get("display-name") or mac.get("display-name") \
                or fb.get("display-name") or folder
            author = old.get("author") or mac.get("author") \
                or fb.get("author") or "Andrew Letov"
            desc = old.get("description") or fb.get("description") \
                or linuxize(mac.get("description", ""), repo)
            if not desc:
                desc = f"{display} plugin for Nextpad++."
                warnings.append(f"{folder}: no description available — placeholder used")

            # The 8 pre-existing Linux entries were copied verbatim from the
            # macOS catalog; re-run the Linux rewrite over them too.
            desc = linuxize(desc, repo)

            leftovers = sorted(set(re.findall(
                r"\b(?:macOS|Apple Silicon|DMG|\.app|Finder|Xcode)\b", desc)))
            if leftovers:
                warnings.append(f"{folder}: description still mentions {leftovers}")

            zip_name = rec["zip"]
            entries.append({
                "folder-name": folder,
                "display-name": display,
                "version": version,
                "id": rec["zip_sha256"],
                "repository": f"{ORG}/{repo}/releases/download/v{version}/{zip_name}",
                "description": desc,
                "author": author,
                "homepage": f"{ORG}/{repo}",
                "so-id": rec["so_sha256"],
                "so-built": rec["built"],
                "npp-min-version": NPP_MIN,
            })

        out = {"version": "1.0.0", "npp-plugins": entries}
        cat_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {cat_path.name}: {len(entries)} entries")

    for w in sorted(set(warnings)):
        print("WARN " + w, file=sys.stderr)


if __name__ == "__main__":
    main()
