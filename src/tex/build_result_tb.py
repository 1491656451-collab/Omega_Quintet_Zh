# -*- coding: utf-8 -*-
"""grSystemResult 的 Total Bonus / Next 两条：擦掉英文，换成斜体中文。

### 为什么能擦干净
放大看清楚之后发现两件事：
  1. 这两处英文**大半个字身压在透明背景上**，只有下半截压在光条上；
  2. 光条是**纯竖直渐变** —— 同一行里颜色从左到右一模一样
     （只有 Total Bonus 那条的 y=374/375 青色高光是横向渐变的）。
所以按行取背景色回填就能完全还原，不需要任何 inpaint 猜测。

### 第一版踩的坑（务必别再犯）
取背景色的列选了 x=246..300，而 **Next 那条光条到 x≈255 就结束了**，
246..300 大半是透明区，取出来的「背景色」是 alpha=0 ——
等于在光条上掏了个洞。预览图当时把 RGBA 转成 RGB 看，透明显示成白色，
和旁边的亮部混在一起，没看出来。
==> 取样列必须**紧贴文字**，而且要 assert 它确实不透明；
==> 预览必须**合成到深色底上**，再单独出一张 alpha 图。
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render3 import FONT, _font

SRC = os.path.join(HERE, 'result_zh.png')
SHEAR = 0.23                       # tan(13°)，和英文的倾斜角一致

# 白→浅蓝渐变 + 深蓝描边，和英文一致；不加外发光（加了是一圈方方的暗晕）
STYLE = dict(top=(255, 255, 255), bot=(150, 190, 226), outline=(13, 25, 70), ew=2)

JOBS = [
    dict(name='Total Bonus', zh='合计加成',
         erase=(56, 360, 242, 391),       # 英文的 l 顶端还有 2 个像素在 y=362
         draw=(56, 363, 242, 391),        # 落笔只能在标签框 [11,363,503,413] 之内
         sample=(250, 330),               # 这一段整段不透明、且和文字左右同色
         ramp_rows=(374, 375), ramp_left=(48, 54),
         size=22, spacing=12, anchor='left'),
    dict(name='Next', zh='下一步',
         erase=(157, 439, 232, 470),
         draw=(140, 440, 246, 470),       # 光条平坦区 x≈82..253，往左右各放一点
         sample=(236, 249),               # 紧贴文字右侧；再往右 x>255 就是透明区了
         ramp_rows=(), ramp_left=None,
         size=24, spacing=6, anchor='center', center_on=194),
]


def rowbg(a, y, sx0, sx1):
    return np.median(a[y, sx0:sx1].astype(float), axis=0)


def erase(a, job):
    """按行回填背景；回填完再和紧邻的框外像素对一遍，防止取样列取歪。"""
    x0, y0, x1, y1 = job['erase']
    sx0, sx1 = job['sample']
    for y in range(y0, y1):
        bg = rowbg(a, y, sx0, sx1)
        if y in job['ramp_rows']:
            lx0, lx1 = job['ramp_left']
            left = rowbg(a, y, lx0, lx1)
            t = np.linspace(0, 1, x1 - x0)[:, None]
            a[y, x0:x1] = (left * (1 - t) + bg * t).round().astype(np.uint8)
        else:
            a[y, x0:x1] = bg.round().astype(np.uint8)
    # 自检：擦完的右边缘必须和框外紧邻的像素一致（alpha 也要一致）
    bad = []
    for y in range(y0, y1):
        inner = a[y, x1 - 1].astype(int)
        outer = a[y, x1 + 2].astype(int)
        if abs(int(inner[3]) - int(outer[3])) > 12 or np.abs(inner[:3] - outer[:3]).sum() > 40:
            bad.append((y, tuple(inner), tuple(outer)))
    if bad:
        raise SystemExit(f"{job['name']} 擦除后和框外对不上（取样列可能取歪了）：{bad[:6]}")
    return a


def ink(text, size, spacing):
    """逐字渲染再按字距拼，这样能把标签拉宽到和英文差不多的横向占位。

    竖直方向**只在最后整体裁一次**：每个字都画在同一条基线上，只横向裁掉左右空白。
    上一版是逐字上下都裁再「底对齐」，「一」这种只有一横的字被顶到了基线上，
    看起来整个字沉下去了 —— 就是你说的「下一步的一不居中」。
    """
    f = _font(size)
    H = size * 3
    imgs = []
    for ch in text:
        tmp = Image.new('L', (size * 3, H), 0)
        ImageDraw.Draw(tmp).text((size, size // 2), ch, font=f, fill=255)
        bb = tmp.getbbox()
        imgs.append(tmp.crop((bb[0], 0, bb[2], H)) if bb else Image.new('L', (1, H), 0))
    W = sum(i.width for i in imgs) + spacing * (len(imgs) - 1)
    cv = Image.new('L', (W, H), 0)
    x = 0
    for i in imgs:
        cv.paste(i, (x, 0), i)
        x += i.width + spacing
    bb = cv.getbbox()
    return cv.crop(bb) if bb else cv


def draw_label(text, size, spacing):
    from scipy import ndimage
    up, dn, oc, ew = STYLE['top'], STYLE['bot'], STYLE['outline'], STYLE['ew']
    m = ink(text, size, spacing)
    pad = ew
    cv = Image.new('L', (m.width + 2 * pad, m.height + 2 * pad), 0)
    cv.paste(m, (pad, pad))
    A = np.array(cv) > 100
    grown = ndimage.binary_dilation(A, np.ones((2 * ew + 1, 2 * ew + 1), bool))
    out = np.zeros((cv.size[1], cv.size[0], 4), np.uint8)
    out[grown] = (*oc, 255)
    ys = np.arange(cv.size[1])[:, None] / max(1, cv.size[1] - 1)
    grad = (np.array(up) * (1 - ys[:, :, None]) + np.array(dn) * ys[:, :, None]).astype(np.uint8)
    grad = np.broadcast_to(grad, (cv.size[1], cv.size[0], 3))
    out[A, :3] = grad[A]
    out[A, 3] = 255
    return Image.fromarray(out, 'RGBA')


def italic(img, k=SHEAR):
    W, H = img.size
    return img.transform((W + int(abs(k) * H) + 2, H), Image.AFFINE,
                         (1, k, -k * (H - 1), 0, 1, 0), resample=Image.BICUBIC)


def main(out_path=None, preview=None):
    im = Image.open(SRC).convert('RGBA')
    old = im.copy()          # 原图快照：out_path 可能就是 SRC，存完再读就读到新图了
    a = np.array(im)
    for job in JOBS:
        a = erase(a, job)
    im = Image.fromarray(a, 'RGBA')

    for job in JOBS:
        x0, y0, x1, y1 = job['draw']
        size, sp = job['size'], job['spacing']
        while True:                       # 字号写死容易和框差一两个像素，兜个底
            lab = italic(draw_label(job['zh'], size, sp))
            if lab.width <= x1 - x0 and lab.height <= y1 - y0:
                break
            size -= 1
            assert size >= 10, job['name']
        job['size'] = size
        if job['anchor'] == 'center':
            ox = job['center_on'] - lab.width // 2
            ox = max(x0, min(ox, x1 - lab.width))
        else:
            ox = x0 + 2
        oy = y0 + ((y1 - y0) - lab.height) // 2
        im.alpha_composite(lab, (ox, oy))
        print(f"  {job['name']:12s} -> {job['zh']}  字号 {job['size']} 字距 {job['spacing']} "
              f"斜体，标签 {lab.size} 放在 {(ox, oy)}")

    if out_path:
        im.save(out_path)
    if preview:
        rows = []
        for job in JOBS:
            x0, y0, x1, y1 = job['draw']
            pad = 16
            box = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
            for src in (old, im):
                c = src.crop(box)
                bg = Image.new('RGBA', c.size, (40, 40, 48, 255))   # 深色底，透明洞一眼看得见
                bg.alpha_composite(c)
                rows.append(bg.convert('RGB'))
                rows.append(Image.merge('RGB', [c.getchannel('A')] * 3))  # alpha 图
        S = 4
        W = max(p.width for p in rows) * S
        H = sum(p.height for p in rows) * S + 10 * len(rows)
        cv = Image.new('RGB', (W, H), (0, 0, 0))
        y = 0
        for p in rows:
            q = p.resize((p.width * S, p.height * S), Image.NEAREST)
            cv.paste(q, (0, y)); y += q.height + 10
        cv.save(preview)
    return im


if __name__ == '__main__':
    main(out_path=os.path.join(HERE, '_tb_new.png'),
         preview=os.path.join(HERE, '_tb_preview.png'))
    print('预览 _tb_preview.png：每条四行 = 旧图/旧alpha/新图/新alpha，深色底')
