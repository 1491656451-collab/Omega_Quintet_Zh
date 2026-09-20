# -*- coding: utf-8 -*-
"""global\\Texture\\Sprites.dds —— PC 移植版新加的一张小图，
   设置界面的两个页签「Graphics / Input」各有选中/未选中两份，一直是英文。
   其余内容（Work In Progress、箭头、鼠标指针）不动。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import autostyle
from render3 import draw, ink_mask

HERE = os.path.dirname(os.path.abspath(__file__))

# (框, 中文)  —— 框是连通块量出来的，含外发光
# (框, 中文, 组) —— 同一组内字号必须统一。美术图里「选中」本来就比「未选中」大一号，
# 所以分两组，不能四条压成一个字号（第 16/17 轮在战斗指令表上踩过这个坑）。
JOBS = [
    ((266, 31, 401,  69), '图像', 'on'),
    ((267, 72, 346, 109), '输入', 'on'),
    ((268,120, 391, 154), '图像', 'off'),
    ((268,157, 338, 190), '输入', 'off'),
]


def metrics(a, box):
    """量出这条英文标签的：左边缘 x、基线 y、字身高 cap。
       两条都带下伸部（Input 的 p、Graphics 的 p），所以基线按
       「行覆盖率跌到峰值 40% 以下」的最后一行定，跌下去那截就是下伸部。"""
    x0, y0, x1, y1 = box
    al = a[y0:y1, x0:x1, 3].astype(float)
    thr = max(40.0, al.max() * 0.72)
    m = al > thr
    prof = m.sum(axis=1)
    peak = prof.max()
    rows = np.nonzero(prof > 0)[0]
    top = rows[0]
    body = np.nonzero(prof >= peak * 0.40)[0]
    base = body[-1]
    cols = np.nonzero(m.any(axis=0))[0]
    return dict(left=x0 + cols[0], right=x0 + cols[-1] + 1,
                baseline=y0 + base, cap=int(base - top + 1))


def ink_box(a, box):
    """框里「实心墨迹」的范围。未选中那两条整体半透（alpha 最高才 158），
       所以阈值按这个框自己的最大 alpha 取七成，不能写死。"""
    x0, y0, x1, y1 = box
    al = a[y0:y1, x0:x1, 3]
    thr = max(40, int(al.max() * 0.72))
    ys, xs = np.nonzero(al > thr)
    if not len(ys):
        return None
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def build(src_png, out_png, preview=None):
    im = Image.open(src_png).convert('RGBA')
    old = im.copy()
    a = np.array(im)
    plan = []
    for box, zh, grp in JOBS:
        st = autostyle.sample(a, box)
        mt = metrics(a, box)
        plan.append((box, zh, st, mt, grp))
        print('  %-9s[%s] 框%s 左%d 基线%d 字身%d  ew=%d glow=%s'
              % (zh, grp, box, mt['left'], mt['baseline'], mt['cap'], st['ew'], st['glow'] is not None))

    # 组内统一字号：取组里最小的那个
    gsize = {}
    for box, zh, st, mt, grp in plan:
        s0 = max(8, mt['cap'] - 2 * st['ew'])
        gsize[grp] = min(gsize.get(grp, 999), s0)
    print('  组内统一字号:', gsize)

    for box, zh, st, mt, grp in plan:
        x0, y0, x1, y1 = box
        a[y0:y1, x0:x1] = 0                       # 底本来就是透明的，直接清零
        pad = st['ew'] + (2 if st['glow'] else 0)
        size = gsize[grp]                          # 汉字墨高 ≈ 字号；描边是额外加出来的
        lab = draw(zh, size, st, x1 - x0)
        la = np.array(lab)
        # 游戏是按这条标签自己的 UV 矩形整块画的，中文比英文短，
        # 左对齐会看着偏左 —— 所以横向按原英文墨迹的中心居中。
        cx = (mt['left'] + mt['right']) // 2
        px = cx - la.shape[1] // 2
        py = mt['baseline'] + 1 - la.shape[0] + pad
        px = max(x0, min(px, x1 - la.shape[1]))
        py = max(y0, min(py, y1 - la.shape[0]))
        sub = a[py:py + la.shape[0], px:px + la.shape[1]]
        msk = la[:, :, 3] > 0
        sub[msk] = la[msk]
        print('  %-4s 字号 %2d 落笔 %dx%d @(%d,%d)  原英文 x %d..%d 中心 %d'
              % (zh, size, la.shape[1], la.shape[0], px, py, mt['left'], mt['right'], cx))

    out = Image.fromarray(a)
    out.save(out_png)
    if preview:
        W, H = out.size
        cv = Image.new('RGB', (W, H * 2 + 8), (26, 30, 40))
        for k, img in enumerate((old, out)):
            bg = Image.new('RGB', (W, H), (26, 30, 40)); bg.paste(img, (0, 0), img)
            cv.paste(bg, (0, k * (H + 8)))
        cv.save(preview)
    return out_png


if __name__ == '__main__':
    build('/tmp/cfg/Sprites_raw.png', os.path.join(HERE, 'sprites_zh.png'),
          '/tmp/cfg/对比_设置页签.png')
