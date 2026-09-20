# -*- coding: utf-8 -*-
"""把 B4 的 1869 条名称写回 database.cl3 的定长内嵌字段。

和说明文（类型 5 字符串列）走的是两条路：说明文改字符串池，名称改行记录本身。
所以两者可以在同一次 GBNL.rebuild 里一起写。
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import tr_b4
from b4_extract import FIELDS


def rowpatches(b4src, verbose=True):
    """{表: {(行, 偏移, 宽度): 中文}}"""
    out = {}
    n = miss = 0
    for tab, off, w, label in FIELDS:
        v = b4src[tab]
        table = tr_b4.TABLES.get(tab, {})
        pat = {}
        for r, en in v['rows'].items():
            zh = tr_b4.resolve(en, table)
            if zh is None:
                miss += 1
                if verbose and miss < 10: print('  ! 未译:', tab, en)
                continue
            pat[(int(r), off, w)] = zh
            n += 1
        out[tab] = pat
        if verbose:
            print(f'  {tab:16s} {label:10s} 写回 {len(pat):5d} 条')
    if miss:
        raise SystemExit(f'还有 {miss} 条没译，先补完再回填')
    return out


if __name__ == '__main__':
    src = json.load(open(os.path.join(HERE, 'b4_src.json'), encoding='utf-8'))
    p = rowpatches(src)
    print('合计', sum(len(v) for v in p.values()), '条')
