#!/usr/bin/env python3
"""从成品 System.bra 里把东西解出来逐条核对：
   菜单 / 系统文本 / 说明文 / 名称 / 六张贴图（BC3 解回 RGBA 再和源 PNG 比）。"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tex'))
sys.path.insert(0, os.path.join(HERE, 'db'))
import numpy as np
import bra as B, gstr, tr_menu, tr_gstr
from cl3 import CL3
from gbnl import GBNL

TEX = {'global\\Texture\\grSystemMenuMain.dds': 'menu_zh.png',
       'global\\Texture\\grSystemString.dds':   'string_zh.png',
       'global\\Texture\\grSystemWorld.dds':    'world_zh.png',
       'global\\Texture\\grSystemResult.dds':   'result_zh.png',
       'global\\Texture\\grSystemDungeon.dds':  'dungeon_zh.png',
       'global\\Texture\\grSystemBattle.dds':   'battle_zh.png'}


def main(path):
    d = open(path, 'rb').read()
    _, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    bad = 0

    # 1) 菜单
    raw, _ = B.get(d, byname['database_en\\strMenu.gstr'])
    g = gstr.GStr(data=raw)
    miss = [i for i, k, v in g.ents if i in tr_menu.ZH and v != tr_menu.ZH[i]]
    print(f'菜单   {len(tr_menu.ZH)} 条，对不上 {len(miss)}'); bad += len(miss)

    # 2) 系统文本
    n = 0
    for fn, table in (('strSystem', tr_gstr.SYSTEM), ('strRpg', tr_gstr.RPG), ('strEvent', tr_gstr.EVENT)):
        raw, _ = B.get(d, byname[f'database_en\\{fn}.gstr'])
        g = gstr.GStr(data=raw)
        m = [i for i, k, v in g.ents if i in table and v != table[i]]
        n += len(m)
    print(f'系统   699 条 x3 套，对不上 {n}'); bad += n

    # 3) 说明文 + 4) 名称
    import db_backfill as DBF, b4_backfill as B4
    srcmap = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    zh = DBF.load_and_check(os.environ.get('OQ_DBZH', '/mnt/user-data/uploads/欧米伽五重奏'), srcmap)
    b4src = json.load(open(os.path.join(HERE, 'db', 'b4_src.json'), encoding='utf-8'))
    rowpat = B4.rowpatches(b4src, verbose=False)
    raw, _ = B.get(d, byname[DBF.TARGET])
    c3 = CL3(data=raw)
    idx = {nm.replace('.gbin', ''): i for i, (nm, _, _) in enumerate(c3.files)}
    m1 = 0
    for t in srcmap:
        blob = c3.get(idx[t]); g = GBNL(data=blob)
        import struct as _st
        for k in srcmap[t]:
            want = zh[(t, k)]
            r, o = map(int, k.split(':'))
            rel = _st.unpack_from('<I', blob, r * g.rowsize + o)[0]
            got = g.rawstr(rel)
            got = got.decode('utf-8', 'replace') if got is not None else None
            if got != want:
                m1 += 1
    print(f'说明文  {sum(len(v) for v in srcmap.values())} 条，对不上 {m1}'); bad += m1
    m2 = 0
    for t, pat in rowpat.items():
        blob = c3.get(idx[t]); g = GBNL(data=blob)
        for (r, o, w), want in pat.items():
            got = blob[r * g.rowsize + o: r * g.rowsize + o + w].split(b'\0')[0].decode('utf-8', 'replace')
            if got != want:
                m2 += 1
    print(f'名称   {sum(len(v) for v in rowpat.values())} 条，对不上 {m2}'); bad += m2

    # 5) 贴图：从包里解出 DDS，确认是 BC3(dxgiFormat=77)，解码后和源 PNG 逐像素比
    import struct
    from texture2ddecoder import decode_bc3
    from PIL import Image
    for key, png in TEX.items():
        raw, _ = B.get(d, byname[key])
        assert raw[:4] == b'DDS '
        fmt = struct.unpack_from('<I', raw, 128)[0]
        h, w = struct.unpack_from('<II', raw, 12)
        dec = decode_bc3(raw[148:148 + (w // 4) * (h // 4) * 16], w, h)
        a = np.frombuffer(dec, np.uint8).reshape(h, w, 4)[:, :, [2, 1, 0, 3]]
        src = np.array(Image.open(os.path.join(HERE, 'tex', png)).convert('RGBA'))
        # BC3 是有损的，只比「有没有明显差异」的比例
        d2 = np.abs(a.astype(int) - src.astype(int)).sum(axis=2)
        r = (d2 > 90).mean()
        flag = 'OK' if (fmt == 77 and r < 0.02) else '!!'
        print(f'贴图 {os.path.basename(key):26s} {w}x{h} fmt={fmt} 明显差异像素 {r*100:.2f}%  {flag}')
        if flag == '!!':
            bad += 1
    print('\n>>> 回读比对' + ('通过' if bad == 0 else f'失败：{bad} 处'))
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else 'out/System_r15.bra') else 0)
