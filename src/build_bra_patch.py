#!/usr/bin/env python3
"""生成「按成员名寻址」的 .bra 原地补丁（OQPATCH2）。

和第 5 轮那份 OQPATCH1 的区别：OQPATCH1 里写死了字节偏移，
所以必须先拿到整个包。Game4.bra 有 721MB，传不过来，
于是改成按**成员名**寻址 —— 偏移由 Windows 侧的脚本自己读索引算，
我这边只需要「新的成员内容」就行。
"""
import sys, os, struct, zlib, hashlib
try:
    import zopfli.zlib
    HAVE_ZOPFLI = True
except ImportError:
    HAVE_ZOPFLI = False


def build(records, out, target='Game4.bra'):
    """records: [(成员名, 新的未压缩字节)]"""
    buf = bytearray()
    buf += b'OQPATCH2'
    buf += struct.pack('<I', len(records))
    tb = target.encode('ascii')
    buf += struct.pack('<H', len(tb)) + tb
    for name, raw in records:
        nb = name.encode('ascii')
        # 原地补丁必须塞回原来的槽位，所以压得越狠越好。
        # zopfli 比 zlib -9 还能再省 3~4%（实测每个成员省 ~1500 字节），
        # menu_Quit 就是靠这个才塞进去的（zlib-9 差 103 字节）。
        co = zlib.compressobj(9, zlib.DEFLATED, -15)
        blob = co.compress(raw) + co.flush()
        if HAVE_ZOPFLI:
            z = zopfli.zlib.compress(raw, numiterations=100)[2:-4]   # 去 zlib 头尾 = 裸 deflate
            assert zlib.decompress(z, -15) == raw, name
            if len(z) < len(blob):
                blob = z
        buf += struct.pack('<H', len(nb)) + nb
        buf += struct.pack('<I', len(raw))
        buf += hashlib.md5(raw).hexdigest().encode()
        buf += struct.pack('<I', len(blob)) + blob
        print(f'  {name:44s} 原始 {len(raw):8d} -> 压缩 {len(blob):8d}（含块头 {len(blob)+16}）')
    open(out, 'wb').write(bytes(buf))
    print(f'补丁 {len(records)} 个成员 -> {out}  {os.path.getsize(out)} 字节')


if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'tex'))
    from cl3 import CL3
    from ddsenc import encode_bc3

    SRC = '/mnt/user-data/uploads/欧米伽五重奏/oq_found/'
    recs = []
    for n in ['Newgame', 'Continue', 'LoadGame', 'Config', 'DLCMenu', 'Quit']:
        blob = open(SRC + f'Game4.bra__Part_TITLE_parts_menu_{n}.CL3', 'rb').read()
        c = CL3(data=blob)
        # 注意：LoadGame / DLCMenu / Quit 这三个 CL3 里面的成员名
        # 没有跟着改，仍然叫 menu_Newgame.tid，所以要按「不是 Back 的那个 tid」来找
        idx = [k for k, (nm, _, _) in enumerate(c.files)
               if nm.endswith('.tid') and 'Back' not in nm]
        assert len(idx) == 1, (n, [f[0] for f in c.files])
        k = idx[0]
        nm, off, sz = c.files[k]
        old = blob[off:off + sz]
        assert old[:4] == b'DDS '
        h, w = struct.unpack_from('<II', old, 12)
        ddslen = 148 + (w // 4) * (h // 4) * 16
        png = os.path.join(HERE, 'tex', 'title4_zh', f'menu_{n}.png')
        new = encode_bc3(png, old[:148])
        assert len(new) == ddslen
        out = bytearray(blob)
        out[off:off + sz] = new + old[ddslen:]
        assert len(out) == len(blob)
        recs.append((f'Part\\TITLE\\parts\\menu_{n}.CL3', bytes(out)))
    build(recs, os.path.join(HERE, 'out', 'Game4_title_zh.oqpatch'), 'Game4.bra')
