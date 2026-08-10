#!/usr/bin/env python3
"""
Resolve the effective release version for every ported Linux plugin.

Both architectures must package the SAME version string (the version is
baked into the zip filename, the git tag and the download URL), so the
resolution happens once, here, and both build runs consume the result.

Rule: take the highest of
  * project(... VERSION x.y.z) in the plugin's CMakeLists.txt  — the port's
    own declared version, the primary source of truth
  * the version already published in pl.linux-{x86,arm64}.json — never
    regress a version users may already have installed
  * the macOS catalog version for the same folder-name — the ports share a
    lineage and the existing Linux entries mirror it

Emits a TSV: repo_dir <TAB> folder_name <TAB> version
and prints any disagreements to stderr so they get a human look.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path("/home/ubuntu/development/npp/nppPluginsLinux")
LIST_REPO = Path(__file__).resolve().parents[1]


def vtuple(v):
    if not v:
        return (0,)
    return tuple(int(x) for x in re.findall(r"\d+", v))


def cmake_info(cml: Path):
    """Return (version, folder_name) parsed from a plugin's CMakeLists.txt."""
    text = cml.read_text(errors="replace")

    version = None
    m = re.search(r"project\s*\(([^)]*)\)", text, re.S)
    if m:
        mv = re.search(r"\bVERSION\s+([0-9][0-9.]*)", m.group(1))
        if mv:
            version = mv.group(1)

    # folder-name == the basename of the install dir the plugin installs to,
    # which is what the app scans (<plugins>/<Folder>/<Folder>.so).
    folder = None
    mi = re.search(r'set\s*\(\s*\w*INSTALL_DIR\s+"[^"]*/plugins/([^"/]+)"', text)
    if mi:
        folder = mi.group(1)
    if not folder:
        mo = re.search(r'OUTPUT_NAME\s+"?([A-Za-z0-9_.+-]+)', text)
        if mo:
            folder = mo.group(1)
    return version, folder


def catalog_versions(path: Path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {
        e["folder-name"]: e.get("version", "")
        for e in data.get("npp-plugins", [])
    }


def main():
    pub = {}
    for name in ("pl.linux-x86.json", "pl.linux-arm64.json", "pl.macos-arm64.json"):
        for folder, ver in catalog_versions(LIST_REPO / name).items():
            if vtuple(ver) > vtuple(pub.get(folder)):
                pub[folder] = ver

    rows, notes = [], []
    for d in sorted(SRC.glob("*.linux"), key=lambda p: p.name.lower()):
        cml = d / "CMakeLists.txt"
        if not cml.exists():
            notes.append(f"{d.name}: NO CMakeLists.txt — skipped")
            continue
        cver, folder = cmake_info(cml)
        if not folder:
            notes.append(f"{d.name}: could not determine folder-name — skipped")
            continue
        pver = pub.get(folder)
        eff = cver if vtuple(cver) >= vtuple(pver) else pver
        if not eff:
            notes.append(f"{d.name}: no version anywhere — skipped")
            continue
        if pver and cver and vtuple(pver) > vtuple(cver):
            notes.append(
                f"{folder}: CMake says {cver} but {pver} is already published "
                f"— using {pver} to avoid a downgrade"
            )
        rows.append((d.name, folder, eff))

    for r in rows:
        print("\t".join(r))
    for n in notes:
        print("NOTE " + n, file=sys.stderr)


if __name__ == "__main__":
    main()
