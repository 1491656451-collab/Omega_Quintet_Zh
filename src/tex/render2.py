# -*- coding: utf-8 -*-
"""统一字号渲染：同一样式用同一字号，同一行用同一竖直框，宽度不足时只横向压缩。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy import ndimage

FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
STYLES={
 'big'  : ((238,244,253),(118,136,168),( 26, 42, 92), 4, True),
 'gold' : ((255,226, 40),(196,126,  0),( 48, 24,  8), 2, False),
 'gray' : ((219,222,226),(122,131,149),( 48, 56, 72), 2, False),
}
_fc={}
def _font(size):
    if size not in _fc: _fc[size]=ImageFont.truetype(FONT,size,index=2)
    return _fc[size]

def ink_mask(text,size):
    f=_font(size)
    tmp=Image.new('L',(size*(len(text)+2)*2, size*3),0)
    ImageDraw.Draw(tmp).text((size,size//2),text,font=f,fill=255)
    bb=tmp.getbbox()
    return tmp.crop(bb)

def fit_size(labels, styles, boxes_w, frame_h, min_squeeze=0.82):
    """labels/styles/boxes_w 同长；返回该样式下可用的最大统一字号。"""
    lo,hi=8,120; best=8
    while lo<=hi:
        S=(lo+hi)//2
        ok=True
        for t,bw in zip(labels,boxes_w):
            m=ink_mask(t,S)
            ow=STYLES[styles][3]
            if m.height+2*ow>frame_h: ok=False; break
            if (m.width+2*ow) > bw/min_squeeze: ok=False; break
        if ok: best=S; lo=S+1
        else: hi=S-1
    return best

def draw(text,size,style,box_w):
    up,dn,oc,ow,glow=STYLES[style]
    m=ink_mask(text,size)
    # 宽度不够 -> 只横向压缩
    avail=box_w-2*ow
    if m.width>avail and m.width>0:
        m=m.resize((max(1,avail),m.height),Image.LANCZOS)
    W,H=m.size; pad=ow
    cv=Image.new('L',(W+2*pad,H+2*pad),0); cv.paste(m,(pad,pad))
    a=np.array(cv)>100
    grown=ndimage.binary_dilation(a,np.ones((2*ow+1,2*ow+1),bool))
    out=np.zeros((cv.size[1],cv.size[0],4),np.uint8)
    out[grown]=(*oc,255)
    ys=np.arange(cv.size[1])[:,None]/max(1,cv.size[1]-1)
    grad=(np.array(up)*(1-ys[:,:,None])+np.array(dn)*ys[:,:,None]).astype(np.uint8)
    grad=np.broadcast_to(grad,(cv.size[1],cv.size[0],3))
    out[a,:3]=grad[a]; out[a,3]=255
    img=Image.fromarray(out,'RGBA')
    if glow:
        g=Image.new('RGBA',img.size,(255,255,255,0))
        g.putalpha(Image.fromarray((grown*85).astype(np.uint8),'L').filter(ImageFilter.GaussianBlur(ow*1.3)))
        img=Image.alpha_composite(g,img)
    return img
