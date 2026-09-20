import struct, zlib, os, sys

def read_index(d):
    magic,ver,idxoff,cnt = struct.unpack_from("<4sIII",d,0)
    assert magic==b"PDA\0"
    p=idxoff; ents=[]
    for i in range(cnt):
        h1,h2,csz,usz = struct.unpack_from("<IIII",d,p)
        nl,flg = struct.unpack_from("<HH",d,p+16)
        off, = struct.unpack_from("<I",d,p+20)
        nf = d[p+24:p+24+nl]
        name = nf.split(b"\0")[0].decode("ascii","replace")
        p += 24+nl
        ents.append(dict(name=name,off=off,csz=csz,usz=usz,h1=h1,h2=h2,flg=flg,nl=nl,namefield=nf))
    return ver,ents

def get(d,e):
    usz,csz,ts,flg,pad = struct.unpack_from("<IIIHH",d,e["off"])
    blob = d[e["off"]+16:e["off"]+16+csz]
    if flg==6:
        out = zlib.decompress(blob,-15)
    elif flg==0:
        out = blob
    else:
        out = None
    return out, (usz,csz,ts,flg,pad)

if __name__=="__main__":
    src=sys.argv[1]; dst=sys.argv[2] if len(sys.argv)>2 else None
    d=open(src,"rb").read()
    ver,ents=read_index(d)
    for e in ents:
        out,meta=get(d,e)
        print("%-46s off=%9d csz=%9d usz=%9d flg=%d %s"%(e["name"],e["off"],e["csz"],e["usz"],meta[3], "OK" if out is not None and len(out)==e["usz"] else "MISMATCH"))
        if dst and out is not None:
            p=os.path.join(dst,e["name"].replace("\\","/"))
            os.makedirs(os.path.dirname(p),exist_ok=True)
            open(p,"wb").write(out)
