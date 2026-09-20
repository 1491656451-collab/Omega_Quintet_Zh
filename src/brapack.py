import struct, zlib, os, sys
from bra import read_index

def repack(src, replacements, out):
    """replacements: {name(with backslashes): bytes_uncompressed}"""
    d=open(src,"rb").read()
    ver,ents=read_index(d)
    body=bytearray()
    newents=[]
    for e in ents:
        off=len(body)+16   # data offsets are relative to file start; header is 16 bytes
        name=e["name"]
        if name in replacements:
            raw=replacements[name]
            co=zlib.compressobj(9,zlib.DEFLATED,-15)
            blob=co.compress(raw)+co.flush()
            usz=len(raw); csz=len(blob)
            ts=struct.unpack_from("<I",d,e["off"]+8)[0]
            flg,pad=struct.unpack_from("<HH",d,e["off"]+12)
            chunk=struct.pack("<IIIHH",usz,csz,ts,flg,pad)+blob
        else:
            chunk=d[e["off"]:e["off"]+e["csz"]]
            usz=e["usz"]
        body+=chunk
        ne=dict(e); ne["off"]=off; ne["csz"]=len(chunk); ne["usz"]=usz
        newents.append(ne)
    idx=bytearray()
    for e in newents:
        nb=e["name"].encode("ascii")
        nf=d[0:0]  # placeholder
        # original name field bytes (length e["nl"]) preserved from source index
        idx+=struct.pack("<IIIIHHI",e["h1"],e["h2"],e["csz"],e["usz"],e["nl"],e["flg"],e["off"])
        idx+=e["namefield"]
    idxoff=16+len(body)
    hdr=struct.pack("<4sIII",b"PDA\0",ver,idxoff,len(newents))
    open(out,"wb").write(hdr+bytes(body)+bytes(idx))
    return out
