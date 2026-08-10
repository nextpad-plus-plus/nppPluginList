#!/usr/bin/env bash
# Build + package every ported Linux plugin for ONE architecture.
#
# Per plugin it emits:
#   <plugin>.linux/dist/<arch>/<Folder>v<ver>-linux-<arch>.zip
#       containing <Folder>/<Folder>.so + payload
#
# The zip lives next to its own plugin, mirroring how the macOS ports keep a
# dist/ folder each; Linux carries two, dist/arm64 and dist/x86, because the
# .so differs per architecture. dist/ is gitignored in every plugin repo.
#
# A build index (hashes, sizes, ldd needs) is written outside the repos to
#   $INDEX/manifest.jsonl
# and is what gen-linux-catalogs.py consumes.
#
# Two constraints drive the design:
#  1. The installer (src/pluginsadmin.c) REQUIRES the archive to extract to
#     <folder-name>/<folder-name>.so and rejects it otherwise.
#  2. Payload beyond the .so (resources/, LICENSE, NextZip's 7z.so, ...) is
#     never listed here — it comes from each plugin, preferring its own
#     package_zip target and falling back to install() harvested through
#     DESTDIR. (--prefix cannot be used for that fallback: the plugins set an
#     absolute $ENV{HOME}/... install dir, which --prefix does not relocate.)
set -uo pipefail

SRC=${SRC:-$HOME/development/npp/nppPluginsLinux}
VERSIONS=${VERSIONS:-$HOME/npp-plugin-dist/versions.tsv}
JOBS=${JOBS:-4}

case "$(uname -m)" in
  aarch64|arm64) ARCH_LABEL=arm64 ;;
  x86_64|amd64)  ARCH_LABEL=x86   ;;
  *) echo "unsupported arch $(uname -m)" >&2; exit 1 ;;
esac
INDEX=${INDEX:-$HOME/npp-plugin-dist/$ARCH_LABEL}

mkdir -p "$INDEX"
MANIFEST="$INDEX/manifest.jsonl"
: > "$MANIFEST"
FAILLOG="$INDEX/failures.txt"
: > "$FAILLOG"

ok=0; fail=0
only=("$@")

while IFS=$'\t' read -r repo folder version; do
  [ -n "${repo:-}" ] || continue
  if [ ${#only[@]} -gt 0 ]; then
    match=0
    for o in "${only[@]}"; do [ "$o" = "$repo" ] || [ "$o" = "$folder" ] && match=1; done
    [ $match -eq 1 ] || continue
  fi

  d="$SRC/$repo"
  echo "=========== $folder v$version ($ARCH_LABEL) ==========="
  log="$INDEX/$folder.build.log"
  # Each plugin keeps its own artifacts, like the macOS ports do.
  OUT="$d/dist/$ARCH_LABEL"
  mkdir -p "$OUT"

  # 1. Configure + build (Release; reuse the existing build dir to stay
  #    inside this VM's tight disk budget).
  if ! cmake -B "$d/build" -S "$d" -DCMAKE_BUILD_TYPE=Release > "$log" 2>&1; then
     echo "  CONFIGURE FAILED (see $log)"; echo "$folder: configure" >> "$FAILLOG"
     fail=$((fail+1)); continue
  fi
  if ! cmake --build "$d/build" -j"$JOBS" >> "$log" 2>&1; then
     echo "  BUILD FAILED (see $log)"; echo "$folder: build" >> "$FAILLOG"
     fail=$((fail+1)); continue
  fi

  # 2. Collect the payload. Most plugins define their own `package_zip`
  #    target listing exactly what they intend to ship — that is the
  #    authored intent and it is a superset of the install() rules (seven
  #    plugins ship a LICENSE/README through package_zip that install()
  #    omits). Fall back to harvesting install() through DESTDIR for the
  #    plugins that define no such target.
  destdir=""
  payload=""
  if grep -q "add_custom_target(package_zip" "$d/CMakeLists.txt" 2>/dev/null \
     && cmake --build "$d/build" --target package_zip >> "$log" 2>&1 \
     && [ -d "$d/build/pkg/$folder" ]; then
     payload="$d/build/pkg/$folder"
     src_kind="package_zip"
  else
     src_kind="install()"
     destdir=$(mktemp -d /tmp/npp-destdir-XXXXXX)
     if ! DESTDIR="$destdir" cmake --install "$d/build" >> "$log" 2>&1; then
        echo "  INSTALL FAILED (see $log)"; echo "$folder: install" >> "$FAILLOG"
        rm -rf "$destdir"; fail=$((fail+1)); continue
     fi
     payload=$(find "$destdir" -type d -path "*/plugins/$folder" | head -1)
     if [ -z "$payload" ]; then
        echo "  NO PAYLOAD DIR named $folder under the install tree"
        echo "$folder: payload-dir" >> "$FAILLOG"
        rm -rf "$destdir"; fail=$((fail+1)); continue
     fi
  fi

  # 3. Stage as <Folder>/ and enforce the installer's contract.
  stage=$(mktemp -d /tmp/npp-stage-XXXXXX)
  cp -a "$payload" "$stage/$folder"
  so="$stage/$folder/$folder.so"
  if [ ! -f "$so" ]; then
     echo "  MISSING $folder/$folder.so — installer would reject this zip"
     echo "$folder: missing-so" >> "$FAILLOG"
     rm -rf "$destdir" "$stage"; fail=$((fail+1)); continue
  fi
  chmod 0755 "$so"

  # 4. Zip (-X drops uid/gid/extra attrs for a cleaner, steadier archive).
  zip_name="${folder}v${version}-linux-${ARCH_LABEL}.zip"
  rm -f "$OUT/$zip_name"
  ( cd "$stage" && zip -q -r -X "$OUT/$zip_name" "$folder" ) || {
     echo "  ZIP FAILED"; echo "$folder: zip" >> "$FAILLOG"
     rm -rf "$destdir" "$stage"; fail=$((fail+1)); continue
  }

  # 5. Record hashes + the shared libraries this .so actually needs.
  zip_sha=$(sha256sum "$OUT/$zip_name" | cut -d' ' -f1)
  so_sha=$(sha256sum "$so" | cut -d' ' -f1)
  built=$(date -u +%Y-%m-%d)
  zip_size=$(stat -c%s "$OUT/$zip_name")
  needed=$(objdump -p "$so" 2>/dev/null | awk '/NEEDED/{printf "%s ", $2}')
  files=$(cd "$stage" && find "$folder" -type f | wc -l)

  python3 - "$folder" "$version" "$zip_name" "$zip_sha" "$so_sha" "$built" \
             "$zip_size" "$files" "$OUT/$zip_name" "$needed" >> "$MANIFEST" <<'PY'
import json, sys
(_, folder, version, zip_name, zip_sha, so_sha, built, size, files,
 zip_path, needed) = sys.argv
print(json.dumps({
    "folder": folder, "version": version, "zip": zip_name,
    "zip_path": zip_path,
    "zip_sha256": zip_sha, "so_sha256": so_sha, "built": built,
    "zip_size": int(size), "file_count": int(files),
    "needed": needed.split(),
}))
PY

  echo "  ok  $zip_name  ($(numfmt --to=iec $zip_size), $files files, via $src_kind)"
  rm -rf "$destdir" "$stage"
  ok=$((ok+1))
done < "$VERSIONS"

echo
echo "=================================================="
echo "$ARCH_LABEL: $ok packaged, $fail failed"
[ -s "$FAILLOG" ] && { echo "failures:"; cat "$FAILLOG"; }
echo "build index: $MANIFEST"
echo "zips: <plugin>.linux/dist/$ARCH_LABEL/"
