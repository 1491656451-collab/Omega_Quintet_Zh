import ffu
from PIL import Image, ImageDraw, ImageFont

NOTO="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
IDX_SC=2   # will be detected

def load(size, idx):
    return ImageFont.truetype(NOTO, size, index=idx)

def ink_box(img):
    bb=img.getbbox()
    return bb

def render_char(c, font, W, H, ox, oy):
    im=Image.new("L",(W+40,H+40),0)
    d=ImageDraw.Draw(im)
    d.text((20+ox,20+oy), c, font=font, fill=255)
    return im.crop((20,20,20+W,20+H))

if __name__=="__main__":
    import sys
    # find SC face index
    from fontTools.ttLib import TTCollection
    tc=TTCollection(NOTO)
    for i,f in enumerate(tc.fonts):
        n=f["name"].getDebugName(1)
        if "SC" in n: print(i,n)
