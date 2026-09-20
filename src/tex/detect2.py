# -*- coding: utf-8 -*-
"""XY-cut 递归切分：先横切成行，再竖切成词，避免跨行/跨标签粘连。"""
import numpy as np
from PIL import Image


def _runs(v, minrun):
    """返回 v 中值>0 的连续段 [(s,e)]，忽略长度<minrun 的空隙。"""
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


def detect2(png, vgap=4, hgap=10, min_w=8, min_h=9, max_h=120, thr=8):
    """vgap: 行间最小空行数; hgap: 词间最小空列数（词内字距要小于它）"""
    a = np.array(Image.open(png).convert('RGBA'))[:, :, 3] > thr
    out = []
    for r0, r1 in _runs(a.sum(axis=1), vgap):
        if r1 - r0 < min_h or r1 - r0 > max_h: continue
        band = a[r0:r1]
        for c0, c1 in _runs(band.sum(axis=0), hgap):
            if c1 - c0 < min_w: continue
            sub = band[:, c0:c1]
            rs = np.nonzero(sub.sum(axis=1))[0]
            cs = np.nonzero(sub.sum(axis=0))[0]
            out.append([c0 + int(cs[0]), r0 + int(rs[0]),
                        c0 + int(cs[-1]) + 1, r0 + int(rs[-1]) + 1])
    out.sort(key=lambda b: (b[1], b[0]))
    return out
