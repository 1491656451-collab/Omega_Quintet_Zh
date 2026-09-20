# -*- coding: utf-8 -*-
"""grSystemResult.dds 汉化：两遍。
   第一遍 build_tex（map_result 里的普通标签）
   第二遍 build_result_tb（Total Bonus / Next：要做 13 度斜体，通用渲染器做不了）
   必须从原图重建，否则第二遍会叠在自己上一次的产物上。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_tex import build
import build_result_tb

SRC = os.path.join(HERE, 'global_Texture_grSystemResult.png')
OUT = os.path.join(HERE, 'result_zh.png')

if __name__ == '__main__':
    build(SRC, 'map_result', OUT)
    build_result_tb.SRC = OUT
    build_result_tb.main(out_path=OUT, preview=os.path.join(HERE, '_tb_preview.png'))
