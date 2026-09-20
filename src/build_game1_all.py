#!/usr/bin/env python3
"""Game1.bra 合并补丁（OQPATCH2，按成员名寻址）：
   标题画面 3 项（Game1 里只有 Newgame/Continue/Config）+ 31 张迷宫名横幅 + 地图图例。
   和 Game4_all_zh.oqpatch 配套，装一次就齐。"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tex'))
import bra as B
from cl3 import CL3
from ddsenc import encode_bc3
from build_bra_patch import build

G1 = '/mnt/user-data/uploads/Omega Quintet/Game1.bra'
TITLE = ['Newgame', 'Continue', 'Config']


def swap_dds(raw, png):
    hh, ww = struct.unpack_from('<II', raw, 12)
    ddslen = 148 + (ww // 4) * (hh // 4) * 16
    out = encode_bc3(png, raw[:148]) + raw[ddslen:]
    assert len(out) == len(raw), (len(out), len(raw))
    return out


def main():
    d = open(G1, 'rb').read()
    _, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    recs = []
    for n in TITLE:
        key = f'Part\\TITLE\\parts\\menu_{n}.CL3'
        blob, _ = B.get(d, byname[key])
        c = CL3(data=blob)
        idx = [k for k, (nm, _, _) in enumerate(c.files)
               if nm.endswith('.tid') and 'Back' not in nm]
        assert len(idx) == 1, (n, [f[0] for f in c.files])
        nm, off, sz = c.files[idx[0]]
        old = blob[off:off + sz]
        assert old[:4] == b'DDS '
        hh, ww = struct.unpack_from('<II', old, 12)
        ddslen = 148 + (ww // 4) * (hh // 4) * 16
        new = encode_bc3(os.path.join(HERE, 'tex', 'title_zh', f'menu_{n}.png'), old[:148])
        assert len(new) == ddslen
        out = bytearray(blob)
        out[off:off + sz] = new + old[ddslen:]
        assert len(out) == len(blob)
        recs.append((key, bytes(out)))
    for f in sorted(os.listdir(os.path.join(HERE, 'tex', 'mapname_zh'))):
        if not f.endswith('.png') or f.startswith('_'):
            continue
        key = f'Part\\DUNGEON\\Texture\\MapName\\{f[:-4]}.dds'
        raw, _ = B.get(d, byname[key])
        recs.append((key, swap_dds(raw, os.path.join(HERE, 'tex', 'mapname_zh', f))))
    key = 'Part\\DUNGEON\\Texture\\MapHelp.dds'
    raw, _ = B.get(d, byname[key])
    recs.append((key, swap_dds(raw, os.path.join(HERE, 'tex', 'MapHelp_zh.png'))))
    build(recs, os.path.join(HERE, 'dist', 'data', 'Game1_all_zh.oqpatch'), 'Game1.bra')


if __name__ == '__main__':
    main()
