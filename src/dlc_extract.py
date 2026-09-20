# -*- coding: utf-8 -*-
"""把 DLC.bra 里那套数据库分表的英文全导出来。

DLC.bra 的 `database_en\\` 下是**独立的 .gbin 成员**（不像主包那样打在 cl3 里），
表名带编号：stItem003 / stCharaMonster030 / stSkill032 …… 一个 DLC 一组。
结构和主表完全一样，所以名称字段的偏移可以直接沿用 b4_extract 那份，
但**还是从列描述表复核一次**，对不上就跳过并报出来。

导出两类：
  names —— 行记录里的定长内嵌字段（物品名/怪物名/技能名/迷宫名/地图地名）
  strs  —— 类型 5 字符串列（说明文）
"""
import json, os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bra as B
from gbnl import GBNL

SRC = '/mnt/user-data/uploads/Omega Quintet/DLC.bra'

# 表名前缀 -> (名称字段偏移, 宽度)，沿用主表
NAMEFIELD = {
    'stItem':         (0x0c, 64),
    'stSkill':        (0x08, 64),
    'stCharaMonster': (0x0c, 64),
    'stMapPoint':     (0x04, 64),
    'stDungeon':      (0x08, 32),
    'stCharaPlayer':  (0x0c, 64),
    'stMaterial':     (0x04, 32),
}


def base(name):
    return re.sub(r'\d+$', '', name)


def dec(b):
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return b.decode('cp932', 'replace')


def load(src=SRC):
    d = open(src, 'rb').read()
    _, ents = B.read_index(d)
    out = {}
    for e in ents:
        if not e['name'].startswith('database_en\\'):
            continue
        tab = e['name'].split('\\')[1].replace('.gbin', '')
        raw, _ = B.get(d, e)
        g = GBNL(data=raw)
        rec = {'rowsize': g.rowsize, 'nrows': g.nrows, 'names': {}, 'strs': {}}
        # 1) 定长内嵌名称字段
        bt = base(tab)
        if bt in NAMEFIELD:
            off, w = NAMEFIELD[bt]
            ok = False
            for i, (t, o) in enumerate(g.cols):
                nxt = g.cols[i + 1][1] if i + 1 < len(g.cols) else g.rowsize
                if t == 1 and o == off and nxt - o == w:
                    ok = True
            rec['field'] = [off, w, ok]
            if ok:
                for r in range(g.nrows):
                    s = raw[r * g.rowsize + off: r * g.rowsize + off + w].split(b'\x00')[0]
                    s = dec(s)
                    if s.strip() and s != '-':
                        rec['names'][f'{r}:{off}'] = s
        # 2) 类型 5 字符串列
        for r, o, rel, b in g.cells():
            if not b:
                continue
            s = dec(b)
            if s.strip() and s != '-':
                rec['strs'][f'{r}:{o}'] = s
        out[tab] = rec
    return out


if __name__ == '__main__':
    data = load()
    tn = ts = 0
    for tab in sorted(data):
        v = data[tab]
        tn += len(v['names']); ts += len(v['strs'])
        if v['names'] or v['strs']:
            print(f"{tab:22s} 行 {v['nrows']:3d}  名称 {len(v['names']):3d}  字符串 {len(v['strs']):3d}"
                  + ('' if v.get('field', [0, 0, True])[2] else '   !! 名称字段对不上列表'))
    print(f'\n合计 名称 {tn} 条 / 字符串 {ts} 条')
    json.dump(data, open(os.path.join(HERE, 'db', 'dlc_src.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('-> db/dlc_src.json')
