import struct,sys

def u8bytes(v):
    # value stored as big-endian utf-8 byte sequence packed into int
    b=[]
    while v: b.insert(0,v&0xff); v>>=8
    return bytes(b)

def dec(v):
    b=u8bytes(v)
    try: return b.decode("utf-8")
    except: return None

class FFU:
    def __init__(self,path):
        d=open(path,"rb").read(); self.raw=d
        self.magic,self.nrange,self.nglyph = struct.unpack_from("<HHI",d,0)
        (self.f08,self.f0c,self.tail,self.rangeoff,self.metaoff,self.bmpoff,self.f20,
         self.f24,self.f28)=struct.unpack_from("<9I",d,8)
        self.ranges=[]
        for i in range(self.nrange):
            a,b,g=struct.unpack_from("<III",d,self.rangeoff+i*12)
            self.ranges.append((a,b,g))
        self.meta=[]
        for i in range(self.nglyph):
            w,h,sz,off=struct.unpack_from("<BBHI",d,self.metaoff+i*8)
            self.meta.append((w,h,sz,off))
    def chars(self):
        out={}
        for a,b,g in self.ranges:
            n=0
            v=a
            while v<b:
                c=dec(v)
                if c is not None:
                    out[c]=g+n; n+=1
                v+=1
            # fallback: count by index
        return out

if __name__=="__main__":
    f=FFU(sys.argv[1])
    print("ranges",f.nrange,"glyphs",f.nglyph,"rangeoff",f.rangeoff,"metaoff",f.metaoff,"bmpoff",f.bmpoff)
    for r in f.ranges[:5]: print(r, repr(dec(r[0])), repr(dec(r[1])))
    for r in f.ranges[-5:]: print(r, repr(dec(r[0])), repr(dec(r[1])))
    ch=f.chars()
    print("mapped chars",len(ch))
