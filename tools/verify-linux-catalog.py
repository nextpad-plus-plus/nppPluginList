#!/usr/bin/env python3
"""
Independently verify a built Linux catalog against its zips.

Re-derives every hash from the artifacts on disk rather than trusting the
build manifest, and reproduces the checks the installer performs
(src/pluginsadmin.c) so a bad archive is caught here and not by a user:

  * zip sha256 == catalog `id`
  * the archive extracts to <folder-name>/<folder-name>.so
  * that .so's sha256 == catalog `so-id`
  * the .so is an ELF shared object of the expected architecture
  * every required schema field is present and well-formed
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

LIST_REPO = Path(__file__).resolve().parents[1]
DIST = Path.home() / "npp-plugin-dist"
EXPECT_MACHINE = {"x86": "x86-64", "arm64": "aarch64"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(arch):
    cat = json.loads((LIST_REPO / f"pl.linux-{arch}.json").read_text())

    # Zips live beside their own plugin (<plugin>.linux/dist/<arch>/); the
    # build index records exactly where each one landed.
    index = {}
    manifest = DIST / arch / "manifest.jsonl"
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec.get("zip_path"):
                    index[rec["folder"]] = Path(rec["zip_path"])

    problems, checked = [], 0

    for e in cat["npp-plugins"]:
        folder = e["folder-name"]
        zpath = index.get(folder, DIST / arch / Path(e["repository"]).name)

        if not zpath.exists():
            problems.append(f"{folder}: zip missing at {zpath}")
            continue

        if sha256(zpath) != e["id"]:
            problems.append(f"{folder}: zip sha256 != catalog id")

        for field in ("id", "so-id"):
            if not re.fullmatch(r"[0-9a-fA-F]{64}", e.get(field, "")):
                problems.append(f"{folder}: {field} is not a 64-hex digest")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.get("so-built", "")):
            problems.append(f"{folder}: so-built is not YYYY-MM-DD")
        if e.get("npp-min-version") != "1.1.0":
            problems.append(f"{folder}: npp-min-version is {e.get('npp-min-version')}")
        if not e.get("description") or not e.get("display-name"):
            problems.append(f"{folder}: empty description/display-name")
        if f"/v{e['version']}/" not in e["repository"]:
            problems.append(f"{folder}: repository URL tag != version {e['version']}")

        want = f"{folder}/{folder}.so"
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(zpath) as z:
                names = z.namelist()
                if want not in names:
                    problems.append(f"{folder}: archive lacks {want} — installer would reject")
                    continue
                # Reject archives that would write outside the plugins dir.
                for n in names:
                    if n.startswith("/") or ".." in Path(n).parts:
                        problems.append(f"{folder}: unsafe path in archive: {n}")
                    if not (n == f"{folder}/" or n.startswith(f"{folder}/")):
                        problems.append(f"{folder}: stray top-level entry: {n}")
                z.extractall(td)
            so = Path(td) / want
            if sha256(so) != e["so-id"]:
                problems.append(f"{folder}: extracted .so sha256 != catalog so-id")
            out = subprocess.run(["file", "-b", str(so)], capture_output=True,
                                 text=True).stdout
            if "ELF" not in out or "shared object" not in out:
                problems.append(f"{folder}: not an ELF shared object ({out.strip()[:50]})")
            elif EXPECT_MACHINE[arch] not in out:
                problems.append(f"{folder}: wrong arch — expected "
                                f"{EXPECT_MACHINE[arch]}, got {out.strip()[:60]}")
        checked += 1

    print(f"[{arch}] verified {checked}/{len(cat['npp-plugins'])} entries")
    if problems:
        print(f"[{arch}] {len(problems)} PROBLEM(S):")
        for p in problems:
            print("   " + p)
        return 1
    print(f"[{arch}] all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(max(main(a) for a in (sys.argv[1:] or ["arm64", "x86"])))
