#!/usr/bin/env python3
"""标题画面汉化：把三个 menu_*.CL3 里的 .tid（其实就是 DDS）换成中文版，
   重新压回 Game1.bra —— 但不重打包整个 388MB 的包，
   而是生成一份「原地补丁」：只改几段字节。

   可行的前提：
     1. BC3 和 BC7 的块大小都是 16 字节/4x4，所以 DDS 体积一模一样，
        CL3 整体体积也就一模一样；
     2. CL3 改动很小，zlib 压完通常不会比原来大，塞得进原来的槽位；
        塞不进就报错，退回整包重打。
"""
import sys, os, struct, zlib, json, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex'))
import bra as B
from cl3 import CL3
from ddsenc import encode_bc3

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS = ['menu_Newgame', 'menu_Continue', 'menu_Config']


def patched_cl3(blob, name, png):
    """把 CL3 里 <name>.tid 的 DDS 部分换掉，其余字节原样保留。"""
    c = CL3(data=blob)
    idx = [i for i, (nm, _, _) in enumerate(c.files) if nm == name + '.tid']
    assert len(idx) == 1, (name, [f[0] for f in c.files])
    i = idx[0]
    nm, off, sz = c.files[i]
    old = blob[off:off + sz]
    assert old[:4] == b'DDS ', old[:4]
    tail_len = len(old) - (148 + struct.unpack_from('<II', old, 12)[0] *
                           0)  # 尾巴长度下面算
    # DDS 数据长度 = 块数 * 16
    h, w = struct.unpack_from('<II', old, 12)
    ddslen = 148 + (w // 4) * (h // 4) * 16
    tail = old[ddslen:]
    new_dds = encode_bc3(png, old[:148])
    assert len(new_dds) == ddslen, (len(new_dds), ddslen)
    out = bytearray(blob)
    out[off:off + sz] = new_dds + tail
    assert len(out) == len(blob)
    return bytes(out)


def main(game1, out_json):
    d = open(game1, 'rb').read()
    ver, ents = B.read_index(d)
    # 索引项在文件里的绝对位置
    idxoff = struct.unpack_from('<I', d, 8)[0]
    pos = idxoff
    idxpos = {}
    for e in ents:
        idxpos[e['name']] = pos
        pos += 24 + e['nl']

    patches = []
    for name in ITEMS:
        key = f'Part\\TITLE\\parts\\{name}.CL3'
        e = [x for x in ents if x['name'] == key][0]
        raw, meta = B.get(d, e)
        png = os.path.join(HERE, 'tex', 'title_zh', f'{name}.png')
        new_raw = patched_cl3(raw, name, png)
        co = zlib.compressobj(9, zlib.DEFLATED, -15)
        blob = co.compress(new_raw) + co.flush()
        chunk = struct.pack('<IIIHH', len(new_raw), len(blob),
                            meta[2], meta[3], meta[4]) + blob
        if len(chunk) > e['csz']:
            raise SystemExit(f'{name}: 压缩后 {len(chunk)} > 原槽位 {e["csz"]}，装不下')
        patches.append((e['off'], chunk))
        # 索引里的 csz / usz 也要跟着改（usz 其实没变，稳妥起见一起写）
        ip = idxpos[key]
        patches.append((ip + 8, struct.pack('<II', len(chunk), len(new_raw))))
        print(f'{name:14s} 原槽位 {e["csz"]:7d} -> 新 {len(chunk):7d}  '
              f'省 {e["csz"]-len(chunk):6d} 字节')

    total = sum(len(b) for _, b in patches)
    obj = {'target': 'Game1.bra',
           'size': len(d),
           'patches': [{'off': o, 'data': base64.b64encode(b).decode()} for o, b in patches]}
    json.dump(obj, open(out_json, 'w'))
    print(f'补丁 {len(patches)} 段 / 共 {total} 字节 -> {out_json} '
          f'({os.path.getsize(out_json)} 字节)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
