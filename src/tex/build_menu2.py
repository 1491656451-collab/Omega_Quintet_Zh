# -*- coding: utf-8 -*-
"""grSystemMenuMain.dds 第二遍：数据记录面板那两条压在光条上的标签。

第 8 轮做这张图时检测是从 y=830 往下扫的（下面全是菜单项），
y=630 附近这两条在光条上，既没被检测到，也不能用通用擦除器 —— 所以一直是英文。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import platefix

SRC = os.path.join(HERE, 'global_Texture_grSystemMenuMain.png')

# 【第 17 轮起停用】用户看过中文版后的决定：数据记录面板那两条保持英文。
# 中文和上面那行 EP 的美术风格对不上，太违和。
#
# 下面这份配置是查证过的，留着备用：
#   * 译名应为「支持率」不是「支援率」—— 贴图写 "Support Rate"，但游戏帮助
#     (stHelp 17) 里同一个数值的官方英文是 "Approval Rating"、日文是「支持率」，
#     数据库译文也一直是「支持率」。「支援」在这个游戏里是战斗的支援类型，撞车。
#   * 字号 20 —— 英文字身（不含 pp 的下伸部）y641..657 = 17px，
#     "Play Time" y680..697 = 18px。汉字墨高 ≈ 字号。
#     别让 fit_size 按落笔框的高度去顶（会顶出 31 号、墨高 33px，撑出光条）。
#   * 左边缘两条统一 1446（英文自己差 9px：1441 / 1450，但两条光条的 quad 左边是对齐的）。
DISABLED_JOBS = [
    dict(tag='Support Rate', zh='支持率', mode='rows',
         erase=(1434, 632, 1590, 672), draw=(1446, 638, 1580, 660),
         mask=dict(mode='lum', thr=150, grow=4), align='left', size=20),
    dict(tag='Play Time', zh='游戏时间', mode='rows',
         erase=(1444, 670, 1584, 710), draw=(1446, 678, 1580, 700),
         mask=dict(mode='lum', thr=150, grow=4), align='left', size=20),
]

JOBS = []


def main(src=SRC, base=None, out_path=None, preview=None):
    return platefix.run(src, JOBS, base, out_path, preview)


if __name__ == '__main__':
    main(base=os.path.join(HERE, 'menu_zh.png'),
         out_path=os.path.join(HERE, 'menu_zh.png'),
         preview=os.path.join(HERE, '_menu2_preview.png'))
