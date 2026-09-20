# -*- coding: utf-8 -*-
"""Game4.bra 里的标题画面六个菜单项。
   （Game1.bra 只有其中三个，Load Game / DLC Menu / Quit 只存在于 Game4。）
   每张 256x64，一张一个词，整张重绘，六个共用同一字号和基线。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from render3 import draw, ink_mask

HERE = os.path.dirname(os.path.abspath(__file__))

STYLE = dict(top=(252, 254, 255), bot=(146, 176, 222),
             outline=(18, 56, 112), glow=(46, 226, 200), ew=2,
             glow_a=150, glow_r=1.6)

ITEMS = [('Newgame',  '新游戏'),
         ('Continue', '继续游戏'),
         ('LoadGame', '读取存档'),
         ('Config',   '设置'),
         ('DLCMenu',  'DLC菜单'),
         ('Quit',     '退出游戏')]

CENTER_Y = 30


def build(srcdir=os.path.join(HERE, 'title4'),
          outdir=os.path.join(HERE, 'title4_zh')):
    os.makedirs(outdir, exist_ok=True)
    W, H = Image.open(os.path.join(srcdir, 'Newgame.png')).size
    # 字号必须和 build_title.py（Game1 里那三张）完全一致。
    # 之前这里是「自动求最大可用字号」，算出来 44，而 Game1 那边写死 42 ——
    # 游戏里 新游戏/继续游戏/设置 取 Game1、读取存档/DLC菜单/退出游戏 取 Game4，
    # 于是同一屏上六个菜单项有两种字号，后三个明显更大。
    from build_title import SIZE as S
    for _, zh in ITEMS:
        m = ink_mask(zh, S)
        assert m.width <= W - 8 and m.height <= 52, (zh, m.size)
    for name, zh in ITEMS:
        cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lab = draw(zh, S, STYLE, W - 8)
        cv.alpha_composite(lab, ((W - lab.width) // 2, CENTER_Y - lab.height // 2))
        cv.save(os.path.join(outdir, f'menu_{name}.png'))
        print(f'  menu_{name:9s} {zh:8s} {lab.size}')
    print(f'标题菜单 6 项，统一字号 {S}')
    return S


if __name__ == '__main__':
    build()
