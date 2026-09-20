# -*- coding: utf-8 -*-
import json, math, sys
from PIL import Image, ImageDraw, ImageFont
from detect3 import detect3
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)

def make(src, tag, cols=5, cw=360, ch=64, parts=3, **kw):
    boxes = detect3(src, **kw)
    json.dump(boxes, open(f'_b_{tag}.json', 'w'))
    im = Image.open(src).convert('RGBA')
    rows = math.ceil(len(boxes)/cols)
    c = Image.new('RGBA', (cols*cw, rows*ch), (18,18,26,255)); d = ImageDraw.Draw(c)
    for i,(x0,y0,x1,y1) in enumerate(boxes):
        cr = im.crop((x0,y0,x1,y1)); w,h = cr.size
        s = min((cw-56)/w, (ch-8)/h, 2.4)
        cr = cr.resize((max(1,int(w*s)), max(1,int(h*s))), Image.LANCZOS)
        cx,cy = (i%cols)*cw, (i//cols)*ch
        d.rectangle([cx,cy,cx+cw-2,cy+ch-2], outline=(70,70,90))
        d.text((cx+4, cy+ch//2-9), str(i), font=F, fill=(255,190,60))
        c.alpha_composite(cr, (cx+50, cy+(ch-cr.size[1])//2))
    c = c.convert('RGB')
    h = math.ceil(c.size[1]/parts)
    for i in range(parts):
        c.crop((0,i*h,c.size[0],min(h*(i+1),c.size[1]))).save(f'_s_{tag}_{i}.png')
    print(tag, len(boxes), c.size)
