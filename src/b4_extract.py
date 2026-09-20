# -*- coding: utf-8 -*-
"""把 database.cl3 里的定长内嵌名称字段全部导出。

B4（物品名/技能名/怪物名/迷宫名/地图地名/素材名/角色名）不是 GBNL 的类型 5
字符串列，而是行记录里的定长 ASCII 字段，所以只读字符串列的流程会整批漏掉。
字段位置是从列描述表推出来的：类型 1 且到下一列的间距 >= 16 字节。
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bra as B
from cl3 import CL3
from gbnl import GBNL

FIELDS = [                      # (表, 行内偏移, 宽度, 说明)
    ('stCharaPlayer',   0x0c, 64, '角色名'),
    ('stCharaMonster',  0x0c, 64, '怪物名'),
    ('stDungeon',       0x08, 32, '迷宫名'),
    ('stItem',          0x0c, 64, '物品名'),
    ('stMaterial',      0x04, 32, '素材/效果名'),
    ('stSkill',         0x08, 64, '技能名'),
    ('stMapPoint',      0x04, 64, '地图地名'),
]


def load(brapath):
    d = open(brapath, 'rb').read()
    _, ents = B.read_index(d)
    raw, _ = B.get(d, {e['name']: e for e in ents}['database_en\\database.cl3'])
    c3 = CL3(data=raw)
    idx = {nm.replace('.gbin', ''): i for i, (nm, _, _) in enumerate(c3.files)}
    out = {}
    for tab, off, w, label in FIELDS:
        b = c3.get(idx[tab]); g = GBNL(data=b)
        # 用列描述表复核一次，别靠写死的偏移
        cols = g.cols
        ok = False
        for i, (t, o) in enumerate(cols):
            nxt = cols[i+1][1] if i+1 < len(cols) else g.rowsize
            if t == 1 and o == off and nxt-o == w: ok = True
        assert ok, f'{tab} 的 +{off:#x}/{w} 字节字段对不上列描述表'
        rows = {}
        for r in range(g.nrows):
            s = b[r*g.rowsize+off: r*g.rowsize+off+w].split(b'\x00')[0]
            try: s = s.decode('utf-8')
            except UnicodeDecodeError: s = s.decode('cp932', 'replace')
            if s.strip() and s != '-': rows[r] = s
        out[tab] = {'off': off, 'w': w, 'label': label, 'rows': rows}
    return out


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Omega Quintet/System.bra'
    data = load(src)
    json.dump(data, open(os.path.join(HERE, 'db', 'b4_src.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    import b4_gloss
    g = b4_gloss.build()
    tot = cov = 0
    for tab, v in data.items():
        u = sorted(set(v['rows'].values()))
        c = sum(1 for x in u if x in g)
        tot += len(u); cov += c
        print(f"{tab:16s} {v['label']:10s} 宽{v['w']:3d}  行 {len(v['rows']):5d}  去重 {len(u):5d}  "
              f"已有译法 {c:4d} ({c*100//max(len(u),1)}%)")
    print(f'\n合计去重 {tot} 条，其中 {cov} 条能直接沿用说明文里的既成译法')
