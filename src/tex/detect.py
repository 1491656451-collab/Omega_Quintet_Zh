# -*- coding: utf-8 -*-
"""检测贴图里的标签框：连通域 + 宽框二次切分。"""
import numpy as np
from scipy import ndimage
from PIL import Image

def detect(png, ymin=0, min_w=18, min_h=12, max_h=110, gap=16, split_gap=18):
    a = np.array(Image.open(png))[:,:,3] > 8
    m = ndimage.binary_dilation(a, np.ones((1,gap//2*2+1), bool))
    lab, _ = ndimage.label(m)
    out = []
    for sl in ndimage.find_objects(lab):
        y0,y1 = sl[0].start, sl[0].stop
        x0,x1 = sl[1].start, sl[1].stop
        if y0 < ymin: continue
        if x1-x0 < min_w or y1-y0 < min_h or y1-y0 > max_h: continue
        # 二次切分：框内找 >=split_gap 的全透明列
        col = a[y0:y1, x0:x1].sum(axis=0)
        segs=[]; s=None; run=0
        for i,v in enumerate(col):
            if v>0:
                if s is None: s=i
                run=0
            else:
                if s is not None:
                    run+=1
                    if run>=split_gap:
                        segs.append((s, i-run+1)); s=None; run=0
        if s is not None: segs.append((s, len(col)))
        for sx,ex in segs:
            if ex-sx < min_w: continue
            sub = a[y0:y1, x0+sx:x0+ex]
            rs = np.nonzero(sub.sum(axis=1))[0]
            cs = np.nonzero(sub.sum(axis=0))[0]
            if len(rs)==0: continue
            out.append([x0+sx+int(cs[0]), y0+int(rs[0]), x0+sx+int(cs[-1])+1, y0+int(rs[-1])+1])
    out.sort(key=lambda b:(b[1]//18, b[0]))
    return out
