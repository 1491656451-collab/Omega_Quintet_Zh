# -*- coding: utf-8 -*-
"""通用标签渲染：样式参数来自 autostyle.sample()（从原像素采样），
   不再依赖手写样式表。字号在组内统一。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy import ndimage

FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
_fc = {}


def _font(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(FONT, size, index=2)
    return _fc[size]


def ink_mask(text, size):
    f = _font(size)
    tmp = Image.new('L', (size * (len(text) + 2) * 2, size * 3), 0)
    ImageDraw.Draw(tmp).text((size, size // 2), text, font=f, fill=255)
    bb = tmp.getbbox()
    return tmp.crop(bb) if bb else Image.new('L', (1, 1), 0)


def fit_each(labels, widths, heights, ew, min_squeeze=0.80, lo=8, hi=120, glow=False):
    """每个标签按「自己的框」算能用的最大字号，取全组最小值。
       不用交集框：交集会把 y0 最低和 y1 最高两个极端叠在一起，字号被压得过小。"""
    best = hi
    for t, bw, bh in zip(labels, widths, heights):
        s = fit_size([t], [bw], bh, ew, min_squeeze, lo, hi, glow)
        best = min(best, s)
    return best


def fit_size(labels, widths, frame_h, ew, min_squeeze=0.80, lo=8, hi=120, glow=False):
    """一组标签共用的最大字号：竖直必须塞进 frame_h，横向最多压到 min_squeeze。"""
    best = lo
    while lo <= hi:
        S = (lo + hi) // 2
        ok = True
        for t, bw in zip(labels, widths):
            m = ink_mask(t, S)
            # 外发光是软的、半透明的，允许溢出框一点点，不计入高度约束，
            # 否则带发光的标签会被硬生生压小一号。
            pad = ew
            if m.height + 2 * pad > frame_h:
                ok = False; break
            if (m.width + 2 * pad) > bw / min_squeeze:
                ok = False; break
        if ok:
            best = S; lo = S + 1
        else:
            hi = S - 1
    return best


def draw(text, size, st, box_w):
    """st 来自 autostyle.sample()"""
    up, dn, oc, glow, ew = st['top'], st['bot'], st['outline'], st['glow'], st['ew']
    m = ink_mask(text, size)
    avail = max(1, box_w - 2 * ew)
    if m.width > avail:
        m = m.resize((avail, m.height), Image.LANCZOS)
    W, H = m.size
    pad = ew + (2 if glow else 0)
    cv = Image.new('L', (W + 2 * pad, H + 2 * pad), 0)
    cv.paste(m, (pad, pad))
    a = np.array(cv) > 100
    if not a.any():
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    grown = ndimage.binary_dilation(a, np.ones((2 * ew + 1, 2 * ew + 1), bool))
    out = np.zeros((cv.size[1], cv.size[0], 4), np.uint8)
    out[grown] = (*oc, 255)
    ys = np.arange(cv.size[1])[:, None] / max(1, cv.size[1] - 1)
    grad = (np.array(up) * (1 - ys[:, :, None]) + np.array(dn) * ys[:, :, None]).astype(np.uint8)
    grad = np.broadcast_to(grad, (cv.size[1], cv.size[0], 3))
    out[a, :3] = grad[a]
    out[a, 3] = 255
    img = Image.fromarray(out, 'RGBA')
    if glow:
        g = Image.new('RGBA', img.size, (*glow, 0))
        ga = st.get('glow_a', 80)
        gr = st.get('glow_r', max(2.6, ew * 2.2))
        g.putalpha(Image.fromarray((grown * ga).astype(np.uint8), 'L')
                   .filter(ImageFilter.GaussianBlur(gr)))
        img = Image.alpha_composite(g, img)
    return img
