# -*- coding: utf-8 -*-
"""C2 第二遍：按「同一个 UI 框」的粒度比宽度。

逐条比（译文 vs 它自己的英文）会误报：短标签(Save→进行保存)所在的框是按
整组里最长的一条做的。整文件比又太松：一张表里既有长描述又有短名字。
真正有意义的粒度是「同一个框 / 同一列」：
  · 数据库 GBNL —— 表 + 列偏移，一列就是一个 UI 字段
  · strMenu     —— IDS_ 键名前三段，同一族标签画在同一处
  · gstr        —— 文件 + id//100，id 是按功能块分配的

判据：英文是游戏自带的，必然放得下 => 该组英文最宽行是框宽的下界。
中文不超过这个下界、行数不超过组内上界 => 一定不溢出。
"""
import json, os, sys, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'db'))
from check_width import measure, px, strip_ctrl


def group_sweep(name, rows, show=8, font='sys'):
    """rows: [(group, key, en, zh)]"""
    g = defaultdict(list)
    for grp, key, en, zh in rows:
        g[grp].append((key, en, zh))
    bad = []
    for grp, items in sorted(g.items()):
        items = [(k, e or '', z or '') for k, e, z in items]
        wmax = max((measure(e, font)[1] for _, e, _ in items if e.strip()), default=0)
        lmax = max((measure(e, font)[0] for _, e, _ in items if e.strip()), default=0)
        if not wmax:
            continue
        over = []
        for key, en, zh in items:
            if not zh.strip():
                continue
            lz, wz = measure(zh, font)
            if wz > wmax or lz > lmax:
                over.append((key, wz, wmax, lz, lmax, en, zh))
        if over:
            bad.append((grp, len(items), wmax, lmax, over))
    tot = sum(len(o[4]) for o in bad)
    print(f'=== {name}：{len(g)} 组，{len(rows)} 条，有风险 {tot} 条')
    for grp, n, wmax, lmax, over in bad:
        print(f'  {grp:26s} ({n:4d} 条) 框宽下界 {wmax}px / 行数上界 {lmax}  超出 {len(over)} 条')
        for key, wz, wm, lz, lm, en, zh in over[:show]:
            print(f'     {str(key):16s} 宽 {wz}/{wm}  行 {lz}/{lm}')
            print(f'        原 {en[:64]!r}')
            print(f'        译 {zh[:64]!r}')
    return tot


def main():
    import tr_menu, tr_gstr, fix_zh
    total = 0

    # —— strMenu：IDS_ 键名前三段 ——
    men = json.load(open(os.path.join(HERE, 'menu_en.json'), encoding='utf-8'))
    key_of = {e[0]: e[1] for e in men}
    en_of = {e[0]: e[2] for e in men}
    rows = []
    for i, en in en_of.items():
        zh = tr_menu.ZH.get(i, '')
        k = key_of[i]
        grp = '_'.join(k.split('_')[:3])
        rows.append((grp, i, en, zh))
    total += group_sweep('菜单 strMenu', rows)

    # —— gstr：文件 + id//100 ——
    gen = json.load(open(os.path.join(HERE, 'gstr_en.json'), encoding='utf-8'))
    rows = []
    for fn, tab in (('strSystem', tr_gstr.SYSTEM), ('strRpg', tr_gstr.RPG), ('strEvent', tr_gstr.EVENT)):
        for sid, en in gen[fn].items():
            zh = tab.get(int(sid), '')
            rows.append((f'{fn}+{int(sid)//100*100}', f'{fn}:{sid}', en, zh))
    total += group_sweep('系统 gstr', rows)

    # —— 数据库：表 + 列偏移 ——
    src = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    zh0 = json.load(open(os.path.join(HERE, 'db', 'db_zh.json'), encoding='utf-8'))
    enm = {f'{t}|{k}': v for t, d in src.items() for k, v in d.items()}
    zh, _ = fix_zh.apply(zh0, enm)
    rows = []
    for k, en in enm.items():
        tab, rc = k.split('|'); row, col = rc.split(':')
        rows.append((f'{tab}+0x{int(col):x}', k, en, zh.get(k, '')))
    total += group_sweep('数据库 cl3', rows)

    # —— 剧情 Event：正文一个对话框、说话人一个名牌，各算一组，用 advfont ——
    # 0001 是开场字幕（整屏滚动，不是对话框，英文单行宽到 2363px），单独成组；
    # 3918 里残留的日文在英文版是乱码，不能拿来当框宽的证据，剔掉。
    import importlib.util, glob
    import tr_speakers, tr_event_pilot
    T = dict(tr_event_pilot.T)
    for pth in sorted(glob.glob(os.path.join(HERE, 'work/batch_*_zh.py'))):
        spec = importlib.util.spec_from_file_location(os.path.basename(pth)[:-3], pth)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for fn, r in m.T.items():
            T.setdefault(fn, r)
    ev = json.load(open(os.path.join(HERE, 'event_text_en.json'), encoding='utf-8'))
    rows = []
    for fname, cells in ev.items():
        stem = fname.split('.')[0]
        rr = T.get(stem) or {}
        for i, off, en in cells:
            en = en or ''
            if off == 0xB8:
                grp = '开场字幕 0001' if stem == '0001' else '对话框 +0xb8'
                if grp == '对话框 +0xb8' and en and not all(ord(c) < 128 for c in en):
                    en = ''                       # 乱码日文不参与框宽下界
                rows.append((grp, f'{stem}:{i}', en, rr.get(i, '')))
            elif off == 0xA8:
                rows.append(('说话人名牌 +0xa8', f'{stem}:{i}', en,
                             tr_speakers.SPEAKERS.get(en, '')))
    total += group_sweep('剧情 Event', rows, font='adv')

    print()
    print(f'>>> 全部四层，按框粒度仍有风险 {total} 条')
    return total


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
