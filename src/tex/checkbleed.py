# -*- coding: utf-8 -*-
"""校验：改动过的像素必须全部落在「被替换的标签自己的框」里面。
   溢出到框外 = 会污染游戏里相邻的那个精灵（UV 是按框取的）。"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from build_tex import collect
from detect3 import detect3


def check(src, mapmod, out, pad=0):
    mod = importlib.import_module(mapmod)
    M = mod.M
    a = np.array(Image.open(src).convert('RGBA')).astype(int)
    b = np.array(Image.open(out).convert('RGBA')).astype(int)
    d = np.abs(a - b).sum(axis=2) > 16
    _, _, boxes, items, _ = collect(src, M)
    allow = np.zeros(d.shape, bool)
    for t, bb, st, p, pl, tg in items:
        x0, y0, x1, y1 = (tg if tg else bb)
        allow[max(0, y0-pad):y1+pad, max(0, x0-pad):x1+pad] = True
    for x0, y0, x1, y1 in getattr(mod, 'ALLOW', []):   # 单独处理的标签（见各 map 模块）
        allow[y0:y1, x0:x1] = True
    bleed = d & ~allow
    n = int(bleed.sum())
    print(f'{os.path.basename(out)}: 改动 {int(d.sum())} 像素，其中溢出框外 {n}')
    if n:
        ys, xs = np.nonzero(bleed)
        # 溢出的像素砸到了哪些「没被替换的」原始框
        hit = {}
        for i, q in enumerate(boxes):
            if M.get(i): continue
            m = bleed[q[1]:q[3], q[0]:q[2]].sum()
            if m: hit[i] = int(m)
        print(f'   溢出范围 y {ys.min()}..{ys.max()}  x {xs.min()}..{xs.max()}')
        if hit:
            print('   砸到的未替换框:', sorted(hit.items(), key=lambda kv: -kv[1])[:10])
        else:
            print('   （没砸到其它检测框，但仍在框外 —— 游戏的 UV 可能比检测框小）')
    return n


if __name__ == '__main__':
    tot = 0
    for src, mm, out in [('global_Texture_grSystemString.png', 'map_string', 'string_zh.png'),
                         ('global_Texture_grSystemWorld.png', 'map_world', 'world_zh.png'),
                         ('global_Texture_grSystemResult.png', 'map_result', 'result_zh.png'),
                         ('global_Texture_grSystemDungeon.png', 'map_dungeon', 'dungeon_zh.png'),
                         ('global_Texture_grSystemBattle.png', 'map_battle', 'battle_zh.png')]:
        tot += check(src, mm, out)
    print('合计溢出像素', tot)
