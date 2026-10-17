"""handwrite.py 가 만든 획 목록을 손글씨 애니메이션 SVG 로 만든다.

usage: python build_svg.py <strokes.json> <out.html> <stroke_width> <write_seconds> <start_delay>

펜은 일정한 속도로 움직인다. 획마다 길이에 비례한 시간을 주고, 앞 획이 끝나면 다음 획을 시작한다.
각 path 의 style 에 stroke-dasharray/dashoffset 과 animation-duration/delay 를 직접 적는다.
"""
import json
import math
import sys

src, out = sys.argv[1], sys.argv[2]
SW, WRITE, START = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
LIFT = 0.05       # 펜을 떼고 다음 획으로 옮기는 시간
LINE_GAP = 0.15   # 줄을 바꾸는 시간

data = json.load(open(src))
strokes = [(li, [[round(x, 1), round(y, 1)] for x, y in s])
           for li, line in enumerate(data['lines']) for s in line['strokes']]
xs = [p[0] for _, s in strokes for p in s]
ys = [p[1] for _, s in strokes for p in s]
x0, y0 = math.floor(min(xs) - SW), math.floor(min(ys) - SW)
w, h = math.ceil(max(xs) + SW) - x0, math.ceil(max(ys) + SW) - y0


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def fmt(v):
    s = ('%.1f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


n_lift = sum(1 for k in range(1, len(strokes)) if strokes[k][0] == strokes[k - 1][0])
speed = sum(plen(s) for _, s in strokes) / (WRITE - n_lift * LIFT - (len(data['lines']) - 1) * LINE_GAP)

paths, t, prev = [], START, None
for li, s in strokes:
    if prev is not None:
        t += LINE_GAP if li != prev else LIFT
    L = plen(s)
    d = 'M' + ' '.join(fmt(x - x0) + ' ' + fmt(y - y0) for x, y in s)
    # 대시 끝이 획 시작점에 걸리면 둥근 끝(round cap)이 점으로 먼저 보인다.
    # 그래서 처음에는 대시가 굵기만큼 획 앞에서 끝나게 두고, 틈은 획 길이보다 넉넉히 준다.
    paths.append('<path d="%s" style="stroke-dasharray:%s %s;stroke-dashoffset:%s;'
                 'animation-duration:%.2fs;animation-delay:%.2fs"/>'
                 % (d, fmt(L + 0.5), fmt(L + 2 * SW + 1), fmt(L + SW + 0.5), L / speed, t))
    t += L / speed
    prev = li

open(out, 'w').write('<svg class="intro_write" viewBox="0 0 %d %d" width="%d" height="%d" focusable="false">\n%s\n</svg>\n'
                     % (w, h, w, h, '\n'.join(paths)))
print('viewBox %d x %d, 획 %d개, 마지막 획이 끝나는 시각 %.2fs' % (w, h, len(paths), t), file=sys.stderr)
