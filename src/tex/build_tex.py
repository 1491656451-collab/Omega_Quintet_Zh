# -*- coding: utf-8 -*-
"""通用贴图汉化构建器。

映射表 M 的值：
  None / 缺项          -> 该框不动
  "中文"               -> 整框替换
  ["中","文",...]      -> 框内自动切成同样数量的子框，逐个替换（空串=该子框不动）
  {"parts":[...],      -> 按「每个标签占几个词」切分，处理词组标签
   "counts":[3,3,1,1]}
"""
import os, json, importlib
from collections import defaultdict
import numpy as np
from scipy import ndimage
from PIL import Image
from detect3 import detect3
from subcut import cut_to_n, cut_groups
from autostyle import sample
from render3 import draw, fit_size, fit_each

HERE = os.path.dirname(os.path.abspath(__file__))


def inpaint_shift(px, mask, x0, x1):
    """从同样的行、横向平移一段距离的地方把底图抄过来补洞。
       平移量用「遮罩外的像素对得最齐」来自动选 —— 光条的网点、
       高光线、斜切边都能原样接上，比线性插值那种平涂自然。
       返回 None 表示没找到够好的来源。"""
    H, W = mask.shape
    free = ~mask
    if free.sum() < 50:
        return None
    ref = px[:, :, :3].astype(np.int32)
    w = x1 - x0
    best, bestd = None, 1e18
    for dx in list(range(w + 6, w + 260, 2)) + list(range(-(w + 6), -(w + 260), -2)):
        if x0 + dx < 0 or x1 + dx > W:
            continue
        src = np.roll(ref, -dx, axis=1)
        srcmask = np.roll(mask, -dx, axis=1)
        ok = free & ~srcmask
        if ok.sum() < free.sum() * 0.5:
            continue
        d = np.abs(src[ok] - ref[ok]).mean()
        if d < bestd:
            bestd, best = d, dx
    if best is None or bestd > 14:
        return None
    out = px.copy()
    out[mask] = np.roll(px, -best, axis=1)[mask]
    return out


def inpaint_local(px, mask, iters=60):
    """由外向内一层层填：每轮把「周围已知像素够多」的遮罩像素用邻域均值补上。
       文字笔画只有四五像素宽，几轮就填满，补出来的颜色跟就近的底图一致，
       不会像长距离线性插值那样抹出一条横带。"""
    out = px.astype(np.float64).copy()
    m = mask.copy()
    k = np.ones((3, 3))
    for _ in range(iters):
        if not m.any():
            break
        known = (~m).astype(np.float64)
        cnt = ndimage.convolve(known, k, mode='nearest')
        front = m & (cnt >= 3)
        if not front.any():
            front = m & (cnt >= 1)
        if not front.any():
            break
        for c in range(out.shape[2]):
            sm = ndimage.convolve(out[:, :, c] * known, k, mode='nearest')
            vals = sm[front] / np.maximum(cnt[front], 1)
            out[:, :, c][front] = vals
        m[front] = False
    return out.round().clip(0, 255).astype(np.uint8)


def inpaint_rows(px, mask):
    """只把 mask 标的像素补掉：逐行在遮罩缺口的左右两侧做线性插值。
       光条/面板基本是横向连续的，这样补完底图的结构（斜切、高光线）能保住，
       比「整块平涂」或「从旁边平铺一段」自然得多。"""
    H, W = mask.shape
    out = px.copy()
    for y in range(H):
        row = mask[y]
        if not row.any():
            continue
        x = 0
        while x < W:
            if not row[x]:
                x += 1; continue
            e = x
            while e < W and row[e]:
                e += 1
            L = x - 1
            R = e
            if L < 0 and R >= W:
                x = e; continue
            if L < 0:
                out[y, x:e] = px[y, R]
            elif R >= W:
                out[y, x:e] = px[y, L]
            else:
                a = px[y, L].astype(float); b = px[y, R].astype(float)
                n = e - x
                for k in range(n):
                    f = (k + 1) / (n + 1)
                    out[y, x + k] = (a * (1 - f) + b * f).round()
            x = e
    return out


def chroma_mask(arr, box=None, ch=80, alpha=150):
    """按彩度取「文字」像素：按钮底板是暗蓝、边框是低彩度的亮灰，
       只有文字本身是高彩度，所以能把字从底板里抠出来。"""
    s = arr if box is None else arr[box[1]:box[3], box[0]:box[2]]
    s = s.astype(int)
    c = s[:, :, :3].max(axis=2) - s[:, :, :3].min(axis=2)
    return (c > ch) & (s[:, :, 3] > alpha)


def collect(src_png, M, det_kw=None, align=None):
    atlas = Image.open(src_png).convert('RGBA')
    arr = np.array(atlas)
    a = arr[:, :, 3] > 128
    boxes = detect3(src_png, **(det_kw or {}))
    items, bad = [], []
    for i, b in enumerate(boxes):
        v = M.get(i)
        if not v:
            continue
        pad = 5
        if isinstance(v, str):
            parts, subs = [v], [b]
        elif isinstance(v, dict) and v.get('abs'):
            # 直接给绝对坐标的子框（用于压在条状底图上的美术字）
            pad = 3
            parts = [t for t, _ in v['abs']]
            rects = [list(q) for _, q in v['abs']]
            tight = [list(q) for q in rects]
            # 手写的矩形只用来「擦」，绘制范围必须收到框内英文墨迹的真实包围盒，
            # 不然中文会画到游戏那个 quad 的外面去（合计奖励被截顶就是这么来的）
            L = v.get('L', 200)
            subs = []
            for q in rects:
                sl = arr[q[1]:q[3], q[0]:q[2]]
                mm = (sl[:, :, :3].astype(int).mean(axis=2) > L) & (sl[:, :, 3] > 150)
                if mm.any():
                    yy, xx = np.nonzero(mm)
                    subs.append([q[0] + int(xx.min()), q[1] + int(yy.min()),
                                 q[0] + int(xx.max()) + 1, q[1] + int(yy.max()) + 1])
                else:
                    subs.append(list(q))
            # 同一个 abs 条目里的几个标签本来就是同一排（共用基线），
            # 竖直范围取并集，免得没有下伸部的那个被裁掉底。
            if len(subs) > 1 and v.get('union', True):
                ty = min(q[1] for q in subs); by = max(q[3] for q in subs)
                subs = [[q[0], ty, q[2], by] for q in subs]
        elif isinstance(v, dict) and v.get('chroma'):
            # 按钮底板里的文字：用彩度掩膜代替 alpha 掩膜
            pad = 2
            m = np.zeros(a.shape, bool)
            m[b[1]:b[3], b[0]:b[2]] = chroma_mask(arr, b, **v.get('ck', {}))
            parts = v['parts'] if isinstance(v.get('parts'), list) else [v['chroma']]
            if len(parts) > 1:
                subs = (cut_groups(m, b, v['counts']) if 'counts' in v
                        else cut_to_n(m, b, len(parts)))
            else:
                ys, xs = np.nonzero(m)
                subs = [[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]] if len(xs) else None
            # 汉字比拉丁字母更吃分辨率：绘制用的竖直框放宽到底板内高（留 3px），
            # 但「擦字」仍按原文字的紧框来，否则会擦到底板的高光边。
            if subs:
                lo, hi2 = b[1] + 3, b[3] - 3
                tight = [list(q) for q in subs]
                subs = [[q[0], min(q[1], max(lo, q[1] - 3)), q[2], max(q[3], min(hi2, q[3] + 3))]
                        for q in subs]
        elif isinstance(v, dict):
            parts = v['parts']
            subs = cut_groups(a, b, v['counts'])
        else:
            parts = list(v)
            subs = cut_to_n(a, b, len(parts))
        if not subs or len(subs) != len(parts):
            bad.append((i, len(parts), len(subs) if subs else 0)); continue
        for j2, (t, bb) in enumerate(zip(parts, subs)):
            if not t: continue
            _st = sample(arr, bb)
            if pad in (2, 3):
                _st['glow'] = None
                _st['grow'] = v.get('grow', 4) if isinstance(v, dict) else 4
                if isinstance(v, dict) and v.get('style'):
                    _st.update(v['style'])
                if isinstance(v, dict) and v.get('size'):
                    _st['fixed_size'] = v['size']
                if isinstance(v, dict) and v.get('align'):
                    _st['align'] = v['align']
            _st = dict(_st); _st['_box'] = i
            if align and align.get(i):
                _st['align'] = align[i]
            items.append([t, list(bb), _st, pad, (list(b) if pad in (2, 3) else None), (tight[j2] if pad in (2, 3) else None)])
    # 检测框用的是 alpha>128，原标签的外发光在框外还有几像素 ——
    # 游戏里那圈发光是显示出来的，说明它的 quad 比这个紧框大。
    # 所以把框向外扩到「还有像素(alpha>8)」的范围，字号能多给六到十号，
    # 但不许扩到相邻检测框里去。
    soft = arr[:, :, 3] > 8
    tights = [tuple(q) for q in boxes]
    for it in items:
        if it[4]:            # 底板/光条上的字不扩
            continue
        x0, y0, x1, y1 = it[1]
        lim = [x0, y0, x1, y1]
        for side in range(4):
            for step in range(4):
                c = list(lim)
                c[side] += -1 if side < 2 else 1
                if c[1] < 0 or c[0] < 0 or c[3] > arr.shape[0] or c[2] > arr.shape[1]:
                    break
                # 扩出去的那一条如果已经没有像素了，就没必要再扩
                hit = any(not (q[2] <= c[0] or q[0] >= c[2] or q[3] <= c[1] or q[1] >= c[3])
                          for q in tights if not (q[0] <= x0 and q[1] <= y0 and q[2] >= x1 and q[3] >= y1))
                if hit:
                    break
                strip = (soft[c[1]:lim[1], c[0]:c[2]] if side == 1 else
                         soft[lim[3]:c[3], c[0]:c[2]] if side == 3 else
                         soft[c[1]:c[3], c[0]:lim[0]] if side == 0 else
                         soft[c[1]:c[3], lim[2]:c[2]])
                if strip.size and not strip.any():
                    break
                lim = c
        it[1] = lim
    return atlas, arr, boxes, items, bad


def build(src_png, mapmod, out_png, row_q=22, h_q=8, det_kw=None, min_squeeze=0.60,
          x_split=None):
    mod = importlib.import_module(mapmod)
    M = mod.M
    # 竖排/横排的一列标签，游戏里是左对齐的（美术图里它们的左边缘就对齐在一起）。
    # 居中放中文的话，字少的那条会整体右移 —— 战斗指令表和「状态/属性/状态异常/地点」
    # 那一排都是这么歪的。ALIGN 指定哪些框要左对齐。
    atlas, arr, boxes, items, bad = collect(src_png, M, det_kw, getattr(mod, 'ALIGN', None))
    for i, want, got in bad:
        print(f'  !! 框 {i}: 需要 {want} 段，切出 {got} 段 —— 已跳过')

    # 只按「行」分组：同一行共用字号与竖直框。
    # 行的判定用框中心，避免带下伸部的框被分到下一行。
    ys = sorted(set((b[1] + b[3]) // 2 for _, b, _, _, _, _ in items))
    rows = []
    for y in ys:
        if rows and y - rows[-1][-1] <= row_q: rows[-1].append(y)
        else: rows.append([y])
    rowof = {y: i for i, r in enumerate(rows) for y in r}
    # 同一行里还要按「上边缘 y0」再分一次组。y0 差得多说明压根不是同一排
    # （比如 grSystemResult 里 x=675 的「奖励」和 x=58 的「合计奖励」，
    #  中心 y 只差 11px 会被并成一组，但它们根本不在同一个界面上）。
    # 同一行里横向离得很远的标签往往根本不在同一个界面上（战斗图左边是指令表、
    # 右边是弹出字），并成一组会被最矮的那个框把字号压小。x_split 给出分区边界。
    def region(x):
        if not x_split:
            return 0
        return sum(1 for q in x_split if x >= q)
    pre = defaultdict(list)
    for k, (t, bb, st, _p, _pl, _tg) in enumerate(items):
        pre[(rowof[(bb[1] + bb[3]) // 2], region(bb[0]))].append(k)
    grp = defaultdict(list)
    for r, ids in pre.items():
        for k in sorted(ids, key=lambda i: items[i][1][1]):
            y0 = items[k][1][1]
            placed = False
            for key in list(grp):
                if key[0] == r and abs(key[1] - y0) <= 6:
                    grp[key].append(k); placed = True; break
            if not placed:
                grp[(r, y0)].append(k)

    sizes = {}; frame = {}; gl_of = {}
    for key, ids in grp.items():
        # 字号：每个标签按自己的框各算一个上限，全组取最小 —— 全组同号，
        # 又保证谁都画得进自己的框。竖直位置按各自的框居中
        # （同一排的框只差一个下伸部，居中偏移 2~3px，看不出来；
        #  用交集框强行对齐基线的话字号要小三四号，得不偿失）。
        ew = max(items[i][2]['ew'] for i in ids)
        gl = any(items[i][2]['glow'] for i in ids)
        S = fit_each([items[i][0] for i in ids],
                     [items[i][1][2] - items[i][1][0] for i in ids],
                     [items[i][1][3] - items[i][1][1] for i in ids],
                     ew, min_squeeze=min_squeeze, glow=gl)
        sizes[key] = S
        for i in ids:
            si = items[i][2].get('fixed_size', S)
            frame[i] = (items[i][1][1], items[i][1][3], si, ew); gl_of[i] = gl

    # ONE_SIZE：指定「这几个框必须同一个字号」。
    # 战斗指令表的金色（选中）那一列在美术图里本来就比灰色那列大一号，
    # 换成汉字之后这个差别特别扎眼 —— 全组取最小值压成一样大。
    for one in getattr(mod, 'ONE_SIZE', []):
        ids = [k for k, it in enumerate(items) if it[2].get('_box') in set(one)]
        if not ids:
            continue
        S1 = min(frame[k][2] for k in ids)
        for k in ids:
            t0, b0, _s, ew0 = frame[k]
            frame[k] = (t0, b0, S1, ew0)
        print(f'  ONE_SIZE: {len(ids)} 个标签统一字号 {S1}')

    # 原标签的外发光会超出「alpha>128」的检测框，只清紧框会留下一圈光晕，
    # 所以按放大 M 像素清；同时把保留不动的框挖回来，别擦到它们。
    keep = np.zeros(arr.shape[:2], bool)
    for i, b in enumerate(boxes):
        if M.get(i): continue
        keep[max(0, b[1]-1):b[3]+1, max(0, b[0]-1):b[2]+1] = True
    # 原标签的外发光会超出「alpha>128」的检测框，但擦一个放大的矩形会波及邻居。
    # 改成：在框外扩 p 像素的范围里，只擦「本来就有像素（alpha>8）」的地方。
    ink = arr[:, :, 3] > 8
    clr = np.zeros(arr.shape[:2], bool)
    for t, bb, st, p, pl, tg in items:
        if pl: continue
        x0, y0, x1, y1 = bb
        reg = np.zeros(arr.shape[:2], bool)
        reg[max(0, y0-p):y1+p, max(0, x0-p):x1+p] = True
        clr |= reg & ink
        clr[y0:y1, x0:x1] = True
    clr &= ~keep
    px = np.array(atlas)
    px[clr] = (0, 0, 0, 0)
    for t, bb, st, p, pl, tg in items:
        if not pl: continue
        x0, y0, x1, y1 = tg
        # 底图上的字：先按「亮度/彩度」把字本身挑出来，再逐行插值补掉，
        # 底板的渐变、斜切、高光线都原样留着。
        R = 6
        gx0, gy0 = max(0, x0 - R), max(0, y0 - R)
        gx1, gy1 = min(px.shape[1], x1 + R), min(px.shape[0], y1 + R)
        reg = px[gy0:gy1, gx0:gx1]
        lum = reg[:, :, :3].astype(int).mean(axis=2)
        chrm = reg[:, :, :3].astype(int).max(axis=2) - reg[:, :, :3].astype(int).min(axis=2)
        m = np.zeros(reg.shape[:2], bool)
        inner = (slice(y0 - gy0, y1 - gy0), slice(x0 - gx0, x1 - gx0))
        if p == 2:
            m[inner] = chrm[inner] > 80
        else:
            m[inner] = lum[inner] > 165
        # 亮的是字芯，字外面还有一圈深色描边，不一起算进遮罩的话
        # 补背景时会把描边的深色抹开，留下一团脏斑。多膨胀几轮把描边吃掉。
        m = ndimage.binary_dilation(m, np.ones((3, 3), bool), iterations=st.get('grow', 4))
        m[:, :x0 - gx0] = False; m[:, x1 - gx0:] = False
        m[:y0 - gy0, :] = False; m[y1 - gy0:, :] = False
        px[gy0:gy1, gx0:gx1] = inpaint_local(reg, m)
    atlas = Image.fromarray(px, 'RGBA')

    over = []
    for k, (t, bb, st, _p, _pl, _tg) in enumerate(items):
        x0, y0, x1, y1 = bb
        top, bot, S, ew = frame[k]
        st = dict(st); st['ew'] = ew
        lab = draw(t, S, st, x1 - x0)
        ox = (x0 if st.get('align') == 'left' else
              x1 - lab.width if st.get('align') == 'right' else
              x0 + ((x1 - x0) - lab.width) // 2)
        oy = top + ((bot - top) - lab.height) // 2
        # 硬裁：不管字号算得对不对，一个像素都不许画到自己的框外面
        cx0, cy0 = max(ox, x0), max(oy, y0)
        cx1, cy1 = min(ox + lab.width, x1), min(oy + lab.height, y1)
        if cx1 > cx0 and cy1 > cy0:
            atlas.alpha_composite(lab.crop((cx0-ox, cy0-oy, cx1-ox, cy1-oy)), (cx0, cy0))
        d = lab.height - (bot - top) - (4 if st.get('glow') else 0)
        if d > 2: over.append((t, d))
    atlas.save(out_png)
    sv = list(sizes.values())
    print(f'{os.path.basename(out_png)}: {len(items)} 标签 / {len(grp)} 组 / '
          f'字号 {min(sv)}~{max(sv)} / 超框 {len(over)}')
    if over: print('  超框:', over[:12])
    return items
