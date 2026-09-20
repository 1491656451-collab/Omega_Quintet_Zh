# -*- coding: utf-8 -*-
"""量一块区域里「文字」的紧包围盒。mode: bright=亮度阈, chroma=彩度阈"""
import sys, json
import numpy as np
from PIL import Image

A = np.array(Image.open('all/global_Texture_grSystemBattle.png').convert('RGBA')).astype(int)

def tight(x0, y0, x1, y1, mode='bright', L=150, C=70, amin=140, colgap=None):
    s = A[y0:y1, x0:x1]
    a = s[:, :, 3]
    lum = s[:, :, :3].mean(axis=2)
    chr_ = s[:, :, :3].max(axis=2) - s[:, :, :3].min(axis=2)
    m = (a > amin) & ((lum > L) if mode == 'bright' else (chr_ > C))
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    box = [x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1]
    if colgap:
        col = m.any(axis=0)
        segs = []; st = None; run = 0
        for i, v in enumerate(col):
            if v:
                if st is None: st = i
                run = 0
            else:
                if st is not None:
                    run += 1
                    if run >= colgap:
                        segs.append((st, i - run + 1)); st = None; run = 0
        if st is not None: segs.append((st, len(col)))
        out = []
        for s0, s1 in segs:
            mm = m[:, s0:s1]
            yy = np.nonzero(mm.any(axis=1))[0]
            out.append([x0 + s0, y0 + int(yy.min()), x0 + s1, y0 + int(yy.max()) + 1])
        return box, out
    return box
