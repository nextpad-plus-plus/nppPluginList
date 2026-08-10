#!/usr/bin/env python3
"""
Verify the PUBLISHED catalogs the way a user's Plugins Admin will see them.

For every entry in pl.linux-{x86,arm64}.json this downloads the catalog's
own `repository` URL anonymously — no token, exactly what an end user's
client does — and checks the bytes against the catalog's `id`, then checks
the archive layout and the `.so` against `so-id`.

Anonymous access is the point of the test: these repos only recently went
public, and a URL that works with our credentials but 404s for everyone
else would be invisible until users complained.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

LIST_REPO = Path(__file__).resolve().parents[1]
EXPECT_MACHINE = {"x86": "x86-64", "arm64": "aarch64"}


def fetch(url, dest):
    # -f: fail on HTTP error. No auth header: anonymous, like a real client.
    r = subprocess.run(
        ["curl", "-fsSL", "--retry", "2", "-o", str(dest), url],
        capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(arch):
    cat = json.loads((LIST_REPO / f"pl.linux-{arch}.json").read_text())
    problems, ok = [], 0

    for e in cat["npp-plugins"]:
        folder = e["folder-name"]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            z = td / "p.zip"
            got, err = fetch(e["repository"], z)
            if not got:
                problems.append(f"{folder}: download failed — {err[:90]}")
                continue
            if sha256(z) != e["id"]:
                problems.append(f"{folder}: published bytes != catalog id")
                continue
            want = f"{folder}/{folder}.so"
            try:
                with zipfile.ZipFile(z) as zf:
                    if want not in zf.namelist():
                        problems.append(f"{folder}: archive lacks {want}")
                        continue
                    zf.extractall(td / "x")
            except zipfile.BadZipFile:
                problems.append(f"{folder}: not a valid zip")
                continue
            so = td / "x" / want
            if sha256(so) != e["so-id"]:
                problems.append(f"{folder}: .so sha256 != catalog so-id")
                continue
            out = subprocess.run(["file", "-b", str(so)],
                                 capture_output=True, text=True).stdout
            if EXPECT_MACHINE[arch] not in out:
                problems.append(f"{folder}: wrong arch — {out.strip()[:50]}")
                continue
            ok += 1
            print(f"  [{arch}] {folder:24} ok")

    print(f"[{arch}] {ok}/{len(cat['npp-plugins'])} verified from the live URLs")
    for p in problems:
        print("   PROBLEM " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(max(main(a) for a in (sys.argv[1:] or ["arm64", "x86"])))
