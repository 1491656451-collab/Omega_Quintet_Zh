# -*- coding: utf-8 -*-
"""从原贴图像素里自动采样某个标签框的样式：
   填充色（按 y 的线性渐变）、描边色、外发光色、描边宽度。
   这样不用为每张贴图手写样式表。"""
import numpy as np
from PIL import Image
from scipy import ndimage


def sample(png_or_arr, box, core_erode=2, ring=1):
    a = np.array(Image.open(png_or_arr).convert('RGBA')) if isinstance(png_or_arr, str) else png_or_arr
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1].astype(np.float64)
    rgb, al = sub[:, :, :3], sub[:, :, 3]
    solid = al > 200
    if solid.sum() < 20:
        solid = al > 100
    # 核心 = 腐蚀后的实心区（避开描边）。细笔画被腐蚀光时退而求其次，
    # 再按亮度把最暗的一成去掉 —— 那些是抗锯齿过渡像素，会把填充色拉暗。
    core = ndimage.binary_erosion(solid, np.ones((3, 3), bool), iterations=core_erode)
    if core.sum() < 10:
        core = ndimage.binary_erosion(solid, np.ones((3, 3), bool), iterations=1)
    if core.sum() < 5:
        core = solid
    lum_all = rgb.mean(axis=2)
    if core.sum() >= 8:
        cut = np.percentile(lum_all[core], 22)
        c2 = core & (lum_all >= cut)
        if c2.sum() >= 6:
            core = c2
    # 描边 = 实心区减去(核心再膨胀)
    edge = solid & ~ndimage.binary_dilation(core, np.ones((3, 3), bool), iterations=ring)
    if edge.sum() < 5:
        edge = solid & ~core

    H = y1 - y0
    ys, xs = np.nonzero(core)
    # 填充色按 y 做线性拟合 -> 顶色/底色
    top, bot = [], []
    if len(ys):
        t = (ys - ys.min()) / max(1, (ys.max() - ys.min()))
        for ch in range(3):
            v = rgb[:, :, ch][core]
            A = np.vstack([t, np.ones_like(t)]).T
            k, b = np.linalg.lstsq(A, v, rcond=None)[0]
            top.append(b); bot.append(k + b)
    else:
        top = bot = list(rgb[:, :, :3].reshape(-1, 3).mean(axis=0))

    oc = rgb[edge].mean(axis=0) if edge.sum() else np.array([0, 0, 0.])

    # 外发光：实心区外 2~5px 圈里、alpha 在 20~180 的像素
    halo = ndimage.binary_dilation(solid, np.ones((3, 3), bool), iterations=4) & ~ndimage.binary_dilation(solid, np.ones((3, 3), bool), iterations=1)
    # 真正的外发光是半透明的；旁边挨着的实心图标（星星之类）alpha 是满的，
    # 不排掉就会把邻居的颜色当成发光色，渲染出一团灰блок。
    hm = halo & (al > 20) & (al < 230)
    glow = None
    if hm.sum() > 40 and (halo & (al > 230)).sum() < hm.sum() * 0.5:
        g = rgb[hm].mean(axis=0)
        if np.abs(g - oc).max() > 25:
            glow = tuple(int(round(v)) for v in np.clip(g, 0, 255))

    # 描边宽度：实心区里到背景的距离中位数的一半
    dist = ndimage.distance_transform_edt(solid)
    ew = max(1, int(round(np.median(dist[edge]) if edge.sum() else 1)))
    ew = min(ew, max(1, H // 10))

    cl = lambda v: tuple(int(round(x)) for x in np.clip(v, 0, 255))
    return dict(top=cl(top), bot=cl(bot), outline=cl(oc), glow=glow, ew=ew, h=H)


def key(st, q=28):
    """样式签名，用来把颜色相近的标签归成一类。"""
    f = lambda c: tuple(v // q for v in c)
    return (f(st['top']), f(st['bot']), f(st['outline']), st['glow'] is not None)
