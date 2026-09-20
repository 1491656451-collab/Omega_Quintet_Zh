# -*- coding: utf-8 -*-
"""把一个检测框切成指定数量的子框：先按行，再按列，
   自动搜索 (行间距, 词间距) 使子框数正好等于期望值。"""
import numpy as np
from detect3 import _runs


def _grid(a, box, vgap, hgap, min_w=3, min_h=5):
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    out = []
    for r0, r1 in _runs(sub.sum(axis=1), vgap):
        if r1 - r0 < min_h: continue
        band = sub[r0:r1]
        for c0, c1 in _runs(band.sum(axis=0), hgap):
            if c1 - c0 < min_w: continue
            s = band[:, c0:c1]
            rs = np.nonzero(s.sum(axis=1))[0]; cs = np.nonzero(s.sum(axis=0))[0]
            out.append([x0 + c0 + int(cs[0]), y0 + r0 + int(rs[0]),
                        x0 + c0 + int(cs[-1]) + 1, y0 + r0 + int(rs[-1]) + 1])
    return out


def cut_to_n(a, box, n, hi=40):
    """返回正好 n 个子框（行优先顺序）；找不到则返回 None。"""
    best = None
    for vgap in (3, 2, 1, 4, 5):
        for hgap in range(hi, 1, -1):
            g = _grid(a, box, vgap, hgap)
            if len(g) == n:
                return g
            if best is None and len(g) > n:
                best = g
    return None


def cut_groups(a, box, counts, hi=40):
    """counts = 每个标签占几个「词」，例如 [3,3,1,1]。
       先切成 sum(counts) 个词框，再按行内顺序合并。"""
    n = sum(counts)
    g = cut_to_n(a, box, n, hi)
    if not g:
        return None
    out = []; k = 0
    for c in counts:
        part = g[k:k + c]; k += c
        out.append([min(p[0] for p in part), min(p[1] for p in part),
                    max(p[2] for p in part), max(p[3] for p in part)])
    return out
