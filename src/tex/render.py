# -*- coding: utf-8 -*-
"""把中文以原样式绘制进贴图标签框。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy import ndimage

FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'

STYLES={
 # name: (填充上色, 填充下色, 描边色, 描边宽, 外发光)
 'big'  : ((238,244,253),(118,136,168),( 26, 42, 92), 4, (255,255,255,120)),
 'gold' : ((255,226, 40),(196,126,  0),( 48, 24,  8), 3, None),
 'gray' : ((219,222,226),(122,131,149),( 48, 56, 72), 3, None),
}

def _mask(text,size,box_w,box_h):
    """返回刚好容纳 text 的字形 mask 和实际尺寸。"""
    f=ImageFont.truetype(FONT,size,index=2)   # index 2 = SC
    tmp=Image.new('L',(size*len(text)*2+80, size*3),0)
    d=ImageDraw.Draw(tmp); d.text((20,20),text,font=f,fill=255)
    bb=tmp.getbbox()
    return tmp.crop(bb), f

def render_label(text, box_w, box_h, style, fill=0.92):
    up,dn,oc,_ow,glow=STYLES[style]
    ow=max(2,round(box_h/15))          # 描边宽随字号缩放
    # 中文字形 bbox 约为字号的 0.72，故从 box_h/0.72 起步向下收
    size=max(8,int(box_h/0.70))
    for _ in range(40):
        m,_f=_mask(text,size,box_w,box_h)
        if m.width+2*ow<=box_w*fill and m.height+2*ow<=box_h: break
        size-=1
        if size<8: break
    m,_f=_mask(text,size,box_w,box_h)
    W,H=m.size
    pad=ow
    canvas=Image.new('RGBA',(W+2*pad,H+2*pad),(0,0,0,0))
    mm=Image.new('L',canvas.size,0); mm.paste(m,(pad,pad))
    a=np.array(mm)>100
    # 描边 = 膨胀环
    grown=ndimage.binary_dilation(a,np.ones((2*ow+1,2*ow+1),bool))
    out=np.zeros((canvas.size[1],canvas.size[0],4),np.uint8)
    out[grown]=(*oc,255)
    # 填充渐变
    ys=np.arange(canvas.size[1])[:,None]
    t=(ys/max(1,canvas.size[1]-1))
    grad=(np.array(up)[None,None,:]*(1-t[:,:,None])+np.array(dn)[None,None,:]*t[:,:,None]).astype(np.uint8)
    grad=np.broadcast_to(grad,(canvas.size[1],canvas.size[0],3))
    out[a,:3]=grad[a]; out[a,3]=255
    img=Image.fromarray(out,'RGBA')
    if glow:
        g=Image.new('RGBA',img.size,glow[:3]+(0,))
        ga=Image.fromarray((grown*90).astype(np.uint8),'L').filter(ImageFilter.GaussianBlur(ow*1.4))
        g.putalpha(ga)
        img=Image.alpha_composite(g,img)
    return img

def place(atlas, box, text, style):
    """把 text 渲染后居中放进 box（先清空原内容）。"""
    x0,y0,x1,y1=box
    bw,bh=x1-x0,y1-y0
    atlas.paste((0,0,0,0),(x0,y0,x1,y1))
    if not text: return
    lab=render_label(text,bw,bh,style)
    ox=x0+(bw-lab.width)//2; oy=y0+(bh-lab.height)//2
    atlas.paste(lab,(ox,oy),lab)
