# -*- coding: utf-8 -*-
"""带坐标网格的放大图，用来人工读取精确矩形。"""
import sys
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 11)

def grid(src, box, out, S=3, step=10):
    im = Image.open(src).convert('RGBA')
    x0, y0, x1, y1 = box
    c = im.crop(box)
    bg = Image.new('RGBA', c.size, (28, 28, 36, 255)); bg.alpha_composite(c)
    q = bg.convert('RGB').resize((c.width * S, c.height * S), Image.NEAREST)
    cv = Image.new('RGB', (q.width + 46, q.height + 20), (0, 0, 0))
    cv.paste(q, (46, 20)); d = ImageDraw.Draw(cv)
    for x in range(x0 - x0 % step + step, x1, step):
        px = 46 + (x - x0) * S
        d.line([(px, 20), (px, cv.height)], fill=(255, 60, 60) if x % 50 == 0 else (70, 70, 70))
        if x % 20 == 0: d.text((px - 12, 4), str(x), font=F, fill=(255, 200, 60))
    for y in range(y0 - y0 % step + step, y1, step):
        py = 20 + (y - y0) * S
        d.line([(46, py), (cv.width, py)], fill=(255, 60, 60) if y % 50 == 0 else (70, 70, 70))
        d.text((2, py - 6), str(y), font=F, fill=(255, 200, 60))
    cv.save(out)
