# -*- coding: utf-8 -*-
"""把检测到的框裁出来，排成带编号的接触表，便于逐个辨认。"""
import sys, math
from PIL import Image, ImageDraw, ImageFont
from detect import detect
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)

def sheet(png, out, cols=6, cw=300, ch=70, **kw):
    boxes = detect(png, **kw)
    im = Image.open(png).convert('RGBA')
    rows = math.ceil(len(boxes)/cols)
    c = Image.new('RGBA', (cols*cw, rows*ch), (18,18,26,255))
    d = ImageDraw.Draw(c)
    for i,(x0,y0,x1,y1) in enumerate(boxes):
        crop = im.crop((x0,y0,x1,y1))
        w,h = crop.size
        s = min((cw-46)/w, (ch-8)/h, 1.6)
        crop = crop.resize((max(1,int(w*s)), max(1,int(h*s))), Image.LANCZOS)
        cx, cy = (i%cols)*cw, (i//cols)*ch
        d.rectangle([cx,cy,cx+cw-2,cy+ch-2], outline=(70,70,90))
        d.text((cx+3, cy+ch//2-9), str(i), font=F, fill=(255,190,60))
        c.alpha_composite(crop, (cx+40, cy+(ch-crop.size[1])//2))
    c.convert('RGB').save(out)
    print(out, len(boxes), 'boxes')
    return boxes

if __name__ == '__main__':
    sheet(sys.argv[1], sys.argv[2])
