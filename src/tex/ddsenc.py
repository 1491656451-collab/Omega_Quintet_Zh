# -*- coding: utf-8 -*-
"""把 PNG 编码成 DDS。原包是 DX10/BC7（无可用编码器），改写成 BC3(DXT5)。
   游戏自带 FOS01/FOS02.dds 本就是 DXT5，说明加载器按文件头走。"""
import struct
from PIL import Image
import quicktex, quicktex.s3tc.bc3 as bc3

DXGI_BC3_UNORM = 77

def encode_bc3(png_path, ref_dds_bytes, level=18):
    im = Image.open(png_path).convert('RGBA')
    w, h = im.size
    assert w % 4 == 0 and h % 4 == 0, f"尺寸必须是4的倍数: {w}x{h}"
    tex = quicktex.RawTexture.frombytes(im.tobytes(), w, h)
    data = bc3.BC3Encoder(level).encode(tex).tobytes()
    # 复制原 DDS 头（128B）+ DX10 头（20B），只改 dxgiFormat 和 pitch
    hdr = bytearray(ref_dds_bytes[:148])
    struct.pack_into('<I', hdr, 20, w*4)              # dwPitchOrLinearSize = 压缩数据大小
    struct.pack_into('<I', hdr, 20, len(data))
    struct.pack_into('<I', hdr, 128, DXGI_BC3_UNORM)  # DX10 header dxgiFormat
    return bytes(hdr) + data
