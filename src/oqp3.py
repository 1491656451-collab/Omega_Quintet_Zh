# -*- coding: utf-8 -*-
"""OQPATCH3 —— 按成员名寻址、可追加的 .bra 差分补丁。

和 OQPATCH2 的区别：新压缩块塞不回原槽位时，**追加到文件末尾**再改索引里的 off，
所以字体那种「体积翻倍」的成员也能打。补丁里只有我们改过的成员，不含游戏原档。

格式：
  'OQPATCH3' u32 记录数 u16 标题长 标题(utf-8)
  每条记录： u16 名长 名(ascii) u32 新未压缩长 32s 新MD5 32s 原MD5 u32 块长 块(raw deflate)

撤销文件 OQUNDO2：
  'OQUNDO2' u64 原文件长度 u32 区段数 [u64 偏移 u32 长度 原字节]...
"""
import struct, zlib, hashlib, os

MAGIC = b'OQPATCH3'
UMAGIC = b'OQUNDO2'


def md5h(b):
    return hashlib.md5(b).hexdigest().encode('ascii')


def build(records, title, out_path, level=9):
    """records: [(name, new_uncompressed_bytes, old_uncompressed_bytes)]"""
    t = title.encode('utf-8')
    buf = bytearray(MAGIC + struct.pack('<I', len(records)) + struct.pack('<H', len(t)) + t)
    for name, new, old in records:
        nb = name.encode('ascii')
        co = zlib.compressobj(level, zlib.DEFLATED, -15)
        blob = co.compress(new) + co.flush()
        buf += struct.pack('<H', len(nb)) + nb
        buf += struct.pack('<I', len(new))
        buf += md5h(new) + md5h(old)
        buf += struct.pack('<I', len(blob)) + blob
    open(out_path, 'wb').write(bytes(buf))
    return len(buf)


def parse(path):
    d = open(path, 'rb').read()
    assert d[:8] == MAGIC, '不是 OQPATCH3'
    cnt, = struct.unpack_from('<I', d, 8)
    tl, = struct.unpack_from('<H', d, 12)
    title = d[14:14 + tl].decode('utf-8')
    p = 14 + tl
    recs = []
    for _ in range(cnt):
        nl, = struct.unpack_from('<H', d, p); p += 2
        name = d[p:p + nl].decode('ascii'); p += nl
        usz, = struct.unpack_from('<I', d, p); p += 4
        m_new = d[p:p + 32]; p += 32
        m_old = d[p:p + 32]; p += 32
        bl, = struct.unpack_from('<I', d, p); p += 4
        blob = d[p:p + bl]; p += bl
        recs.append(dict(name=name, usz=usz, md5=m_new, md5_old=m_old, blob=blob))
    return title, recs


# ---------------------------------------------------------------- 应用（Python 孪生）

def _index(f):
    f.seek(0)
    magic, ver, idxoff, cnt = struct.unpack('<4sIII', f.read(16))
    assert magic == b'PDA\0'
    f.seek(idxoff)
    ib = f.read()
    m = {}
    q = 0
    for _ in range(cnt):
        csz, = struct.unpack_from('<I', ib, q + 8)
        nl, = struct.unpack_from('<H', ib, q + 16)
        off, = struct.unpack_from('<I', ib, q + 20)
        nm = ib[q + 24:q + 24 + nl].split(b'\0')[0].decode('ascii')
        if nm not in m:
            m[nm] = dict(off=off, csz=csz, idxpos=idxoff + q)
        q += 24 + nl
    return m, idxoff


def apply(target, patch, undo_path=None, verbose=True):
    """返回 (exit_code, 说明)。0 成功 / 2 已经打过 / 3 缺成员 / 5 校验失败已回滚 / 6 原档对不上"""
    undo_path = undo_path or target + '.oqundo'
    title, recs = parse(patch)
    f = open(target, 'r+b')
    try:
        m, idxoff = _index(f)
        orig_len = os.path.getsize(target)
        jobs = []
        already = 0
        mismatch = []
        for r in recs:
            if r['name'] not in m:
                return 3, '缺成员: ' + r['name']
            e = m[r['name']]
            f.seek(e['off'])
            hdr = f.read(16)
            usz, csz, ts, flg, pad = struct.unpack('<IIIHH', hdr)
            if flg != 6:
                return 6, '成员不是 deflate: ' + r['name']
            raw = zlib.decompress(f.read(csz), -15)
            h = md5h(raw)
            if h == r['md5']:
                already += 1
                continue
            if h != r['md5_old']:
                mismatch.append(r['name'])
                continue
            jobs.append((r, e, bytearray(hdr)))
        if mismatch:
            return 6, '这些成员和原版对不上（可能已被别的补丁改过）: ' + ', '.join(mismatch[:5])
        if not jobs:
            return 2, '已经打过了'

        # 撤销文件
        spans = []
        for r, e, hdr in jobs:
            need = 16 + len(r['blob'])
            if need <= e['csz']:
                f.seek(e['off']); spans.append((e['off'], f.read(need)))
            f.seek(e['idxpos'] + 8); spans.append((e['idxpos'] + 8, f.read(8)))
            f.seek(e['idxpos'] + 20); spans.append((e['idxpos'] + 20, f.read(4)))
        u = bytearray(UMAGIC + struct.pack('<QI', orig_len, len(spans)))
        for off, b in spans:
            u += struct.pack('<QI', off, len(b)) + b
        open(undo_path, 'wb').write(bytes(u))

        # 写入
        f.seek(0, 2)
        end = f.tell()
        for r, e, hdr in jobs:
            blob = r['blob']; need = 16 + len(blob)
            struct.pack_into('<II', hdr, 0, r['usz'], len(blob))
            if need <= e['csz']:
                newoff = e['off']
            else:
                if end % 16:
                    f.seek(0, 2); f.write(b'\0' * (16 - end % 16)); end += 16 - end % 16
                newoff = end; end += need
            f.seek(newoff); f.write(bytes(hdr)); f.write(blob)
            f.seek(e['idxpos'] + 8); f.write(struct.pack('<II', need, r['usz']))
            f.seek(e['idxpos'] + 20); f.write(struct.pack('<I', newoff))
        f.flush()

        # 回读校验
        bad = []
        m2, _ = _index(f)
        for r, e, hdr in jobs:
            e2 = m2[r['name']]
            f.seek(e2['off']); h2 = f.read(16)
            csz2, = struct.unpack_from('<I', h2, 4)
            raw = zlib.decompress(f.read(csz2), -15)
            if md5h(raw) != r['md5']:
                bad.append(r['name'])
        if bad:
            rollback(f, undo_path)
            return 5, '校验失败已回滚: ' + ', '.join(bad[:5])
        return 0, '成功替换 %d 个成员（%d 个已是最新）' % (len(jobs), already)
    finally:
        f.close()


def rollback(f, undo_path):
    u = open(undo_path, 'rb').read()
    assert u[:7] == UMAGIC
    orig_len, n = struct.unpack_from('<QI', u, 7)
    p = 7 + 12
    for _ in range(n):
        off, ln = struct.unpack_from('<QI', u, p); p += 12
        f.seek(off); f.write(u[p:p + ln]); p += ln
    f.flush(); f.truncate(orig_len)


def undo(target, undo_path=None):
    undo_path = undo_path or target + '.oqundo'
    with open(target, 'r+b') as f:
        rollback(f, undo_path)
    return 0, '已还原'
