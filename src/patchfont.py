import struct, hashlib, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffu

ALL_CJK=True
BOLD="/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
CFG={"sysfont":dict(W=24,H=30,size=24,dx=0,dy=-3),
     "advfont":dict(W=35,H=44,size=33,dx=1,dy=-3)}

def pack4(arr, W, H):
    """arr: HxStride uint8 0..255 -> 4bpp bytes, even index = high nibble"""
    stride=(W+7)//8*8
    a=np.zeros((H,stride),dtype=np.uint8)
    a[:,:arr.shape[1]]=arr[:,:stride]
    n=((a.astype(np.uint16)*15+127)//255).astype(np.uint8)
    flat=n.reshape(-1)
    hi=flat[0::2]<<4
    lo=flat[1::2]
    return (hi|lo).tobytes()

def patch(src, out, kind, verbose=True):
    cfg=CFG[kind]; W,H=cfg["W"],cfg["H"]
    stride=(W+7)//8*8
    f=ffu.FFU(src); ch=f.chars()
    bmp=bytearray(f.raw[f.bmpoff:f.tail])
    meta=list(f.meta)
    # find placeholder signature
    import collections
    sigs=collections.Counter()
    cjk=[c for c in ch if 0x4E00<=ord(c)<=0x9FFF]
    def sig(c):
        w,h,sz,off=f.meta[ch[c]]
        return hashlib.md5(f.raw[f.bmpoff+off:f.bmpoff+off+sz]).hexdigest()
    for c in cjk: sigs[sig(c)]+=1
    ph=sigs.most_common(1)[0][0]
    targets=cjk if ALL_CJK else [c for c in cjk if sig(c)==ph]
    targets.sort()
    fnt=ImageFont.truetype(BOLD,cfg["size"],index=2)
    t0=time.time(); n=0
    PAD=20
    for c in targets:
        im=Image.new("L",(stride+2*PAD,H+2*PAD),0)
        ImageDraw.Draw(im).text((PAD+cfg["dx"],PAD+cfg["dy"]), c, font=fnt, fill=255)
        arr=np.asarray(im.crop((PAD,PAD,PAD+stride,PAD+H)))
        data=pack4(arr,W,H)
        off=len(bmp)
        bmp+=data
        meta[ch[c]]=(W,H,len(data),off)
        n+=1
    if verbose: print(kind,"patched",n,"glyphs in",round(time.time()-t0,1),"s")
    # rebuild
    d=f.raw
    newmeta=b"".join(struct.pack("<BBHI",*m) for m in meta)
    assert len(newmeta)==f.nglyph*8
    head=bytearray(d[:f.bmpoff])
    head[f.metaoff:f.metaoff+len(newmeta)]=newmeta
    tailbytes=d[f.tail:]
    newtail=f.bmpoff+len(bmp)
    struct.pack_into("<I",head,16,newtail)
    open(out,"wb").write(bytes(head)+bytes(bmp)+tailbytes)
    return out

if __name__=="__main__":
    patch(sys.argv[1],sys.argv[2],sys.argv[3])
