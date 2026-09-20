# -*- coding: utf-8 -*-
"""迷宫名横幅：640x48，一张一个名字，两端各有一个菱形装饰，中间是金色美术字。
   菱形保住，只把中间的英文换成中文，字号全 31 张统一。"""
import os, sys, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from detect3 import detect3, _runs
from autostyle import sample
from render3 import draw, ink_mask

HERE = os.path.dirname(os.path.abspath(__file__))

ZH = {
 '001': '翠绿地带',     '002': '干涸荒野',     '003': '摩天避难所',
 '004': '南米德尔顿',   '005': '北米德尔顿',   '006': '水晶洞窟',
 '007': '山手町遗迹',   '008': '湾岸工厂',     '009': '溪谷补给基地',
 '010': '中央塔',       '011': '剧场大厅',     '012': '二桥商业区',
 '013': '台场运河桥',
 '014': '训练设施 1',   '015': '训练设施 2',   '016': '训练设施 3',
 '017': '训练设施 4',   '018': '训练设施 5',   '019': '训练设施 6',
 '020': '训练设施 7',   '021': '训练设施 8',   '022': '训练设施 9',
 '023': '训练设施 10',  '024': '训练设施 11',  '025': '训练设施 12',
 '026': '训练设施 13',
 '101': '裾野镇',       '102': '三重塔',       '103': '中央广场',
 '104': '气象观测站',   '105': '南部平原',
}

STYLE = dict(top=(252, 246, 120), bot=(206, 138, 52),
             outline=(96, 74, 34), glow=None, ew=2)


def parts_of(png):
    """横幅只有一行，直接按列投影切：首尾两段是菱形，中间全是文字。"""
    a = np.array(Image.open(png).convert('RGBA'))[:, :, 3] > 128
    r = _runs(a.sum(axis=0), 5)
    if len(r) < 2:
        return None
    # 菱形宽度固定 38px：左边一个贴着 x=4，右边一个贴着整条横幅的右端。
    # 不能靠「首尾两段」来判断 —— 像 017 那样末位数字会和右菱形连成一段。
    l0, l1 = r[0][0], r[0][0] + 38
    r1 = r[-1][1]; r0 = r1 - 38
    if r0 <= l1:
        return None
    return [l0, 0, l1, a.shape[0]], [l1, 0, r0, a.shape[0]], [r0, 0, r1, a.shape[0]]


def build(outdir=os.path.join(HERE, 'mapname_zh')):
    os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HERE, 'mapname', '*.png')))
    info = []
    for f in files:
        # 文件名里带反斜杠（从 .bra 里原样导出的），basename 在 Linux 上切不掉
        key = os.path.splitext(os.path.basename(f).split('\\')[-1])[0]
        if key not in ZH: continue
        p = parts_of(f)
        if not p:
            print('  !! 切不出菱形/文字：', key); continue
        left, tb, right = p
        info.append((f, key, left, tb, right))

    # 统一字号：所有横幅取同一个，按最紧的一张定
    S = 40
    while S > 12:
        ok = True
        for f, key, left, tb, right in info:
            m = ink_mask(ZH[key], S)
            avail_w = right[0] - left[2] - 24
            if m.height + 2 * STYLE['ew'] > 44 or m.width > avail_w:
                ok = False; break
        if ok: break
        S -= 1

    for f, key, left, tb, right in info:
        im = Image.open(f).convert('RGBA')
        px = np.array(im)
        px[:, left[2] + 2:right[0] - 2] = (0, 0, 0, 0)     # 只清中间，菱形不动
        im = Image.fromarray(px, 'RGBA')
        lab = draw(ZH[key], S, STYLE, right[0] - left[2] - 20)
        cx = (left[2] + right[0]) // 2
        im.alpha_composite(lab, (cx - lab.width // 2, 24 - lab.height // 2))
        im.save(os.path.join(outdir, key + '.png'))
    print(f'迷宫名 {len(info)} 张，统一字号 {S}')
    return [k for _, k, _, _, _ in info]


if __name__ == '__main__':
    build()
