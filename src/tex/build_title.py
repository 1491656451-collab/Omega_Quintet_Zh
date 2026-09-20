# -*- coding: utf-8 -*-
"""标题画面三个菜单项：New Game / Continue / Config。
   贴图是 256x64 的独立 tid，一张一个词，所以直接整张重绘，
   三个用同一字号、同一基线，保证标题画面上看起来是一套。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from render3 import draw

HERE = os.path.dirname(os.path.abspath(__file__))

# 从原图采样后手工提亮：原图顶部接近纯白，采样会被抗锯齿拉灰
# glow_r 要小：原文的青色外发光是紧贴笔画的，半径一大，汉字笔画密，
# 几个字的光晕会连成一块灰底。
STYLE = dict(top=(252, 254, 255), bot=(146, 176, 222),
             outline=(18, 56, 112), glow=(46, 226, 200), ew=2,
             glow_a=150, glow_r=1.6)

ITEMS = [('menu_Newgame',  '新游戏'),
         ('menu_Continue', '继续游戏'),
         ('menu_Config',   '设置')]

SIZE = 42
CENTER_Y = 30     # 原文 New Game / Continue 的墨迹中心


def build(outdir=os.path.join(HERE, 'title_zh')):
    os.makedirs(outdir, exist_ok=True)
    made = []
    for name, zh in ITEMS:
        src = os.path.join(HERE, 'title', f'{name}__{name}.png')
        W, H = Image.open(src).size
        cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lab = draw(zh, SIZE, STYLE, W - 8)
        cv.alpha_composite(lab, ((W - lab.width) // 2, CENTER_Y - lab.height // 2))
        p = os.path.join(outdir, f'{name}.png')
        cv.save(p); made.append(p)
        print(f'{name:14s} {zh}  {lab.size}  -> {os.path.basename(p)}')
    return made


if __name__ == '__main__':
    build()
