#!/usr/bin/env bash
# Publish each ported Linux plugin as a GitHub release carrying both
# architecture zips, at exactly the URLs the catalogs point to:
#
#   https://github.com/<ORG>/<repo>/releases/download/v<ver>/<Folder>v<ver>-linux-<arch>.zip
#
# One release per plugin (tag v<version>) with two assets. Idempotent: an
# existing release is reused, and an asset of the same name is replaced
# rather than duplicated (GitHub would otherwise rename the upload and
# silently break the catalog URL).
set -uo pipefail

SRC=${SRC:-$HOME/development/npp/nppPluginsLinux}
VERSIONS=${VERSIONS:-$HOME/npp-plugin-dist/versions.tsv}
LIST_REPO=${LIST_REPO:-$HOME/development/npp/nppPluginList}
ORG=nextpad-plus-plus-plugins
API=https://api.github.com
UPLOADS=https://uploads.github.com
DRY=${DRY:-0}

TOKEN=$(sed -n 's#https://[^:]*:\([^@]*\)@github.com#\1#p' ~/.git-credentials | head -1)
[ -n "$TOKEN" ] || { echo "no GitHub token found" >&2; exit 1; }
AUTH="Authorization: token $TOKEN"

ok=0; fail=0
while IFS=$'\t' read -r repo folder version; do
  [ -n "${repo:-}" ] || continue
  arm="$SRC/$repo/dist/arm64/${folder}v${version}-linux-arm64.zip"
  x86="$SRC/$repo/dist/x86/${folder}v${version}-linux-x86.zip"

  if [ ! -f "$arm" ] || [ ! -f "$x86" ]; then
    echo "### $folder: missing zip(s) — skipped"; fail=$((fail+1)); continue
  fi

  # Values reach python through the environment, never by interpolation into
  # source: display names contain apostrophes ("Poor Man's T-Sql Formatter").
  display=$(NPP_FOLDER="$folder" NPP_CAT="$LIST_REPO/pl.linux-arm64.json" python3 -c "
import json, os
f = os.environ['NPP_FOLDER']
c = json.load(open(os.environ['NPP_CAT']))
print(next((e['display-name'] for e in c['npp-plugins'] if e['folder-name'] == f), f))")
  sha_arm=$(sha256sum "$arm" | cut -d' ' -f1)
  sha_x86=$(sha256sum "$x86" | cut -d' ' -f1)

  echo "=========== $display v$version ($repo) ==========="
  if [ "$DRY" = "1" ]; then echo "  (dry run)"; ok=$((ok+1)); continue; fi

  # 1. Reuse or create the release for tag v<version>.
  rel=$(curl -s -H "$AUTH" "$API/repos/$ORG/$repo/releases/tags/v$version")
  rel_id=$(echo "$rel" | jq -r '.id // empty')
  if [ -z "$rel_id" ]; then
    body=$(NPP_VER="$version" NPP_DISPLAY="$display" \
           NPP_ARM="$(basename "$arm")" NPP_X86="$(basename "$x86")" \
           NPP_SHA_ARM="$sha_arm" NPP_SHA_X86="$sha_x86" python3 -c "
import json, os
E = os.environ
print(json.dumps({
  'tag_name': 'v' + E['NPP_VER'],
  'target_commitish': 'main',
  'name': E['NPP_DISPLAY'] + ' v' + E['NPP_VER'],
  'body': (
    'Linux build of ' + E['NPP_DISPLAY'] + ' for Nextpad++.\n\n'
    'Two architecture builds are attached; Plugins Admin picks the right\n'
    'one automatically. To install by hand, unzip into\n'
    '\`~/.local/share/nextpad++/plugins/\`.\n\n'
    '| asset | sha256 |\n| --- | --- |\n'
    '| \`' + E['NPP_ARM'] + '\` | \`' + E['NPP_SHA_ARM'] + '\` |\n'
    '| \`' + E['NPP_X86'] + '\` | \`' + E['NPP_SHA_X86'] + '\` |\n\n'
    'Requires Nextpad++ 1.1.0 or newer.'
  ),
  'draft': False, 'prerelease': False,
}))")
    rel=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
                -d "$body" "$API/repos/$ORG/$repo/releases")
    rel_id=$(echo "$rel" | jq -r '.id // empty')
    if [ -z "$rel_id" ]; then
      echo "  RELEASE CREATE FAILED: $(echo "$rel" | jq -r '.message // "?"')"
      echo "$rel" | jq -r '.errors[]?  | "    " + (.field // "") + " " + (.code // "")'
      fail=$((fail+1)); continue
    fi
    echo "  release created (id=$rel_id, tag v$version)"
  else
    echo "  release already exists (id=$rel_id) — reusing"
  fi

  # 2. Upload both assets, replacing any same-named asset.
  aok=1
  for z in "$arm" "$x86"; do
    name=$(basename "$z")
    existing=$(curl -s -H "$AUTH" "$API/repos/$ORG/$repo/releases/$rel_id/assets" \
               | jq -r --arg n "$name" '.[] | select(.name==$n) | .id')
    if [ -n "$existing" ]; then
      curl -s -X DELETE -H "$AUTH" "$API/repos/$ORG/$repo/releases/assets/$existing" > /dev/null
      echo "    replaced existing $name"
    fi
    up=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/zip" \
              --data-binary @"$z" \
              "$UPLOADS/repos/$ORG/$repo/releases/$rel_id/assets?name=$name")
    state=$(echo "$up" | jq -r '.state // empty')
    if [ "$state" != "uploaded" ]; then
      echo "    UPLOAD FAILED for $name: $(echo "$up" | jq -r '.message // .error // "?"')"
      aok=0
    else
      echo "    uploaded $name ($(echo "$up" | jq -r '.size') bytes)"
    fi
  done
  if [ "$aok" = "1" ]; then ok=$((ok+1)); else fail=$((fail+1)); fi
done < "$VERSIONS"

echo
echo "=================================================="
echo "published=$ok  failed=$fail"
