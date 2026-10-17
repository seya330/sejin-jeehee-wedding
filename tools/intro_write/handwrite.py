"""브라우저로 크게 그린 문구에서 획의 중심선(skeleton)을 뽑아, 펜이 지나가는 순서대로 잇는다.

usage: python handwrite.py <lines_dir> <out.json> <줄1> <줄2> ...
  lines_dir/l0.png, l1.png ... : make.sh 가 크롬으로 그린 각 줄.
  글자 크기 600px, 가로 중앙 2200px, 기준선 900px 에 맞춰 그려져 있어야 한다.

PIL 로 직접 그리지 않는 이유: PIL 은 폰트의 문맥 대체 글자(calt)를 적용하지 않아서
브라우저에서 보이는 WindSong 과 글자 모양이 다르다(tt 가로획, g 꼬리 등이 빠진다).
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize

LINES_DIR, OUT, LINES = sys.argv[1], sys.argv[2], sys.argv[3:]
SIZE = 600            # 렌더링 글자 크기(px)
UNIT = 100 / SIZE     # 출력 좌표는 글자 크기를 100 으로 둔 단위
LINE_HEIGHT = 1.05
CX, BASE = 2200, 900  # 렌더링한 줄 이미지의 가로 중앙, 기준선
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def neighbors(sk, y, x):
    h, w = sk.shape
    for dy, dx in N8:
        yy, xx = y + dy, x + dx
        if 0 <= yy < h and 0 <= xx < w and sk[yy, xx]:
            yield yy, xx


def build_graph(sk):
    """중심선 픽셀을 노드(끝점·갈림길)와 그 사이를 잇는 엣지(픽셀 사슬)로 나눈다."""
    deg = ndimage.convolve(sk.astype(int), np.ones((3, 3), int), mode='constant') - 1
    deg[~sk] = 0
    node_px = sk & (deg != 2)
    lab, n = ndimage.label(node_px, structure=np.ones((3, 3)))
    nodes = {}
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        nodes[i] = np.array([xs.mean(), ys.mean()])
    elab, en = ndimage.label(sk & ~node_px, structure=np.ones((3, 3)))
    edges = []
    for i in range(1, en + 1):
        ys, xs = np.nonzero(elab == i)
        comp = set(zip(ys.tolist(), xs.tolist()))
        nb = {p: [q for q in neighbors(sk, *p) if q in comp] for p in comp}
        ends = [p for p in comp if len(nb[p]) <= 1]
        cur = ends[0] if ends else next(iter(comp))
        chain, seen = [], set()
        while cur is not None and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            nxt = [q for q in nb[cur] if q not in seen]
            # 계단 모양에서 이웃이 둘 이상이면 상하좌우 쪽을 먼저 간다
            nxt.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            cur = nxt[0] if nxt else None

        def touching(p):
            for q in neighbors(sk, *p):
                if lab[q] > 0:
                    return int(lab[q])
            return None
        a, b = touching(chain[0]), touching(chain[-1])
        if a is None and b is None and not ends:
            # 갈림길 없는 닫힌 고리: 노드를 하나 만든다
            nid = max(nodes, default=0) + 1
            nodes[nid] = np.array([chain[0][1], chain[0][0]], float)
            a = b = nid
        if a is None or b is None:
            continue
        edges.append({'a': a, 'b': b, 'pts': np.array([[x, y] for y, x in chain], float)})
    return nodes, edges


def length(pts):
    return float(np.sum(np.linalg.norm(np.diff(pts, axis=0), axis=1))) if len(pts) > 1 else 0.0


def degree(nodes, edges):
    d = {k: 0 for k in nodes}
    for e in edges:
        d[e['a']] += 1
        d[e['b']] += 1
    return d


def simplify_graph(nodes, edges, sw):
    for _ in range(4):
        d = degree(nodes, edges)
        # 획 끝에 생기는 짧은 잔가지를 지운다
        edges = [e for e in edges if not (
            (d[e['a']] == 1) != (d[e['b']] == 1) and length(e['pts']) < 1.3 * sw)]
        # 획이 교차하면 갈림길이 둘로 갈라져 짧은 다리가 생긴다. 하나로 합친다.
        merged = True
        while merged:
            merged = False
            for e in edges:
                if e['a'] != e['b'] and length(e['pts']) < 0.9 * sw:
                    d = degree(nodes, edges)
                    if d[e['a']] >= 3 and d[e['b']] >= 3:
                        keep, drop = e['a'], e['b']
                        nodes[keep] = (nodes[keep] + nodes[drop]) / 2
                        edges = [x for x in edges if x is not e]
                        for x in edges:
                            if x['a'] == drop:
                                x['a'] = keep
                            if x['b'] == drop:
                                x['b'] = keep
                        merged = True
                        break
    return nodes, edges


def out_dir(e, at_start, sw):
    """노드에서 엣지로 나가는 방향. 갈림길 근처는 모양이 뭉개지므로 조금 떨어진 구간으로 잰다."""
    pts = e['pts'] if at_start else e['pts'][::-1]
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    i0 = min(np.searchsorted(cum, 0.6 * sw), len(pts) - 1)
    i1 = min(np.searchsorted(cum, 2.6 * sw), len(pts) - 1)
    if i1 <= i0:
        i0, i1 = 0, len(pts) - 1
    v = pts[i1] - pts[i0]
    n = np.linalg.norm(v)
    return v / n if n else v


def traverse(nodes, edges, sw):
    """남은 획 중 가장 왼쪽 끝점에서 펜을 대고, 갈림길에서는 가장 곧게 이어지는 쪽으로 간다.
    되돌아가야 할 만큼 꺾이면 펜을 뗀다. tt 가로획 같은 나머지 획은 그 뒤에 왼쪽부터 쓴다."""
    ports = {k: [] for k in nodes}
    for i, e in enumerate(edges):
        ports[e['a']].append((i, True))
        ports[e['b']].append((i, False))
    unvisited = set(range(len(edges)))
    strokes = []
    while unvisited:
        d = {k: sum(1 for i, _ in ports[k] if i in unvisited) for k in nodes}
        cands = []
        for i in unvisited:
            e = edges[i]
            for at_start, nid in ((True, e['a']), (False, e['b'])):
                p = e['pts'][0] if at_start else e['pts'][-1]
                cands.append((0 if d[nid] == 1 else 1, p[0], i, at_start))
        cands.sort()
        _, _, i, fwd = cands[0]
        path = []
        while True:
            unvisited.discard(i)
            e = edges[i]
            path.extend((e['pts'] if fwd else e['pts'][::-1]).tolist())
            arrive = e['b'] if fwd else e['a']
            vin = -out_dir(e, not fwd, sw)
            best = None
            for j, js in ports[arrive]:
                if j in unvisited:
                    score = float(np.dot(vin, out_dir(edges[j], js, sw)))
                    if best is None or score > best[0]:
                        best = (score, j, js)
            if best is None or best[0] < -0.6:
                break
            _, i, fwd = best
        strokes.append(np.array(path))
    return strokes


def smooth(pts, sigma):
    """고르게 다시 뽑은 뒤 가우시안으로 다듬는다. 양 끝은 원래 점에 가깝게 둔다."""
    if len(pts) < 5:
        return pts
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    s = np.linspace(0, cum[-1], max(int(cum[-1] / 2), 5))
    pts = np.stack([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])], 1)
    sm = ndimage.gaussian_filter1d(pts, sigma / 2, axis=0, mode='nearest')
    k = min(len(pts) // 2, int(sigma))
    for i in range(k):
        w = i / max(k, 1)
        sm[i] = pts[i] * (1 - w) + sm[i] * w
        sm[-1 - i] = pts[-1 - i] * (1 - w) + sm[-1 - i] * w
    return sm


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.linalg.norm(ab)
    if n == 0:
        dist = np.linalg.norm(pts - a, axis=1)
    else:
        dist = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / n
    i = int(np.argmax(dist))
    if dist[i] > eps:
        return np.vstack([rdp(pts[:i + 1], eps)[:-1], rdp(pts[i:], eps)])
    return np.array([a, b])


result = {'lines': []}
for li, text in enumerate(LINES):
    img = np.array(Image.open('%s/l%d.png' % (LINES_DIR, li)).convert('L'))
    mask = ndimage.binary_closing(img < 128, iterations=1)
    sk = skeletonize(mask)
    dist = ndimage.distance_transform_edt(mask)
    sw = float(2 * np.median(dist[sk]))
    nodes, edges = simplify_graph(*build_graph(sk), sw)
    out = []
    for st in traverse(nodes, edges, sw):
        if length(st) < 0.8 * sw:
            continue
        # 이 획에서 글자가 가장 굵은 쪽에 맞춘 굵기. 마스크 선이 글자를 다 덮을 만큼 굵어야 한다.
        thick = 2 * float(np.percentile(dist[st[:, 1].astype(int), st[:, 0].astype(int)], 90))
        st = rdp(smooth(st, sw * 0.9), 0.35)
        g = np.stack([(st[:, 0] - CX) * UNIT, (st[:, 1] - BASE + li * LINE_HEIGHT * SIZE) * UNIT], 1)
        out.append({'thick': round(thick * UNIT, 2), 'pts': g.round(2).tolist()})
    result['lines'].append({'text': text, 'stroke_width': sw * UNIT, 'strokes': out})
    print('%s: 획 굵기 %.1fpx, 획 %d개' % (text, sw, len(out)), file=sys.stderr)
json.dump(result, open(OUT, 'w'))
