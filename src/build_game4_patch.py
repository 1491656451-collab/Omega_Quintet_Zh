#!/usr/bin/env python3
"""Game4.bra 原地补丁（OQPATCH2，按成员名寻址）：
   标题画面 6 项 + 31 张迷宫名横幅 + 地图图例。

为什么要打进 Game4：
  * 标题画面的 6 个 menu_*.CL3 只有 Game4 里是全的，
    而且实测游戏读的是 Game4 的那份；
  * 31 张 MapName 横幅第 5 轮只打进了 Game1，Game4 里还有一份同名同大小的，
    到底读哪份不确定 —— 两个都打就没有悬念了；
  * MapHelp 图例第 14 轮已经两个包都打了，这里一并带上，装一次就齐。

Game4.bra 有 721MB，我这边拿不到，所以：
  * 每个成员的「原始字节」拿 Game1.bra 里的同名成员（DDS 同名同大小，
    横幅/图例两个包里是同一张图），标题 CL3 拿用户导出的 oq_found/ 那 6 个文件；
  * 偏移由 Windows 侧的 apply_bra.ps1 自己读 Game4 的索引算。
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tex'))
import bra as B
from cl3 import CL3
from ddsenc import encode_bc3
from build_bra_patch import build

G1 = '/mnt/user-data/uploads/Omega Quintet/Game1.bra'
FOUND = '/mnt/user-data/uploads/欧米伽五重奏/oq_found/'
TITLE = ['Newgame', 'Continue', 'LoadGame', 'Config', 'DLCMenu', 'Quit']


def swap_dds(raw, png):
    hh, ww = struct.unpack_from('<II', raw, 12)
    ddslen = 148 + (ww // 4) * (hh // 4) * 16
    out = encode_bc3(png, raw[:148]) + raw[ddslen:]     # .dds 成员尾部 33 字节名字要接回去
    assert len(out) == len(raw), (len(out), len(raw))
    return out


def main():
    d = open(G1, 'rb').read()
    _, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    recs = []

    # 标题 6 项：CL3 里换 tid
    for n in TITLE:
        blob = open(FOUND + f'Game4.bra__Part_TITLE_parts_menu_{n}.CL3', 'rb').read()
        c = CL3(data=blob)
        idx = [k for k, (nm, _, _) in enumerate(c.files)
               if nm.endswith('.tid') and 'Back' not in nm]
        assert len(idx) == 1, (n, [f[0] for f in c.files])
        nm, off, sz = c.files[idx[0]]
        old = blob[off:off + sz]
        assert old[:4] == b'DDS '
        hh, ww = struct.unpack_from('<II', old, 12)
        ddslen = 148 + (ww // 4) * (hh // 4) * 16
        new = encode_bc3(os.path.join(HERE, 'tex', 'title4_zh', f'menu_{n}.png'), old[:148])
        assert len(new) == ddslen
        out = bytearray(blob)
        out[off:off + sz] = new + old[ddslen:]
        assert len(out) == len(blob)
        recs.append((f'Part\\TITLE\\parts\\menu_{n}.CL3', bytes(out)))

    # 31 张迷宫名横幅
    for f in sorted(os.listdir(os.path.join(HERE, 'tex', 'mapname_zh'))):
        if not f.endswith('.png') or f.startswith('_'):
            continue
        key = f'Part\\DUNGEON\\Texture\\MapName\\{f[:-4]}.dds'
        raw, _ = B.get(d, byname[key])
        recs.append((key, swap_dds(raw, os.path.join(HERE, 'tex', 'mapname_zh', f))))

    # 地图图例
    key = 'Part\\DUNGEON\\Texture\\MapHelp.dds'
    raw, _ = B.get(d, byname[key])
    recs.append((key, swap_dds(raw, os.path.join(HERE, 'tex', 'MapHelp_zh.png'))))

    build(recs, os.path.join(HERE, 'out', 'Game4_all_zh.oqpatch'), 'Game4.bra')


if __name__ == '__main__':
    main()
