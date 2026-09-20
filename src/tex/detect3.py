# -*- coding: utf-8 -*-
"""递归 XY-cut：交替横切/竖切直到切不动为止。对付「某列有高元素导致整行连成一片」。"""
import numpy as np
from PIL import Image


def _runs(v, minrun):
    segs = []; s = None; run = 0
    for i, x in enumerate(v):
        if x > 0:
            if s is None: s = i
            run = 0
        else:
            if s is not None:
                run += 1
                if run >= minrun:
                    segs.append((s, i - run + 1)); s = None; run = 0
    if s is not None: segs.append((s, len(v)))
    return segs


def _hsegs(sub, vgap, max_h):
    """横切。若整段切不动且明显过高，剥掉「纵向贯通」的列后重试
       （比如右侧竖排的 FRONT/BACK，会把整片区域连成一块）。"""
    segs = _runs(sub.sum(axis=1), vgap)
    if len(segs) > 1 or sub.shape[0] <= max_h:
        return segs
    colspan = sub.sum(axis=0)
    for frac in (0.45, 0.32, 0.22, 0.15):
        tall = colspan > sub.shape[0] * frac
        if not tall.any():
            continue
        s2 = sub.copy(); s2[:, tall] = False
        segs2 = _runs(s2.sum(axis=1), vgap)
        if len(segs2) > 1:
            return segs2
    return segs


def _cut(a, y0, y1, x0, x1, vgap, hgap, horiz, depth, out, min_w, min_h, max_h):
    sub = a[y0:y1, x0:x1]
    if sub.size == 0 or not sub.any():
        return
    if horiz:
        segs = _hsegs(sub, vgap, max_h)
        if len(segs) > 1 or depth == 0:
            for s, e in segs:
                _cut(a, y0 + s, y0 + e, x0, x1, vgap, hgap, False, depth + 1, out, min_w, min_h, max_h)
            return
        return _cut(a, y0, y1, x0, x1, vgap, hgap, False, depth + 1, out, min_w, min_h, max_h)
    else:
        segs = _runs(sub.sum(axis=0), hgap)
        if len(segs) > 1:
            for s, e in segs:
                _cut(a, y0, y1, x0 + s, x0 + e, vgap, hgap, True, depth + 1, out, min_w, min_h, max_h)
            return
        # 竖切不动：再用「剥离贯通列」的横切试一次
        hs = _hsegs(sub, vgap, max_h)
        if len(hs) > 1:
            for s, e in hs:
                _cut(a, y0 + s, y0 + e, x0, x1, vgap, hgap, False, depth + 1, out, min_w, min_h, max_h)
            return
        # 切不动了 -> 收框
        rs = np.nonzero(sub.sum(axis=1))[0]
        cs = np.nonzero(sub.sum(axis=0))[0]
        b = [x0 + int(cs[0]), y0 + int(rs[0]), x0 + int(cs[-1]) + 1, y0 + int(rs[-1]) + 1]
        if b[2] - b[0] >= min_w and min_h <= b[3] - b[1] <= max_h:
            out.append(b)


def detect3(png, vgap=3, hgap=11, min_w=8, min_h=9, max_h=120, thr=128):
    a = np.array(Image.open(png).convert('RGBA'))[:, :, 3] > thr
    out = []
    _cut(a, 0, a.shape[0], 0, a.shape[1], vgap, hgap, True, 0, out, min_w, min_h, max_h)
    out.sort(key=lambda b: (b[1] // 12, b[0]))
    return out
