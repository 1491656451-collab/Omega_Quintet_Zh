import struct, os, sys

SEC=0x38; SECSZ=0x50; ESZ=560; NAMEOFF=0; OFFFLD=516; SIZEFLD=520

class CL3:
    def __init__(self,path=None,data=None):
        d=open(path,'rb').read() if path else data
        assert d[:4]==b'CL3L', d[:4]
        self.raw=d
        self.secs={}
        p=SEC
        while True:
            nm=d[p:p+32].split(b'\0')[0].decode('ascii','replace')
            if not nm: break
            cnt,size,tbl=struct.unpack_from('<III',d,p+32)
            self.secs[nm]=(cnt,size,tbl)
            if nm=='FILE_LINK': break
            p+=SECSZ
        cnt,size,tbl=self.secs['FILE_COLLECTION']
        self.base=tbl
        self.files=[]
        for i in range(cnt):
            e=tbl+i*ESZ
            nm=d[e:e+256].split(b'\0')[0].decode('ascii','replace')
            off,sz=struct.unpack_from('<II',d,e+OFFFLD)
            self.files.append((nm,tbl+off,sz))
    def get(self,i):
        nm,off,sz=self.files[i]
        return self.raw[off:off+sz]

if __name__=="__main__":
    c=CL3(sys.argv[1])
    print(c.secs)
    tot=0
    for nm,off,sz in c.files:
        print(f"  {nm:28s} off={off:9d} size={sz:9d}")
        tot+=sz
    print("files",len(c.files),"total",tot,"filesize",len(c.raw))
    if len(sys.argv)>2:
        os.makedirs(sys.argv[2],exist_ok=True)
        for i,(nm,off,sz) in enumerate(c.files):
            open(os.path.join(sys.argv[2],nm or f"_{i}"),'wb').write(c.get(i))
