import struct, sys

class GBNL:
    """Compile Heart GBNL table: rows | column-desc | string-pool | 64B footer.
       Strings are handled as raw bytes; decoding is opt-in (utf-8, cp932 fallback)."""
    NOSTR = 0xFFFFFFFF
    def __init__(self, path=None, data=None):
        d = open(path,'rb').read() if path else data
        self.raw = d
        f = len(d)-64
        assert d[f:f+4] == b'GBNL', d[f:f+4]
        (self.v1,self.v2,self.v3,self.v4,self.z0,
         self.nrows,self.rowsize,self.ncols,self.rowbytes,
         self.nstr,self.pool,self.tail1) = struct.unpack_from('<12I', d, f+4)
        self.footoff = f
        self.cols = [struct.unpack_from('<HH', d, self.rowbytes+i*4) for i in range(self.ncols)]
        self.strcols = [o for t,o in self.cols if t == 5]
    def rawstr(self, rel):
        if rel == self.NOSTR or self.pool+rel >= self.footoff: return None
        e = self.raw.index(b'\0', self.pool+rel)
        return self.raw[self.pool+rel:e]
    @staticmethod
    def dec(b):
        if b is None: return None
        try: return b.decode('utf-8'), 'utf-8'
        except UnicodeDecodeError: pass
        try: return b.decode('cp932'), 'cp932'
        except UnicodeDecodeError: return b.decode('latin-1'), 'latin-1'
    def cells(self):
        for i in range(self.nrows):
            for o in self.strcols:
                rel = struct.unpack_from('<I', self.raw, i*self.rowsize+o)[0]
                yield i, o, rel, self.rawstr(rel)
    def rebuild(self, mapping, rowpatch=None):
        """mapping: {(row, col_offset): str}. Untouched cells keep their exact original bytes.
        rowpatch: {(row, col_offset, width): str} —— 行记录里的定长内嵌字段（类型 1 的
        宽字段，物品名/技能名那批）。写进去的是 UTF-8 + NUL，余下补零；超宽直接报错。"""
        d = bytearray(self.raw[:self.rowbytes])
        for (i, o, w), v in (rowpatch or {}).items():
            b = v.encode('utf-8')
            if len(b) + 1 > w:
                raise ValueError(f'内嵌字段放不下: row {i} +{o:#x} 宽 {w}，{v!r} 要 {len(b)+1} 字节')
            d[i*self.rowsize+o : i*self.rowsize+o+w] = b + b'\0'*(w-len(b))
        d += self.raw[self.rowbytes:self.pool]          # column table verbatim
        pool = bytearray(); idx = {}
        def add(b):
            if b in idx: return idx[b]
            o = len(pool); pool.extend(b); pool.append(0); idx[b] = o; return o
        for i, o, rel, ob in self.cells():
            if ob is None:
                struct.pack_into('<I', d, i*self.rowsize+o, rel); continue
            new = mapping.get((i,o))
            nb = new.encode('utf-8') if new is not None else ob
            struct.pack_into('<I', d, i*self.rowsize+o, add(nb))
        while len(pool) % 16: pool.append(0)
        foot = bytearray(self.raw[self.footoff:])
        struct.pack_into('<12I', foot, 4, self.v1,self.v2,self.v3,self.v4,self.z0,
                         self.nrows,self.rowsize,self.ncols,self.rowbytes,
                         len(idx), self.pool, self.tail1)
        return bytes(d)+bytes(pool)+bytes(foot)

if __name__ == "__main__":
    g = GBNL(sys.argv[1])
    print(f"rows={g.nrows} rowsize={g.rowsize} ncols={g.ncols} pool@{g.pool} nstr={g.nstr} strcols={g.strcols}")
    for i,o,rel,b in list(g.cells())[:int(sys.argv[2]) if len(sys.argv)>2 else 8]:
        print(i, hex(o), (g.dec(b) if b is not None else None))
