import struct,sys,json

class GStr:
    def __init__(self,path=None,data=None):
        d=open(path,"rb").read() if path else data
        self.raw=d
        (self.magic,self.ver,self.hsz,self.x1,self.x2,self.tbloff,self.cnt,self.esz,
         self.x3,self.poolhdr,self.poolcnt,self.pool,self.x4)=struct.unpack_from("<4sIIIIIIIIIIII",d,0)
        assert self.magic==b"GSTL"
        self.head_extra=d[self.poolhdr:self.pool]
        base=self.pool
        def s(off):
            e=d.index(b"\0",base+off)
            return d[base+off:e]
        self.ents=[]
        for i in range(self.cnt):
            koff,idv,voff=struct.unpack_from("<QQQ",d,self.tbloff+i*self.esz)
            self.ents.append([idv,s(koff).decode("utf-8"),s(voff).decode("utf-8")])

def build(ref, ents):
    """ents: list of [id,key,value]; returns bytes in GSTL format"""
    pool=bytearray(); off={}
    def add(sb):
        b=sb.encode("utf-8")
        if b in off: return off[b]
        o=len(pool); pool.extend(b); pool.append(0); off[b]=o; return o
    tbl=bytearray()
    rows=[]
    for idv,k,v in ents:
        rows.append((add(k),idv,add(v)))
    for k,i,v in rows:
        tbl+=struct.pack("<QQQ",k,i,v)
    tbloff=0x40
    poolhdr=tbloff+len(tbl)
    pool_off=poolhdr+len(ref.head_extra)
    hdr=struct.pack("<4sIIIIIIIIIIII",b"GSTL",ref.ver,ref.hsz,ref.x1,ref.x2,
                    tbloff,len(ents),24,ref.x3,poolhdr,len(off),pool_off,ref.x4)
    hdr=hdr.ljust(0x40,b"\0")
    return bytes(hdr+tbl+ref.head_extra+pool)

if __name__=="__main__":
    g=GStr(sys.argv[1])
    print("cnt",g.cnt,"poolcnt",g.poolcnt,"extra",g.head_extra.hex(),"x1",g.x1,"x2",g.x2,"x3",g.x3)
    # roundtrip test
    nb=build(g,g.ents)
    print("roundtrip identical:", nb==g.raw, len(nb), len(g.raw))
    n=int(sys.argv[2]) if len(sys.argv)>2 else 0
    for e in g.ents[:n]: print(e)
