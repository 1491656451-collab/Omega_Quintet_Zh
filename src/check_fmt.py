#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""格式符闸：中译文的 printf 转换符「种类与顺序」必须和英文原文完全一致。

为什么要有这一道：游戏用 sprintf 拼很多 UI 串。占位符**个数**对得上但**顺序**变了，
编译期没人管，运行时 `%s` 会拿到一个整数 -> strlen(小整数) -> 0xC0000005。
第 24 轮就是这么崩的（菜单 1083 委托「击破」）。

用法:  python3 check_fmt.py        # 全层扫描，返回码非 0 表示有问题
"""
import json, re, sys, os, glob, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# 不要带「空格标志」，否则英文 "25% of HP" 会被当成 "% o"
SPEC = re.compile(r'%[-+0#]*[0-9]*(?:\.[0-9]+)?(?:hh|h|ll|l|I64)?([sdiuxXfFgGeEcp%])')
kinds = lambda s: [m.group(1) for m in SPEC.finditer(s)]
specs = lambda s: [m.group(0) for m in SPEC.finditer(s)]

bad, total = [], 0

def check(layer, triples):
    global total
    n = 0
    for key, en, zh in triples:
        if not isinstance(en, str) or not isinstance(zh, str):
            continue
        n += 1
        if kinds(en) != kinds(zh):
            bad.append((layer, key, en, zh, specs(en), specs(zh)))
    total += n
    print('%-22s 比对 %6d 条' % (layer, n))

def load(p):
    spec = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

# 1) strMenu 410
tm = load(os.path.join(HERE, 'tr_menu.py'))
EN = {int(r[0]): r[2] for r in json.load(open(os.path.join(HERE, 'menu_en.json'), encoding='utf-8'))}
check('strMenu', [(k, EN.get(int(k)), v) for k, v in tm.ZH.items() if v is not None])

# 2) strSystem / strRpg / strEvent 699
tg = load(os.path.join(HERE, 'tr_gstr.py'))
g = json.load(open(os.path.join(HERE, 'gstr_en.json'), encoding='utf-8'))
for name, table in (('strSystem', tg.SYSTEM), ('strRpg', tg.RPG), ('strEvent', tg.EVENT)):
    check(name, [('%s[%s]' % (name, k), g[name].get(str(k)), v)
                 for k, v in table.items() if v is not None])

# 3) database 说明文 8396
src = json.load(open(os.path.join(HERE, 'db/db_src.json'), encoding='utf-8'))
flat = {'%s|%s' % (t, k): v for t, rows in src.items() for k, v in rows.items()}
zh = json.load(open(os.path.join(HERE, 'db/db_zh_fixed.json'), encoding='utf-8'))
check('database 说明文', [(k, flat.get(k), v) for k, v in zh.items()])

# 4) B4 名称 1869
b4 = json.load(open(os.path.join(HERE, 'db/_b4_en2zh.json'), encoding='utf-8'))
check('B4 名称', [(t + '|' + e, e, z) for t, m in b4.items() for e, z in m.items()])

# 5) 剧情 11039
ev = json.load(open(os.path.join(HERE, 'event_text_en.json'), encoding='utf-8'))
T = dict(load(os.path.join(HERE, 'tr_event_pilot.py')).T)
for p in sorted(glob.glob(os.path.join(HERE, 'work/batch_*_zh.py'))):
    for fn, rows in load(p).T.items():
        T.setdefault(fn, rows)
triples = []
for fn, rows in T.items():
    er = ev.get(fn + '.gbin')
    if er is None: continue
    ed = {(r[0], r[1]): r[2] for r in er}
    for idx, z in rows.items():
        triples.append(('%s[%s]' % (fn, idx), ed.get((idx, 184)), z))
check('剧情 event', triples)

# 6) DLC
td = load(os.path.join(HERE, 'tr_dlc.py'))
for nm in ('NAMES', 'STRS'):
    d = getattr(td, nm, None)
    if isinstance(d, dict):
        check('DLC/' + nm, [(e, e, z) for e, z in d.items()])

print('\n共比对 %d 条 —— 不一致 %d 条' % (total, len(bad)))
for layer, key, en, zh_, a, b in bad:
    print('  !! %s %s\n     EN %r\n        %s\n     ZH %r\n        %s' % (layer, key, en[:100], a, zh_[:100], b))
sys.exit(1 if bad else 0)
