from PIL import Image, ImageDraw, ImageFont

def make_font(path, size, idx=2):
    return ImageFont.truetype(path, size, index=idx)

def render_bitmap(c, fnt, W, H, dx, dy, gamma=1.0):
    """return (stride, bytes) 4bpp, stride = ceil(W/8)*8"""
    stride=(W+7)//8*8
    im=Image.new("L",(stride+40,H+40),0)
    ImageDraw.Draw(im).text((20+dx,20+dy), c, font=fnt, fill=255)
    im=im.crop((20,20,20+stride,20+H))
    px=im.load()
    out=bytearray(stride*H//2)
    for y in range(H):
        for x in range(stride):
            v=px[x,y]
            if gamma!=1.0:
                v=int(255*((v/255.0)**gamma))
            n=(v*15+127)//255
            i=y*stride+x
            if i%2: out[i//2] |= n
            else:   out[i//2] |= (n<<4)
    return stride, bytes(out)
