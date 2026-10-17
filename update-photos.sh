#!/usr/bin/env bash
# photos/ 안의 이미지 목록을 photos/photos.js 로 다시 만든다.
# 사진을 넣거나 지운 뒤 ./update-photos.sh 를 실행한다.
set -euo pipefail

cd "$(dirname "$0")"

DIR="photos"
OUT="$DIR/photos.js"

if [ ! -d "$DIR" ]; then
  echo "폴더가 없습니다: $DIR" >&2
  exit 1
fi

# BSD sort 에 -V 가 없는 환경을 대비한다.
if sort -V </dev/null >/dev/null 2>&1; then
  SORT="sort -f -V"
else
  SORT="sort -f"
fi

# macOS 는 한글 파일 이름을 NFD(자모 분리)로 돌려주는데, git 은 NFC 로 저장한다.
# NFD 이름을 그대로 쓰면 로컬에서는 보여도 GitHub Pages 에서는 404 가 난다. 목록을 NFC 로 맞춘다.
nfc() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import sys, unicodedata; sys.stdout.write(unicodedata.normalize("NFC", sys.stdin.read()))'
  else
    cat
  fi
}

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

find "$DIR" -maxdepth 1 -type f \
  \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \
     -o -iname '*.webp' -o -iname '*.gif' -o -iname '*.avif' \) \
  | sed "s|^$DIR/||" | nfc | $SORT > "$tmp"

{
  echo "// update-photos.sh 가 만드는 파일입니다. 직접 고치지 않습니다."
  echo "window.WEDDING_PHOTOS = ["
  first=1
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    esc=$(printf '%s' "$name" | sed 's/\\/\\\\/g; s/"/\\"/g')
    if [ "$first" -eq 1 ]; then first=0; else echo ","; fi
    printf '  "%s"' "$esc"
  done < "$tmp"
  [ "$first" -eq 1 ] || echo
  echo "];"
} > "$OUT"

echo "사진 $(wc -l < "$tmp" | tr -d ' ')장을 $OUT 에 기록했습니다."
