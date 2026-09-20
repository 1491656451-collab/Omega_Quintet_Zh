# -*- coding: utf-8 -*-
"""地名跨层一致性：迷宫名横幅贴图已交付，全线以贴图为准。

专名可能被断行切开（翠绿\n绿化带），所以匹配时字与字之间容许一个换行。
"""
import json, os, re, sys, glob, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'db'))
import fix_zh, tr_event_pilot

CANON = {
 'Verdant Greenbelt': '翠绿地带', 'Arid Wilderness': '干涸荒野',
 'Skyscraper Shelter': '摩天避难所', 'Yamate': '山手町遗迹',
 'Bayside Plant': '湾岸工厂', 'Valley Supply Base': '溪谷补给基地',
 'Nibashi': '二桥商业区', 'Crystal Cave': '水晶洞窟',
 'Stargazers': '观星者之地', 'Central Tower': '中央塔',
 'Theater Hall': '剧场大厅', 'Daiba': '台场运河桥',
 'Misty Plateau': '迷雾高原', 'Weathervane': '风向标平原',
 'Leafy Pond': '绿叶池', 'Underworld Trail': '冥界小径',
 'Middleton': '米德尔顿', 'South Middleton': '南米德尔顿',
}


def layers():
    src = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    zh0 = json.load(open(os.path.join(HERE, 'db', 'db_zh.json'), encoding='utf-8'))
    enm = {f'{t}|{k}': v for t, d in src.items() for k, v in d.items()}
    zh, _ = fix_zh.apply(zh0, enm)
    yield '数据库', [(k, enm[k], zh[k]) for k in zh]

    T = dict(tr_event_pilot.T)
    for p in sorted(glob.glob(os.path.join(HERE, 'work/batch_*_zh.py'))):
        spec = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for fn, r in m.T.items(): T.setdefault(fn, r)
    ev = json.load(open(os.path.join(HERE, 'event_text_en.json'), encoding='utf-8'))
    rows = []
    for fname, cells in ev.items():
        stem = fname.split('.')[0]; rr = T.get(stem) or {}
        for i, off, e in cells:
            if off == 0xB8 and e and rr.get(i): rows.append((f'{stem}:{i}', e, rr[i]))
    yield '剧情', rows


def main():
    bad = 0
    for name, rows in layers():
        n = 0
        for en, canon in CANON.items():
            rx = re.compile(r'\n?'.join(canon))
            for k, e, z in rows:
                if en.lower() not in e.lower(): continue
                if rx.search(z): continue
                n += 1
                if n <= 5: print(f'  ✗ {name} {k} 「{en}」应作「{canon}」: {z[:50]!r}')
        print(f'{name:6s} 不合口径 {n} 条')
        bad += n
    print('\n>>> 地名口径一致' if not bad else f'\n>>> 还有 {bad} 条不合口径')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
