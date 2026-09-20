#!/usr/bin/env python3
"""apply_bra.ps1 的 Python 复刻，用来在这边先把补丁跑一遍。
   逻辑一比一照抄：按成员名从索引里找偏移 -> 查槽位塞不塞得下 ->
   写块头+压缩流 -> 改索引里的 csz/usz -> 解出来核 MD5 -> 记 undo -> 还原。"""
import sys, os, struct, zlib, hashlib, shutil

def apply(target, patch, undo_out):
    pb = open(patch, 'rb').read()
    assert pb[:8] == b'OQPATCH2'
    cnt = struct.unpack_from('<I', pb, 8)[0]
    tl = struct.unpack_from('<H', pb, 12)[0]
    p = 14 + tl
    d = bytearray(open(target, 'rb').read())
    magic, ver, idxoff, ecount = struct.unpack_from('<4sIII', d, 0)
    assert magic == b'PDA\0'
    q = idxoff; mp = {}
    for i in range(ecount):
        csz = struct.unpack_from('<I', d, q + 8)[0]
        nl = struct.unpack_from('<H', d, q + 16)[0]
        off = struct.unpack_from('<I', d, q + 20)[0]
        nm = bytes(d[q + 24:q + 24 + nl]).split(b'\0')[0].decode('ascii')
        mp.setdefault(nm, (off, csz, q))
        q += 24 + nl
    jobs = []
    for i in range(cnt):
        nl = struct.unpack_from('<H', pb, p)[0]; p += 2
        nm = pb[p:p + nl].decode(); p += nl
        usz = struct.unpack_from('<I', pb, p)[0]; p += 4
        md5 = pb[p:p + 32].decode(); p += 32
        bl = struct.unpack_from('<I', pb, p)[0]; p += 4
        blob = pb[p:p + bl]; p += bl
        if nm not in mp:
            print('  成员不存在（跳过）:', nm); continue
        off, csz, ip = mp[nm]
        if 16 + bl > csz:
            print(f'  塞不下: {nm} 需要 {16+bl} 槽位 {csz}'); return 4
        jobs.append((nm, off, csz, ip, usz, md5, blob))
    # undo
    undo = []
    for nm, off, csz, ip, usz, md5, blob in jobs:
        span = 16 + len(blob)
        undo.append((off, bytes(d[off:off + span])))
        undo.append((ip + 8, bytes(d[ip + 8:ip + 16])))
    # write
    for nm, off, csz, ip, usz, md5, blob in jobs:
        hdr = bytearray(d[off:off + 16])
        struct.pack_into('<II', hdr, 0, usz, len(blob))
        d[off:off + 16] = hdr
        d[off + 16:off + 16 + len(blob)] = blob
        struct.pack_into('<II', d, ip + 8, 16 + len(blob), usz)
    # verify
    bad = 0
    for nm, off, csz, ip, usz, md5, blob in jobs:
        u2, c2 = struct.unpack_from('<II', d, off)
        raw = zlib.decompress(bytes(d[off + 16:off + 16 + c2]), -15)
        if len(raw) != usz or hashlib.md5(raw).hexdigest() != md5:
            print('  校验失败:', nm); bad += 1
    print(f'  写入 {len(jobs)} 个成员，校验失败 {bad}')
    open(target, 'wb').write(bytes(d))
    open(undo_out, 'wb').write(b''.join(struct.pack('<QI', o, len(b)) + b for o, b in undo))
    return 5 if bad else 0


def rollback(target, undo_file):
    d = bytearray(open(target, 'rb').read())
    u = open(undo_file, 'rb').read(); p = 0
    n = 0
    while p < len(u):
        off, ln = struct.unpack_from('<QI', u, p); p += 12
        d[off:off + ln] = u[p:p + ln]; p += ln; n += 1
    open(target, 'wb').write(bytes(d))
    return n


if __name__ == '__main__':
    src = sys.argv[1]; patch = sys.argv[2]
    tmp = '/tmp/_oqtest.bra'
    shutil.copyfile(src, tmp)
    m0 = hashlib.md5(open(tmp, 'rb').read()).hexdigest()
    print('原包 MD5', m0, os.path.getsize(tmp), '字节')
    r = apply(tmp, patch, '/tmp/_oqtest.undo')
    print('  返回', r, '包大小', os.path.getsize(tmp))
    # 随机抽 40 个别的成员解压，确认没被殃及
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bra as B, random
    d = open(tmp, 'rb').read()
    _, ents = B.read_index(d)
    random.seed(1)
    bad = 0
    for e in random.sample(ents, 40):
        out, meta = B.get(d, e)
        if out is None or len(out) != e['usz']:
            print('  其它成员坏了:', e['name']); bad += 1
    print('  随机抽 40 个其它成员解压，坏 {}'.format(bad))
    n = rollback(tmp, '/tmp/_oqtest.undo')
    m1 = hashlib.md5(open(tmp, 'rb').read()).hexdigest()
    print(f'  还原 {n} 段，MD5 {"回到原版" if m1 == m0 else "对不上！"}')
    os.remove(tmp); os.remove('/tmp/_oqtest.undo')
