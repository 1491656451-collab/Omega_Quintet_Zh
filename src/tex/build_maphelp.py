# -*- coding: utf-8 -*-
"""地图图例 Part\\DUNGEON\\Texture\\MapHelp.dds（640x880, BC7）汉化。

这张贴图 Game1.bra 和 Game4.bra 里各有一份（成员名、大小都一样）。
之前一直搜不到图例的文字，就是因为它根本不是文本，是画在贴图上的。

结构很规整：12 行，每行「◇ 标题（白）」+「说明（青）」，底板是两种纯色
（标题带 16,44,68,204 / 说明带 11,23,41,205），所以擦除就是按框填底色 ——
底色取框内**非文字像素**的中位数，这样不用担心取样列取歪（结算画面那次的教训）。
◇ 菱形在 x<55，不动。
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render3 import FONT

SRC = os.path.join(HERE, 'MapHelp_orig.png')

# (y0, y1, x0, x1)  —— 从原图里量出来的英文墨迹框
# 注意：标题行的右侧有图标，量框时必须停在「第一个 >=25px 的空隙」，
# 否则会把图标一起圈进擦除框 —— 第一版就是这么把敌人图标和宝箱图标抹掉的。
TITLE_BOX = [(37, 62, 55, 218), (107, 131, 55, 220), (176, 196, 55, 222), (244, 265, 55, 212),
             (314, 334, 55, 196), (382, 404, 55, 260), (451, 476, 55, 253), (520, 546, 55, 330),
             (589, 610, 55, 243), (658, 684, 55, 307), (727, 753, 55, 304), (797, 818, 55, 248)]
DESC_BOX = [(71, 89, 37, 235), (139, 158, 37, 610), (208, 227, 37, 513), (278, 296, 37, 366),
            (346, 365, 37, 611), (416, 434, 37, 481), (484, 503, 37, 404), (554, 572, 35, 540),
            (623, 641, 37, 371), (692, 710, 37, 400), (761, 779, 37, 446), (830, 847, 37, 452)]

TITLE_ZH = ['玩家图标', '敌人图标', '事件点', '存档点', '遗失物', '清除点',
            '解析点', '突破点', '圣域点', '禁行点', '地图切换点', '重启点']
DESC_ZH = ['显示玩家所在位置的图标。',
           '显示敌人图标。（稀有／弱／普通／强／极强／极端）',
           '显示可能发生事件的地点。（支线／主线）',
           '显示可以存档的区域。',
           '显示遗失物所在位置。（普通／消除／探物／隐藏）',
           '显示可以清除Blare的地点。',
           '可以进行解析的地点。',
           '可以突破的区域。（高跳Lv.3）',
           '可以通过的地点。',
           '无法通过的地点。',
           '可以移动到其他地图的地点。',
           '可以存档、退出并重新开始的地点。']

TITLE_RGB = (235, 239, 247)      # 采自原图
DESC_RGB = (25, 233, 205)
TITLE_SIZE = 22                  # 12 行统一字号
DESC_SIZE = 16


def masks(a):
    rgb = a[:, :, :3].astype(int); al = a[:, :, 3].astype(int)
    lum = rgb.mean(axis=2); sat = rgb.max(axis=2) - rgb.min(axis=2)
    white = (lum > 150) & (sat < 60) & (al > 120)
    cyan = (rgb[:, :, 1] > 140) & (rgb[:, :, 2] > 120) & (rgb[:, :, 0] < 140) & (al > 120)
    return white, cyan


def erase(a, box, mask):
    """底色 = 框内非文字像素的中位数；文字掩膜先膨胀，把抗锯齿边也排掉。"""
    from scipy import ndimage
    y0, y1, x0, x1 = box
    sub = a[y0:y1, x0:x1]
    m = ndimage.binary_dilation(mask[y0:y1, x0:x1], np.ones((5, 5), bool))
    bgpix = sub[~m]
    if len(bgpix) < 30:
        raise SystemExit(f'框 {box} 里几乎全是字，取不到底色')
    bg = np.median(bgpix.reshape(-1, 4), axis=0).round().astype(np.uint8)
    spread = bgpix.reshape(-1, 4).std(axis=0)
    if spread[:3].max() > 22:          # 底色不该有花样；有就说明框里混进了图标/线
        raise SystemExit(f'框 {box} 的底色太杂（std={spread.round(1)}），八成圈到图标了')
    a[y0:y1, x0:x1] = bg
    return bg, spread


def text_img(text, size, color):
    f = ImageFont.truetype(FONT, size, index=2)
    tmp = Image.new('L', (size * (len(text) + 2), size * 3), 0)
    ImageDraw.Draw(tmp).text((size, size // 2), text, font=f, fill=255)
    bb = tmp.getbbox()
    m = tmp.crop(bb)
    out = Image.new('RGBA', m.size, (*color, 0))
    out.putalpha(m)
    return out


def fit(text, color, bw, bh, lo=8, hi=40):
    best = lo
    while lo <= hi:
        s = (lo + hi) // 2
        im = text_img(text, s, color)
        if im.width <= bw and im.height <= bh:
            best = s; lo = s + 1
        else:
            hi = s - 1
    return best


def main(out_path=None, preview=None):
    im = Image.open(SRC).convert('RGBA')
    a = np.array(im)
    orig_a = a.copy()
    white, cyan = masks(a)
    bgmap = {}
    for tag, boxes, mask in (('标题', TITLE_BOX, white), ('说明', DESC_BOX, cyan)):
        for i, box in enumerate(boxes):
            bg, sp = erase(a, box, mask)
            bgmap[(tag, i)] = tuple(int(v) for v in bg)
    im = Image.fromarray(a, 'RGBA')

    PANEL_R = 612          # 面板右边界，字不许越过
    # 英文的框高度是被 y/p 这种下伸部撑出来的，逐框取最大字号会让 12 行大小不一。
    # 改成全组统一字号，竖直方向对齐到原墨迹框的中心，允许往上下各溢一点点 ——
    # 那一圈是纯色底板，溢出去也不会碰到分隔线（下面 assert 会校验）。
    for tag, boxes, texts, color, size in (
            ('标题', TITLE_BOX, TITLE_ZH, TITLE_RGB, TITLE_SIZE),
            ('说明', DESC_BOX, DESC_ZH, DESC_RGB, DESC_SIZE)):
        for i, (box, zh) in enumerate(zip(boxes, texts)):
            y0, y1, x0, x1 = box
            lab = text_img(zh, size, color)

            ox = x0 + (6 if tag == '标题' else 0)   # 标题要和 ◇ 留一点间距
            oy = y0 + ((y1 - y0) - lab.height) // 2
            assert ox + lab.width <= PANEL_R, f'{tag}{i} 太宽 {lab.width}'
            # 标签比擦除框高一点，溢出的上下两条必须落在纯色底上，
            # 不能压到分隔线或图标。拿该框的底色当基准逐像素比。
            bg = np.array(bgmap[(tag, i)], dtype=int)
            for sy0, sy1 in ((oy, min(y0, oy + lab.height)),
                             (max(y1, oy), oy + lab.height)):
                if sy1 <= sy0: continue
                strip = orig_a[sy0:sy1, ox:ox + lab.width].astype(int)
                stray = int((np.abs(strip - bg).sum(axis=2) > 90).sum())
                assert stray < 20, (f'{tag}{i} 溢出的那条里有 {stray} 个异色像素'
                                    f'（y {sy0}..{sy1}），可能压到分隔线或图标')
            im.alpha_composite(lab, (ox, oy))
            print(f'  {tag} {i:2d} 字号 {size} {lab.size} 放在 {(ox, oy)}  {zh}')

    if out_path:
        im.save(out_path)
    if preview:
        old = Image.open(SRC).convert('RGBA')
        cv = Image.new('RGB', (old.width * 2 + 20, old.height), (0, 0, 0))
        for k, src in enumerate((old, im)):
            bg = Image.new('RGBA', src.size, (25, 25, 35, 255)); bg.alpha_composite(src)
            cv.paste(bg.convert('RGB'), (k * (old.width + 20), 0))
        cv.save(preview)
    return im


if __name__ == '__main__':
    main(out_path=os.path.join(HERE, 'MapHelp_zh.png'),
         preview=os.path.join(HERE, '_maphelp_cmp.png'))
    print('对比图 _maphelp_cmp.png（左原 右新）')
