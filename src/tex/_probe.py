# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
from scipy import ndimage
A = np.array(Image.open('all/global_Texture_grSystemBattle.png').convert('RGBA')).astype(int)

def comps(box, mode='bright', L=185, C=70, amin=150, wmax=280, hmin=8, hmax=45, merge=18):
    x0, y0, x1, y1 = box
    s = A[y0:y1, x0:x1]
    lum = s[:, :, :3].mean(axis=2)
    chr_ = s[:, :, :3].max(axis=2) - s[:, :, :3].min(axis=2)
    m = (s[:, :, 3] > amin) & ((lum > L) if mode == 'bright' else (chr_ > C))
    lab, n = ndimage.label(m, np.ones((3, 3)))
    out = []
    for o in ndimage.find_objects(lab):
        h = o[0].stop - o[0].start; w = o[1].stop - o[1].start
        if w > wmax or h < hmin or h > hmax: continue
        out.append([x0 + o[1].start, y0 + o[0].start, x0 + o[1].stop, y0 + o[0].stop])
    out.sort(key=lambda b: b[0])
    # 横向合并成词
    res = []
    for b in out:
        if res and b[0] - res[-1][2] <= merge:
            r = res[-1]
            r[1] = min(r[1], b[1]); r[2] = max(r[2], b[2]); r[3] = max(r[3], b[3])
        else:
            res.append(list(b))
    return res
