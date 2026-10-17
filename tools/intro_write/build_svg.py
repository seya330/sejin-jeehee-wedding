"""handwrite.py 가 만든 획 목록과 WindSong 글자 윤곽선으로 손글씨 애니메이션 SVG 를 만든다.

usage: python build_svg.py <strokes.json> <font.ttf> <out.svg> <write_seconds> <start_delay>

화면에 보이는 것은 실제 WindSong 글자(윤곽선 path 하나)다. 중심선은 마스크에만 쓴다.
마스크 안의 흰 선이 펜 순서대로 그려지면서 그 자리의 글자를 드러낸다. 그래서 다 쓴 모습은 폰트와 같다.
마스크 선이 닿지 않은 획 끝 같은 자투리는 마지막 획 뒤에 마스크 전체를 서서히 채워 드러낸다.

펜은 일정한 속도로 움직인다. 획마다 길이에 비례한 시간을 주고, 앞 획이 끝나면 다음 획을 시작한다.
각 path 의 style 에 stroke-width, stroke-dasharray/dashoffset, animation-duration/delay 를 직접 적는다.
"""
import json
import math
import sys

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

src, font_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
WRITE, START = float(sys.argv[4]), float(sys.argv[5])
FONT_SIZE = 100      # handwrite.py 의 출력 단위와 같다
LINE_HEIGHT = 1.05
LIFT = 0.05          # 펜을 떼고 다음 획으로 옮기는 시간
LINE_GAP = 0.15      # 줄을 바꾸는 시간
MASK_SCALE = 1.25    # 마스크 선 굵기 = 글자 굵기 × MASK_SCALE + MASK_PAD
MASK_PAD = 0.8
FILL_REST = 0.2      # 마지막 획 뒤에 남은 자투리를 드러내는 시간


def fmt(v):
    s = ('%.1f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


# 글자 윤곽선: 크롬과 같은 HarfBuzz 로 배치해야 문맥 대체 글자(calt)가 똑같이 들어간다
blob = hb.Blob.from_file_path(font_path)
hb_font = hb.Font(hb.Face(blob))
tt = TTFont(font_path)
glyphs = tt.getGlyphSet()
scale = FONT_SIZE / tt['head'].unitsPerEm


def place(text, baseline, pen_factory):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, {})
    total = sum(p.x_advance for p in buf.glyph_positions)
    x = -total / 2  # text-anchor:middle 과 같다
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = tt.getGlyphName(info.codepoint)
        pen = pen_factory()
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale,
                                             (x + pos.x_offset) * scale, baseline - pos.y_offset * scale)))
        x += pos.x_advance


data = json.load(open(src))
texts = [line['text'] for line in data['lines']]
strokes = [(li, s['thick'], [[round(x, 1), round(y, 1)] for x, y in s['pts']])
           for li, line in enumerate(data['lines']) for s in line['strokes']]

# viewBox: 글자 윤곽선과 마스크 선을 모두 담는다
bounds = []
for li, text in enumerate(texts):
    bp = BoundsPen(glyphs)
    place(text, li * LINE_HEIGHT * FONT_SIZE, lambda: bp)
    if bp.bounds:
        bounds.append(bp.bounds)
for _, th, s in strokes:
    r = (th * MASK_SCALE + MASK_PAD) / 2
    for x, y in s:
        bounds.append((x - r, y - r, x + r, y + r))
x0 = math.floor(min(b[0] for b in bounds) - 1)
y0 = math.floor(min(b[1] for b in bounds) - 1)
w = math.ceil(max(b[2] for b in bounds) + 1) - x0
h = math.ceil(max(b[3] for b in bounds) + 1) - y0

svg_pen = SVGPathPen(glyphs, ntos=fmt)
for li, text in enumerate(texts):
    place(text, li * LINE_HEIGHT * FONT_SIZE - y0,
          lambda: TransformPen(svg_pen, (1, 0, 0, 1, -x0, 0)))
# 한 줄로 두면 수만 자가 되어 index.html 을 훑기 어렵다. 윤곽(Z)마다 줄을 나눈다.
ink = svg_pen.getCommands().replace('Z', 'Z\n').strip()


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


n_lift = sum(1 for k in range(1, len(strokes)) if strokes[k][0] == strokes[k - 1][0])
speed = sum(plen(s) for _, _, s in strokes) / (WRITE - n_lift * LIFT - (len(texts) - 1) * LINE_GAP)

paths, t, prev = [], START, None
for li, th, s in strokes:
    if prev is not None:
        t += LINE_GAP if li != prev else LIFT
    L, sw = plen(s), th * MASK_SCALE + MASK_PAD
    d = 'M' + ' '.join(fmt(x - x0) + ' ' + fmt(y - y0) for x, y in s)
    # 대시 끝이 획 시작점에 걸리면 둥근 끝(round cap)이 점으로 먼저 드러난다.
    # 그래서 처음에는 대시가 굵기만큼 획 앞에서 끝나게 두고, 틈은 획 길이보다 넉넉히 준다.
    paths.append('<path d="%s" style="stroke-width:%s;stroke-dasharray:%s %s;stroke-dashoffset:%s;'
                 'animation-duration:%.2fs;animation-delay:%.2fs"/>'
                 % (d, fmt(sw), fmt(L + 0.5), fmt(L + 2 * sw + 1), fmt(L + sw + 0.5), L / speed, t))
    t += L / speed
    prev = li

svg = ('<svg class="intro_write" viewBox="0 0 {w} {h}" width="{w}" height="{h}" focusable="false">\n'
       '<mask id="introInk" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">\n'
       '{paths}\n'
       '<rect width="{w}" height="{h}" style="animation-duration:{rest}s;animation-delay:{end:.2f}s"/>\n'
       '</mask>\n'
       '<path class="intro_ink" mask="url(#introInk)" d="{ink}"/>\n'
       '</svg>\n').format(w=w, h=h, paths='\n'.join(paths), rest=FILL_REST, end=t, ink=ink)
open(out, 'w').write(svg)
print('viewBox %d x %d, 획 %d개, 마지막 획이 끝나는 시각 %.2fs, 자투리까지 %.2fs, 글자 윤곽선 %d자'
      % (w, h, len(paths), t, t + FILL_REST, len(ink)), file=sys.stderr)
