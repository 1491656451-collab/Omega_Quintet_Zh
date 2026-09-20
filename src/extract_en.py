#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从你自己的游戏文件里抽出英文原文，生成构建所需的四个 json。

本仓库**不包含游戏的英文文本** —— 那是游戏本体的内容。
构建汉化包之前先跑一次这个脚本，它会从你自己那份游戏里把英文抽出来。

用法:
    python3 extract_en.py "<游戏目录>"
例:
    python3 extract_en.py "D:/SteamLibrary/steamapps/common/Omega Quintet"

产物（都在本仓库根目录）:
    menu_en.json        strMenu 410 条      [[id, key, text], ...]
    gstr_en.json        strSystem / strRpg / strEvent   {表名: {id: text}}
    event_text_en.json  剧情 274 个事件     {"0001.gbin": [[行, 列偏移, text], ...]}
    db/db_src.json      数据库说明文 23 张表 {表名: {"行:列": text}}

说明文那 23 张表和各自的列偏移记在 db_tables.json 里（只是表结构，不含游戏文本）。
"""
import sys, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bra as B
from gbnl import GBNL
from cl3 import CL3
import gstr

EVENT_COLS = (0xA8, 0xB8)          # 说话人 / 正文


def members(path):
    d = open(path, 'rb').read()
    ver, ents = B.read_index(d)
    return d, {e['name']: e for e in ents}


def main(gamedir):
    sysbra = os.path.join(gamedir, 'System.bra')
    evtbra = os.path.join(gamedir, 'Event.bra')
    for p in (sysbra, evtbra):
        if not os.path.exists(p):
            sys.exit('找不到 %s —— 第一个参数要填游戏目录（里面有 System.bra 和 OmegaQuintet.exe）' % p)

    d, by = members(sysbra)

    # 1) strMenu
    raw, _ = B.get(d, by['database_en\\strMenu.gstr'])
    menu = [[i, k, v] for i, k, v in gstr.GStr(data=raw).ents]
    json.dump(menu, open(os.path.join(HERE, 'menu_en.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('menu_en.json        %d 条' % len(menu))

    # 2) strSystem / strRpg / strEvent
    g = {}
    for name in ('strSystem', 'strRpg', 'strEvent'):
        raw, _ = B.get(d, by['database_en\\%s.gstr' % name])
        g[name] = {str(i): v for i, k, v in gstr.GStr(data=raw).ents}
    json.dump(g, open(os.path.join(HERE, 'gstr_en.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('gstr_en.json        %s' % {k: len(v) for k, v in g.items()})

    # 3) database.cl3 说明文
    man = json.load(open(os.path.join(HERE, 'db_tables.json'), encoding='utf-8'))
    raw, _ = B.get(d, by['database_en\\database.cl3'])
    c = CL3(data=raw)
    idx = {nm.replace('.gbin', ''): i for i, (nm, _, _) in enumerate(c.files)}
    out = {}
    for t, cols in man.items():
        gb = GBNL(data=c.get(idx[t]))
        rows = {}
        want = set(cols)
        for i, o, rel, b in gb.cells():
            if o not in want or b is None:
                continue
            s, enc = gb.dec(b)
            # 空格子、占位行（'-' / '0' / '???' / '......'）都不是要翻译的文本，
            # 判据：一个拉丁字母都没有的串一律跳过
            if not re.search(r'[A-Za-z]', s):
                continue
            rows['%d:%d' % (i, o)] = s
        out[t] = rows
    os.makedirs(os.path.join(HERE, 'db'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'db', 'db_src.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('db/db_src.json      %d 张表 / %d 条' % (len(out), sum(len(v) for v in out.values())))

    # 4) 剧情
    d2, by2 = members(evtbra)
    ev = {}
    for name, e in by2.items():
        if not name.startswith('SCRIPT\\DATA\\') or not name.endswith('.gbin'):
            continue
        gb = GBNL(data=B.get(d2, e)[0])
        rows = []
        for i, o, rel, b in gb.cells():
            if o not in EVENT_COLS or b is None:
                continue
            s, enc = gb.dec(b)
            rows.append([i, o, s])
        if rows:
            ev[name.split('\\')[-1]] = rows
    json.dump(ev, open(os.path.join(HERE, 'event_text_en.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('event_text_en.json  %d 个事件 / %d 条' % (len(ev), sum(len(v) for v in ev.values())))
    print('\n抽取完成。接下来可以跑 check_fmt.py 或 build_system.py 了。')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
