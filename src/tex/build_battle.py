# -*- coding: utf-8 -*-
"""grSystemBattle.dds 汉化：两遍。
   第一遍 build_tex（透明底、检测框干净的 39 个标签）
   第二遍 build_battle2（压在底板上的 22 条，逐条给矩形）
   必须按顺序跑，而且第一遍要从原图重建 —— 否则第二遍会叠在自己上一次的产物上。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_tex import build
import build_battle2

SRC = os.path.join(HERE, 'global_Texture_grSystemBattle.png')
OUT = os.path.join(HERE, 'battle_zh.png')

if __name__ == '__main__':
    # 左边两列是指令表、中间是面板、右边是弹出字，互不相干：分区之后
    # 每一区各算各的字号，不会被别区最矮的那个框压小
    build(SRC, 'map_battle', OUT, x_split=[190, 420, 1000, 1440])
    build_battle2.main(src=SRC, base=OUT, out_path=OUT,
                       preview=os.path.join(HERE, '_bat2_preview.png'))
