# -*- coding: utf-8 -*-
"""grSystemBattle.dds 第二遍：压在底板/光条上、或者和美术底图纠缠的标签。
   通用机器在 platefix.py，这里只给逐条的矩形和译文。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import platefix

SRC = os.path.join(HERE, 'global_Texture_grSystemBattle.png')

JOBS = [
    # ---- 指令条 / 按钮：白字压在光条上，底板用可分离剖面重建 ----
    dict(tag='72 Character Switch', zh='切换角色', mode='prof',
         erase=(54, 383, 210, 410), draw=(68, 384, 202, 409),
         vcols=(28, 52), hrows=[(383, 385), (408, 411)],
         mask=dict(mode='lum', thr=150, grow=2)),
    dict(tag='84 Command Switch', zh='切换指令', mode='prof',
         erase=(56, 429, 224, 456), draw=(70, 430, 216, 455),
         vcols=(28, 52), hrows=[(429, 431), (454, 457)],
         mask=dict(mode='lum', thr=150, grow=2)),
    dict(tag='145 Action(按钮)', zh='行动', mode='prof',
         erase=(684, 714, 772, 747), draw=(686, 716, 768, 746),
         vcols=(800, 880), hrows=[(714, 717), (743, 747)],
         mask=dict(mode='lum', thr=150, grow=2)),

    # ---- 金字压在底板上 ----
    # Request / Magnetic Field / DMG Modifier 都是金黄字压在蓝底上：
    # 金色掩膜挑得很干净，所以只补笔画缺口，底板上的装饰线原样留着
    dict(tag='19 Request', zh='委托', mode='rows',
         erase=(474, 103, 582, 144), draw=(479, 107, 577, 140),
         mask=dict(mode='gold', thr=130, grow=4)),

    # ---- 回合条上的 Turn ----
    dict(tag='118 Turn', zh='回合', mode='rows',
         erase=(1303, 578, 1382, 612), draw=(1309, 581, 1377, 609),
         mask=dict(mode='lum', thr=175, grow=4)),

    # ---- DMG Modifier：黄绿字压在青色箭头带上 ----
    dict(tag='42 DMG Modifier', zh='伤害修正', mode='rows',
         erase=(792, 324, 994, 366), draw=(798, 328, 990, 362),
         mask=dict(mode='gold', thr=140, grow=4)),

    # ---- Turn Back!! / Wait Damage!! 保持英文 ----
    # 用户看过中文版后的决定：这两条是美术字横幅（红/蓝箭头带 + 斜体描边），
    # 换成汉字不好看，保留原文。
    # 查到的实据留在这里备用：JP 是「ターンバック」，官方英文帮助（stHelp 46）
    # 把同一个机制写成 "Turn Delay"，我们的数据库译文是「行动延迟」；
    # 出现场景 = 用塔克特的「追击」把敌人的行动顺序往后推。
    # 真要做的话矩形是：
    #   Turn Back!!   erase=(914,702,1114,750) draw=(918,705,1110,747) lum150/grow4 size30
    #   Wait Damage!! erase=(1123,702,1369,750) draw=(1127,705,1365,747) lum170/grow4 size30

    # ---- 透明底：直接清零 ----
    dict(tag='118 Target', zh='目标', mode='clear',
         erase=(748, 590, 858, 634), draw=(750, 592, 856, 632)),
    dict(tag='118 Support Type Change', zh='支援类型变更', mode='clear',
         erase=(868, 562, 1062, 592), draw=(870, 564, 1060, 590)),
    dict(tag='118 Current Support', zh='当前支援', mode='clear',
         erase=(893, 592, 1057, 622), draw=(895, 594, 1055, 620)),
    # 这条 Harmonics 标题 detect3 没切出框来（和旁边的图元连在一起被 max_h 滤掉了）
    dict(tag='Harmonics 标题', zh='和声', mode='clear',
         erase=(996, 874, 1196, 926), draw=(999, 877, 1193, 923)),
    dict(tag='172 Pursuit', zh='追击', mode='clear',
         erase=(1748, 855, 1876, 892), draw=(1751, 857, 1873, 890)),
    dict(tag='183 Group Defense', zh='全体防御', mode='clear',
         erase=(1693, 944, 1916, 994), draw=(1696, 946, 1914, 992)),
    dict(tag='180 Display Switch', zh='切换显示', mode='clear',
         erase=(1001, 922, 1130, 956), draw=(1003, 924, 1128, 954)),
    dict(tag='193 Pair Change', zh='更换搭档', mode='clear',
         erase=(569, 1044, 734, 1081), draw=(571, 1046, 732, 1079)),
    dict(tag='200 Change Outfit', zh='更换服装', mode='clear',
         erase=(569, 1094, 734, 1132), draw=(571, 1096, 732, 1130)),
    dict(tag='205 Info', zh='情报', mode='clear',
         erase=(699, 1142, 773, 1187), draw=(701, 1144, 771, 1185)),
    dict(tag='215/216 Switch Char.', zh='切换角色', mode='clear',
         erase=(566, 1194, 793, 1237), draw=(568, 1196, 791, 1235)),
]




def main(src=SRC, base=None, out_path=None, preview=None):
    return platefix.run(src, JOBS, base, out_path, preview)


if __name__ == '__main__':
    main(base=os.path.join(HERE, 'battle_zh.png'),
         out_path=os.path.join(HERE, 'battle_zh.png'),
         preview=os.path.join(HERE, '_bat2_preview.png'))
