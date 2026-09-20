# -*- coding: utf-8 -*-
"""CL3 容器写回。

布局（database.cl3 实测）：
    0x00        头 0x38 字节
    0x38        段描述符，每个 0x50：名字(32) + cnt,size,tbl (3×u32)
                目前就两段：FILE_COLLECTION、FILE_LINK
    tbl(=216)   FILE_COLLECTION 表，cnt × 560 字节
                每条：名字(256) … 偏移@+516（相对 tbl）、大小@+520
    表后        各成员数据**连续排列、无填充**，每个成员大小都是 16 的倍数
    末尾        FILE_LINK 的 tbl 指向文件末尾（本文件里它是空段）
"""
import struct
from cl3 import CL3, SEC, SECSZ, ESZ, OFFFLD, SIZEFLD


def rebuild(orig_bytes, replacements):
    """replacements: {成员名: 新字节}。没给的成员原样保留。"""
    c = CL3(data=orig_bytes)
    d = bytearray(orig_bytes)
    tbl = c.base
    n = len(c.files)

    body = bytearray()
    base_rel = n * ESZ                      # 数据区相对 tbl 的起始 = 表本身的长度
    for i, (nm, off, sz) in enumerate(c.files):
        blob = replacements.get(nm, orig_bytes[off:off + sz])
        if len(blob) % 16:
            raise ValueError(f'{nm}: 大小 {len(blob)} 不是 16 的倍数，原文件里所有成员都是')
        rel = base_rel + len(body)
        struct.pack_into('<II', d, tbl + i * ESZ + OFFFLD, rel, len(blob))
        body += blob

    out = bytearray(d[:tbl + n * ESZ])       # 头 + 段描述符 + 条目表（含刚改过的 off/size）
    out += body

    # 更新段描述符：FILE_COLLECTION.size 和 FILE_LINK.tbl
    p = SEC
    while True:
        name = bytes(out[p:p + 32]).split(b'\0')[0].decode('ascii', 'replace')
        if not name:
            break
        if name == 'FILE_COLLECTION':
            struct.pack_into('<I', out, p + 36, len(out) - tbl)   # size
        elif name == 'FILE_LINK':
            struct.pack_into('<I', out, p + 40, len(out))         # tbl 指向末尾（cnt@+32 size@+36 tbl@+40）
            break
        p += SECSZ
    return bytes(out)


def selftest(path):
    """空替换必须字节一致 —— 不然写回逻辑就是错的。"""
    b = open(path, 'rb').read()
    return rebuild(b, {}) == b


if __name__ == '__main__':
    import sys
    print('空替换往返字节一致:', selftest(sys.argv[1]))
