# -*- coding: utf-8 -*-
"""渲染 grSystemMenuMain 中文版：统一字号 + 逐行统一竖直框。"""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from collections import defaultdict
import map_menu
from render2 import draw, STYLES

HERE=os.path.dirname(os.path.abspath(__file__))

def split_box(a,b):
    x0,y0,x1,y1=b; col=a[y0:y1,x0:x1].sum(axis=0)
    g=[];s=None
    for i,v in enumerate(col):
        if v==0:
            if s is None: s=i
        else:
            if s is not None: g.append((i-s,s,i)); s=None
    if not g: return [b]
    w,gs,ge=max(g); return [[x0,y0,x0+gs,y1],[x0+ge,y0,x1,y1]]

def build(src_png, boxes_json, sizes_json, out_png):
    atlas=Image.open(src_png).convert('RGBA')
    a=np.array(atlas)[:,:,3]>8
    boxes=json.load(open(boxes_json))
    S=json.load(open(sizes_json))
    items=[]
    for i,b in enumerate(boxes):
        v=map_menu.M.get(i)
        if not v: continue
        txt,st=v; parts=txt.split('|')
        bs=split_box(a,b) if len(parts)>1 else [b]
        for t,bb in zip(parts,bs): items.append((t,st,bb))
    # 按 (样式, 行) 分组，取该组统一的上下边界
    grp=defaultdict(list)
    for k,(t,st,bb) in enumerate(items): grp[(st,bb[1]//20)].append(k)
    frame={}
    for key,ids in grp.items():
        top=min(items[i][2][1] for i in ids); bot=max(items[i][2][3] for i in ids)
        for i in ids: frame[i]=(top,bot)
    # 先清空所有标签区域，再统一绘制（避免相邻框互相擦掉）
    for t,st,bb in items:
        atlas.paste((0,0,0,0),tuple(bb))
    n=0
    for k,(t,st,bb) in enumerate(items):
        x0,y0,x1,y1=bb
        top,bot=frame[k]
        lab=draw(t,S[st],st,x1-x0)
        ox=x0+((x1-x0)-lab.width)//2
        oy=top+((bot-top)-lab.height)//2
        atlas.alpha_composite(lab,(ox,oy)); n+=1
    atlas.save(out_png)
    return n,S

if __name__=='__main__':
    n,S=build(os.path.join(HERE,'global_Texture_grSystemMenuMain.png'),
              os.path.join(HERE,'menu_boxes.json'),
              os.path.join(HERE,'menu_sizes.json'),
              os.path.join(HERE,'menu_zh.png'))
    print(f"渲染 {n} 个标签，字号 {S}")
