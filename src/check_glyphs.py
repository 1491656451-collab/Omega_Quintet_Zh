# -*- coding: utf-8 -*-
"""字形覆盖：把四层译文用到的每个字符，拿去打过补丁的字体里查一遍。
查不到的字在游戏里会变成空白/豆腐块，所以这一项必须是 0。
直接从成品 System.bra 里取字体，查的就是玩家实际会用的那两个 ffu。
"""
import sys, os, json, glob, importlib.util, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'db'))
import bra as B, ffu, tr_menu, tr_gstr, tr_speakers, tr_event_pilot, fix_zh


def all_text():
    T = {}
    T['菜单'] = list(tr_menu.ZH.values())
    T['系统'] = [v for tab in (tr_gstr.SYSTEM, tr_gstr.RPG, tr_gstr.EVENT) for v in tab.values()]
    src = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    zh0 = json.load(open(os.path.join(HERE, 'db', 'db_zh.json'), encoding='utf-8'))
    enm = {f'{t}|{k}': v for t, d in src.items() for k, v in d.items()}
    zh, _ = fix_zh.apply(zh0, enm)
    T['数据库'] = list(zh.values())
    ev = dict(tr_event_pilot.T)
    for p in sorted(glob.glob(os.path.join(HERE, 'work/batch_*_zh.py'))):
        spec = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for fn, r in m.T.items(): ev.setdefault(fn, r)
    T['剧情'] = [v for r in ev.values() for v in r.values()] + list(tr_speakers.SPEAKERS.values())
    import tr_b4
    b4 = json.load(open(os.path.join(HERE, 'db', 'b4_src.json'), encoding='utf-8'))
    names = []
    for tab, v in b4.items():
        table = tr_b4.TABLES.get(tab, {})
        for en in set(v['rows'].values()):
            z = tr_b4.resolve(en, table)
            if z: names.append(z)
    T['名称'] = names
    return T


def main(brapath):
    d = open(brapath, 'rb').read()
    _, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    tmp = tempfile.mkdtemp()
    fonts = {}
    for name in ('sysfont.ffu', 'advfont.ffu'):
        raw, _ = B.get(d, byname[f'window\\font\\{name}'])
        p = os.path.join(tmp, name); open(p, 'wb').write(raw)
        fonts[name] = ffu.FFU(p).chars()
        print(f'{name}: {len(fonts[name])} 个字形')

    T = all_text()
    bad = 0
    for layer, texts in T.items():
        cs = set()
        for t in texts:
            cs |= set(t or '')
        cs -= set('\n\r\t')
        # 菜单/系统/数据库走 sysfont，剧情走 advfont；两个都补过，两个都查
        miss = {f: sorted(c for c in cs if c not in ch) for f, ch in fonts.items()}
        n = sum(len(v) for v in miss.values())
        bad += n
        print(f'{layer:6s} 用到 {len(cs):5d} 个不同字符，'
              + ' / '.join(f'{f} 缺 {len(v)}' for f, v in miss.items()))
        for f, v in miss.items():
            if v: print('    缺:', ''.join(v[:80]))
    print()
    print('>>> 字形覆盖通过，零缺字' if not bad else f'>>> 缺字 {bad} 个')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else 'out/System_r10.bra') else 0)
