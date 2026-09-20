# -*- coding: utf-8 -*-
"""压在底板/光条上的贴图标签，逐条替换。

通用擦除器（build_tex 的 inpaint 分支）在这类标签上不好使 ——
底板本身就是亮的，亮度掩膜会把底板一起吃掉，糊成一片。
这里用三种确定性的擦法，每种都能自检：

  clear —— 背景本来就是透明的，直接把矩形清零
  rows  —— 只补「文字掩膜」标中的像素，逐行在缺口左右线性插值。
           底板的高光、网点、渐变原样保留，插值跨度只有几个像素
  prof  —— 底板 = 竖直剖面 + 横向剖面，整块重建（文字几乎占满整条时用）

落笔一律裁在 draw 矩形内，一个像素都不许画到外面（UV 约束）。
"""
import os, sys
import numpy as np
from scipy import ndimage
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render3 import draw as render_label, fit_size
from autostyle import sample as sample_style


def premul(a):
    f = a.astype(np.float64)
    f[:, :, :3] *= f[:, :, 3:4] / 255.0
    return f


def unpremul(f):
    out = f.copy()
    al = np.clip(out[:, :, 3:4], 0, 255)
    with np.errstate(divide='ignore', invalid='ignore'):
        rgb = np.where(al > 0, out[:, :, :3] * 255.0 / np.maximum(al, 1e-6), 0)
    out[:, :, :3] = rgb
    return out.round().clip(0, 255).astype(np.uint8)


def bg_of(a, rect):
    """矩形内背景的估计：逐行在左右两侧线性插值（预乘 RGBA）。"""
    x0, y0, x1, y1 = rect
    f = premul(a[y0:y1, x0 - 1:x1 + 1].astype(np.uint8))
    n = x1 - x0
    t = np.linspace(0, 1, n + 2)[1:-1][None, :, None]
    L = f[:, :1, :]; R = f[:, -1:, :]
    f[:, 1:-1, :] = L * (1 - t) + R * t
    return unpremul(f)[:, 1:-1, :]


def textmask(a, job, core_only=False):
    """框内「文字」的掩膜。

    分两层抓：
      1. 字芯 —— 按亮度 / 彩度 / 金色阈值挑出来；
         整行都命中的行是底板自己的高光线（光条上下沿那两条白线），不是字，剔掉，
         而且**膨胀之后还要再剔一次**，否则高光线会被当成字一起补掉，
         补出来就是一条横贯的亮带（第一版那个「白药丸」就是这么来的）。
      2. 描边和外发光 —— 只在字芯周围 grow 圈之内，按「和本行背景差得远」来抓。
         本行背景 = 该行落在这一圈之外的像素的中位数。
         这样深色描边、半透明发光都能吃掉，又不会把底板整片圈进来。
    """
    x0, y0, x1, y1 = job['erase']
    s = a[y0:y1, x0:x1].astype(int)
    lum = s[:, :, :3].mean(axis=2)
    chrm = s[:, :, :3].max(axis=2) - s[:, :, :3].min(axis=2)
    k = job.get('mask', {})
    mode = k.get('mode', 'lum')
    if mode == 'lum':
        core = lum > k.get('thr', 150)
    elif mode == 'chroma':
        core = chrm > k.get('thr', 70)
    elif mode == 'gold':
        core = (s[:, :, 0] > k.get('thr', 140)) & ((s[:, :, 0] - s[:, :, 2]) > 55)
    else:
        raise SystemExit('未知掩膜模式 ' + mode)
    core &= s[:, :, 3] > 40
    band = core.mean(axis=1) > 0.85          # 底板高光线所在的行
    core[band] = False
    if core_only:
        return core
    g = int(k.get('grow', 4))
    near = ndimage.binary_dilation(core, np.ones((3, 3), bool), iterations=g) if g else core.copy()
    near[band] = False
    out = core.copy()
    for y in range(s.shape[0]):
        if band[y] or not near[y].any():
            continue
        free = ~near[y]
        if free.sum() < 6:
            continue
        ref = np.median(s[y][free], axis=0)
        d = np.abs(s[y] - ref[None, :]).sum(axis=1)
        out[y] = near[y] & (d > k.get('edge', 70))
    out |= core
    out = ndimage.binary_dilation(out, np.ones((3, 3), bool), iterations=1)
    out[band] = False
    out[:, :1] = False; out[:, -1:] = False   # 贴边的一列留给插值当锚点
    return out


def text_style(orig, job):
    """只按「文字掩膜」采样样式。
       autostyle.sample 默认拿 alpha>200 当实心区 —— 在底板上那等于把整块底板
       当成了文字，采出来的填充色是底板色，字画出去就是一片灰蓝。"""
    x0, y0, x1, y1 = job['erase']
    m = textmask(orig, job, core_only=True)
    fake = np.zeros_like(orig[y0:y1, x0:x1])
    fake[:, :, :3] = orig[y0:y1, x0:x1, :3]
    fake[:, :, 3] = np.where(m, 255, 0)
    return sample_style(fake, (0, 0, x1 - x0, y1 - y0))


def blockfill(a, job):
    """底板重建：左右各取一块「干净」的列区，逐行取中位数，再按 x 线性过渡。

    比「从紧邻的一列插值」稳得多 —— 单列很容易正好落在外发光上，
    一条脏像素会被拉成一整条横带（第一版那条白药丸就是这么来的）。
    两块都给的时候能还原横向渐变；只给一块就是逐行常量填充（底板横向均匀时正确）。
    """
    x0, y0, x1, y1 = job['erase']
    L = job.get('left'); R = job.get('right')
    assert L or R, job['tag']
    def med(blk):
        c = a[y0:y1, blk[0]:blk[1]].astype(float)
        sd = c.std(axis=1).max()
        if sd > job.get('sdmax', 30):
            raise SystemExit(f"{job['tag']}: 取样块 {blk} 不干净（行内标准差 {sd:.1f}）")
        return np.median(c, axis=1)
    ml = med(L) if L else None
    mr = med(R) if R else None
    if ml is None: ml = mr
    if mr is None: mr = ml
    t = np.linspace(0, 1, x1 - x0)[None, :, None]
    fill = ml[:, None, :] * (1 - t) + mr[:, None, :] * t
    a[y0:y1, x0:x1] = fill.round().clip(0, 255).astype(np.uint8)
    # 自检：填出来的边缘要和框外紧邻的像素对得上
    bad = []
    for k, y in enumerate(range(y0, y1)):
        for xin, xout in ((x0, x0 - 2), (x1 - 1, x1 + 1)):
            if not (0 <= xout < a.shape[1]):
                continue
            i = a[y, xin].astype(int); o = a[y, xout].astype(int)
            if abs(i[3] - o[3]) > 24 or np.abs(i[:3] - o[:3]).sum() > job.get('tol', 90):
                bad.append((y, xout, tuple(i), tuple(o)))
    if len(bad) > job.get('badmax', 4):
        raise SystemExit(f"{job['tag']}: 底板重建和框外对不上 {len(bad)} 行，例 {bad[:3]}")


def proffill(a, job):
    """底板重建（可分离模型）：底板 = 竖直剖面 + 横向剖面。

      竖直剖面 v(y)：从一段干净的列（vcols）逐行取中位数 —— 光条的上下渐变、
                    中间那条高光带都带着。
      横向剖面 h(x)：从文字上下方几行干净的行（hrows）逐列取中位数 ——
                    光条左右的明暗差、圆角端的收边都带着。
      fill(y,x) = v(y) + (h(x) − h̄)，h̄ 是 h 在 vcols 那几列上的均值。

    比「左右两块线性过渡」准：这条光条从 x≈30 到 150 基本是平的，
    150 往右才慢慢提亮，线性过渡会把中段整体提亮一截。
    """
    x0, y0, x1, y1 = job['erase']
    cx0, cx1 = job['vcols']
    v = np.median(a[y0:y1, cx0:cx1].astype(float), axis=1)          # (H,4)
    hs = [np.median(a[r0:r1, x0:x1].astype(float), axis=0) for r0, r1 in job['hrows']]
    h = np.mean(hs, axis=0)                                          # (W,4)
    hbar = np.median(np.concatenate([np.median(a[r0:r1, cx0:cx1].astype(float), axis=0)
                                     for r0, r1 in job['hrows']], axis=0).reshape(-1, 4), axis=0)
    fill = v[:, None, :] + (h[None, :, :] - hbar[None, None, :])
    a[y0:y1, x0:x1] = fill.round().clip(0, 255).astype(np.uint8)
    bad = []
    for y in range(y0, y1):
        for xin, xout in ((x0, x0 - 2), (x1 - 1, x1 + 1)):
            if not (0 <= xout < a.shape[1]):
                continue
            i = a[y, xin].astype(int); o = a[y, xout].astype(int)
            if abs(i[3] - o[3]) > 24 or np.abs(i[:3] - o[:3]).sum() > job.get('tol', 80):
                bad.append((y, xout, tuple(i), tuple(o)))
    if len(bad) > job.get('badmax', 3):
        raise SystemExit(f"{job['tag']}: 底板重建和框外对不上 {len(bad)} 处，例 {bad[:3]}")


def erase(a, job):
    x0, y0, x1, y1 = job['erase']
    if job['mode'] == 'prof':
        proffill(a, job)
        return
    if job['mode'] == 'clear':
        a[y0:y1, x0:x1] = 0
        return
    if job['mode'] == 'block':
        blockfill(a, job)
        return
    # rows：只补「文字掩膜」标中的像素，逐行在缺口左右做线性插值。
    # 整块重填会把底板的高光、网点、渐变一起抹平；只补笔画缺口，
    # 背景结构原样保留，插值跨度只有几个像素，误差看不出来。
    m = textmask(a, job)
    reg = a[y0:y1, x0:x1]
    f = premul(reg)
    H, W = m.shape
    for y in range(H):
        row = m[y]
        if not row.any():
            continue
        x = 0
        while x < W:
            if not row[x]:
                x += 1; continue
            e = x
            while e < W and row[e]:
                e += 1
            L, R = x - 1, e
            if L < 0 and R >= W:
                x = e; continue
            if L < 0:
                f[y, x:e] = f[y, R]
            elif R >= W:
                f[y, x:e] = f[y, L]
            else:
                aL, aR = f[y, L].copy(), f[y, R].copy()
                n = e - x
                for kk in range(n):
                    t = (kk + 1) / (n + 1)
                    f[y, x + kk] = aL * (1 - t) + aR * t
            x = e
    a[y0:y1, x0:x1] = unpremul(f)


def run(src, JOBS, base=None, out_path=None, preview=None):
    im = Image.open(base or src).convert('RGBA')
    orig = np.array(Image.open(src).convert('RGBA'))
    a = np.array(im)
    styles = {}
    for job in JOBS:
        styles[job['tag']] = (text_style(orig, job)
                              if job['mode'] != 'clear'
                              else sample_style(orig, job['erase']))
    before = a.copy()
    for job in JOBS:
        erase(a, job)
    # 自检：字芯像素必须都被改掉了（底板本来就不该变，所以不能拿整框比）
    for job in JOBS:
        x0, y0, x1, y1 = job['erase']
        if job['mode'] == 'clear':
            core = orig[y0:y1, x0:x1, 3] > 150
        else:
            core = textmask(orig, job, core_only=True)
        if core.sum() < 20:
            raise SystemExit(f"{job['tag']}: 掩膜没抓到字（{core.sum()} 个像素），阈值要调")
        d = (np.abs(a[y0:y1, x0:x1].astype(int) - orig[y0:y1, x0:x1].astype(int)).sum(axis=2) > 24)
        hit = (core & d).sum() / core.sum()
        if hit < 0.80:
            raise SystemExit(f"{job['tag']}: 擦除没盖住原文（只改掉了 {hit:.0%} 的字芯）")

    im = Image.fromarray(a, 'RGBA')
    for job in JOBS:
        dx0, dy0, dx1, dy1 = job['draw']
        st = dict(styles[job['tag']])
        st['ew'] = max(1, min(st['ew'], 3))
        S = job.get('size') or fit_size([job['zh']], [dx1 - dx0], dy1 - dy0,
                                        st['ew'], min_squeeze=0.72, glow=bool(st['glow']))
        lab = render_label(job['zh'], S, st, dx1 - dx0)
        al = job.get('align', 'center')
        ox = (dx0 if al == 'left' else
              dx1 - lab.width if al == 'right' else
              dx0 + ((dx1 - dx0) - lab.width) // 2)
        oy = dy0 + ((dy1 - dy0) - lab.height) // 2
        cx0, cy0 = max(ox, dx0), max(oy, dy0)
        cx1, cy1 = min(ox + lab.width, dx1), min(oy + lab.height, dy1)
        if cx1 <= cx0 or cy1 <= cy0:
            raise SystemExit(f"{job['tag']}: 落笔矩形太小")
        im.alpha_composite(lab.crop((cx0 - ox, cy0 - oy, cx1 - ox, cy1 - oy)), (cx0, cy0))
        print(f"  {job['tag']:26s} -> {job['zh']:8s} 字号 {S:3d} 标签 {lab.size} @ {(cx0, cy0)}")

    if out_path:
        im.save(out_path)
    if preview:
        rows = []
        for job in JOBS:
            x0, y0, x1, y1 = job['erase']
            p = 10
            box = (max(0, x0 - p), max(0, y0 - p), x1 + p, y1 + p)
            for src_im in (Image.fromarray(before, 'RGBA'), im):
                c = src_im.crop(box)
                bg = Image.new('RGBA', c.size, (34, 34, 42, 255)); bg.alpha_composite(c)
                rows.append(bg.convert('RGB'))
        S = 2
        W = max(r.width for r in rows) * S
        H = sum(r.height for r in rows) * S + 6 * len(rows)
        cv = Image.new('RGB', (W, H), (0, 0, 0)); y = 0
        for r in rows:
            q = r.resize((r.width * S, r.height * S), Image.NEAREST)
            cv.paste(q, (0, y)); y += q.height + 6
        cv.save(preview)
    return im


