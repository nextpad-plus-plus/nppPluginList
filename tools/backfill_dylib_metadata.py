#!/usr/bin/env python3
"""Backfill dylib-id, dylib-built, and npp-min-version fields for every
entry in pl.macos-arm64.json.

For each plugin:
  1. Download the zip from `repository`.
  2. Extract the dylib (<folder-name>/<folder-name>.dylib).
  3. dylib-id       = sha256 of the extracted dylib (hex, lowercase).
  4. dylib-built    = release `published_at` date, formatted YYYY-MM-DD.
                      Pulled from `gh api` for the release tag that owns
                      the asset. Falls back to the asset's `updated_at`
                      if release lookup fails.
  5. npp-min-version = "1.0.4" (per policy — host v1.0.4 is the current
                      shipping baseline).

The script is idempotent — rerunning against an already-backfilled
catalog recomputes the values from source-of-truth (the live GitHub
zip) and overwrites in place.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parent.parent / "pl.macos-arm64.json"
NPP_MIN_VERSION = "1.0.4"

# Matches GitHub release-asset URLs like:
#   https://github.com/<owner>/<repo>/releases/download/<tag>/<file>
REPO_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)"
    r"/releases/download/(?P<tag>[^/]+)/(?P<file>[^/]+)$"
)


def gh_api(path: str) -> dict | list:
    """Invoke `gh api` and return parsed JSON."""
    result = subprocess.run(
        ["gh", "api", path],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def release_date_for_tag(owner: str, repo: str, tag: str) -> str:
    """Return YYYY-MM-DD for a release's `published_at`. Raises on miss."""
    rel = gh_api(f"repos/{owner}/{repo}/releases/tags/{tag}")
    published = rel.get("published_at") or rel.get("created_at")
    if not published:
        raise RuntimeError(f"No published_at/created_at for {owner}/{repo}@{tag}")
    # "2026-04-18T12:49:20Z" → "2026-04-18"
    return published[:10]


def download(url: str, dest: Path) -> None:
    """Fetch url to dest (binary)."""
    with urllib.request.urlopen(url) as resp:
        dest.write_bytes(resp.read())


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().lower()


def process_entry(entry: dict) -> dict:
    """Mutate `entry` in place with dylib-id, dylib-built, npp-min-version."""
    folder = entry["folder-name"]
    repo_url = entry["repository"]
    display = entry.get("display-name", folder)

    m = REPO_URL_RE.match(repo_url)
    if not m:
        raise RuntimeError(
            f"[{display}] repository URL doesn't match expected shape: {repo_url}"
        )
    owner, repo, tag = m["owner"], m["repo"], m["tag"]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        zip_path = tmp / "plugin.zip"
        download(repo_url, zip_path)

        # Verify zip sha256 matches catalog `id` — catch drift between
        # catalog and GitHub before we compute anything downstream.
        zip_sha = sha256_hex(zip_path.read_bytes())
        catalog_zip_id = entry.get("id", "").lower()
        if catalog_zip_id and zip_sha != catalog_zip_id:
            raise RuntimeError(
                f"[{display}] zip sha256 mismatch:\n"
                f"  catalog id: {catalog_zip_id}\n"
                f"  actual zip: {zip_sha}\n"
                f"  url: {repo_url}"
            )

        # Extract and find the dylib — zip convention is <folder>/<folder>.dylib.
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)
        dylib_path = tmp / folder / f"{folder}.dylib"
        if not dylib_path.is_file():
            # Fall back: search any .dylib in the extracted tree. Some
            # plugins have a folder name that differs from the dylib name.
            candidates = list(tmp.rglob("*.dylib"))
            if len(candidates) != 1:
                raise RuntimeError(
                    f"[{display}] expected one dylib at {folder}/{folder}.dylib, "
                    f"found: {[str(c.relative_to(tmp)) for c in candidates]}"
                )
            dylib_path = candidates[0]

        dylib_id = sha256_hex(dylib_path.read_bytes())

    built_date = release_date_for_tag(owner, repo, tag)

    entry["dylib-id"]        = dylib_id
    entry["dylib-built"]     = built_date
    entry["npp-min-version"] = NPP_MIN_VERSION

    print(f"[{display:<32}] dylib-id={dylib_id[:16]}…  built={built_date}  min-npp={NPP_MIN_VERSION}")
    return entry


def main():
    data = json.loads(CATALOG_PATH.read_text())
    plugins = data["npp-plugins"]
    print(f"Backfilling {len(plugins)} plugins…\n")

    errors = []
    for entry in plugins:
        try:
            process_entry(entry)
        except Exception as e:
            errors.append((entry.get("display-name", entry.get("folder-name", "?")), e))
            print(f"  ERROR [{entry.get('display-name', '?')}]: {e}", file=sys.stderr)

    if errors:
        print(f"\n{len(errors)} error(s):", file=sys.stderr)
        for name, e in errors:
            print(f"  {name}: {e}", file=sys.stderr)
        sys.exit(1)

    # Preserve the exact 4-space indent the existing file uses.
    CATALOG_PATH.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
    print(f"\n✓ Wrote {CATALOG_PATH}")


if __name__ == "__main__":
    main()
