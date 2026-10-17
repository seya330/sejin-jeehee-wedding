#!/bin/bash
# 첫 화면 손글씨 SVG 를 다시 만든다. 결과: tools/intro_write/out/intro_write.svg
# 필요: macOS 의 Google Chrome, python3. 처음 실행하면 .venv 에 pillow, numpy, scipy, scikit-image,
# uharfbuzz, fonttools 를 설치한다.
# 문구는 아래 LINES 에 줄 단위로 적는다. & < > 는 HTML 로 그려지므로 쓰지 않는다.
set -euo pipefail
cd "$(dirname "$0")"

LINES=("We are" "getting" "married")
WRITE_SECONDS=2.6   # 처음 획부터 마지막 획까지 쓰는 시간
START_DELAY=0.2     # 오버레이가 뜬 뒤 첫 획을 시작할 때까지
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_URL='https://raw.githubusercontent.com/google/fonts/main/ofl/windsong/WindSong-Regular.ttf'

mkdir -p out/lines
[ -x .venv/bin/python ] || { python3 -m venv .venv && .venv/bin/pip install -q pillow numpy scipy scikit-image uharfbuzz fonttools; }
[ -f out/WindSong-Regular.ttf ] || curl -sSL -o out/WindSong-Regular.ttf "$FONT_URL"

# 줄마다 크롬으로 크게 그린다. 글자 크기 600px, 가로 중앙 2200px, 기준선 900px 은 handwrite.py 와 맞춘 값이다.
for i in "${!LINES[@]}"; do
  cat > "out/lines/l$i.html" <<EOF
<!doctype html><meta charset="utf-8"><style>@font-face{font-family:WS;src:url(../WindSong-Regular.ttf)}html,body{margin:0;background:#fff;overflow:hidden}svg{display:block}</style>
<svg width="4400" height="1500"><text x="2200" y="900" font-family="WS" font-size="600" text-anchor="middle">${LINES[$i]}</text></svg>
EOF
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --user-data-dir="$PWD/out/chrome" --virtual-time-budget=3000 --window-size=4400,1500 \
    --screenshot="out/lines/l$i.png" "file://$PWD/out/lines/l$i.html" >/dev/null 2>&1
done

.venv/bin/python -I handwrite.py out/lines out/strokes.json "${LINES[@]}"
.venv/bin/python -I build_svg.py out/strokes.json out/WindSong-Regular.ttf out/intro_write.svg "$WRITE_SECONDS" "$START_DELAY"
echo "만들었습니다: tools/intro_write/out/intro_write.svg"
