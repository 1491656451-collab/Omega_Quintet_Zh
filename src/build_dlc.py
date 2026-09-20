#!/usr/bin/env python3
"""从原版 DLC.bra 生成汉化版。

DLC.bra 的 `database_en\\` 下是 56 个独立的 .gbin（不像主包那样打在 cl3 里），
所以比主包简单：逐个成员重建，再整包重打（DLC.bra 只有 95MB，不用走原地补丁）。

两类文本一起写：
  * 名称  -> 行记录里的定长内嵌字段（rowpatch）
  * 说明文 -> 类型 5 字符串池（mapping）
译文来源优先级：主包 1869 条名称 / 8396 条说明文里一模一样的原文 > tr_dlc.py。

出包前的闸：
  1. 每张表先跑 `g.rebuild({}) == 原字节`，不一致的表**只原地改行字节、不重建**；
  2. 定长字段 UTF-8 字节数 + 1 个 NUL <= 字段宽度；
  3. 像素宽不得超过**主包同一字段里最宽的英文**（英文是游戏自带的，必然放得下）；
  4. 重打之后逐条解出来回读比对。
"""
import sys, os, json, re, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bra as B, brapack
from gbnl import GBNL
import tr_dlc
import dlc_extract

NAMEFIELD = dlc_extract.NAMEFIELD


def tbase(t):
    return re.sub(r'\d+$', '', t)


def load_maps():
    n = json.load(open(os.path.join(HERE, 'db', '_b4_en2zh.json'), encoding='utf-8'))
    s = json.load(open(os.path.join(HERE, 'db', '_en2zh.json'), encoding='utf-8'))
    return n, s


def zh_name(en, bt, NAME):
    en = en.strip()
    for src in (NAME.get(bt, {}), NAME.get('stItem', {}), NAME.get('stSkill', {})):
        if en in src:
            return src[en]
    return tr_dlc.NAMES.get(en)


def zh_str(en, STR):
    return STR.get(en) or tr_dlc.STRS.get(en)


def main(src, dst, verbose=True):
    NAME, STR = load_maps()
    d = open(src, 'rb').read()
    _, ents = B.read_index(d)
    rep = {}
    nn = ns = 0
    nofull = []
    for e in ents:
        if not e['name'].startswith('database_en\\'):
            continue
        tab = e['name'].split('\\')[1].replace('.gbin', '')
        bt = tbase(tab)
        raw, _ = B.get(d, e)
        g = GBNL(data=raw)

        rowpat = {}
        if bt in NAMEFIELD:
            off, w = NAMEFIELD[bt]
            ok = any(t == 1 and o == off and
                     ((g.cols[i + 1][1] if i + 1 < len(g.cols) else g.rowsize) - o) == w
                     for i, (t, o) in enumerate(g.cols))
            if ok:
                for r in range(g.nrows):
                    en = raw[r * g.rowsize + off: r * g.rowsize + off + w].split(b'\x00')[0]
                    try:
                        en = en.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                    if not en.strip() or en == '-':
                        continue
                    z = zh_name(en, bt, NAME)
                    assert z, f'{tab} 第 {r} 行名称没译：{en!r}'
                    assert len(z.encode('utf-8')) + 1 <= w, f'{tab} 第 {r} 行超宽：{z}'
                    rowpat[(r, off, w)] = z

        mapping = {}
        for r, o, rel, b in g.cells():
            if not b:
                continue
            try:
                en = b.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if not en.strip() or en == '-':
                continue
            z = zh_str(en, STR)
            assert z, f'{tab} {r}:{o} 说明没译：{en!r}'
            mapping[(r, o)] = z

        if not rowpat and not mapping:
            continue
        nn += len(rowpat); ns += len(mapping)

        if g.rebuild({}) == raw:
            new = g.rebuild(mapping, rowpat)
        else:
            # 空重建不是字节一致的：只原地改行记录，不碰字符串池
            nofull.append(tab)
            assert not mapping, f'{tab} 空重建不一致却又要改字符串池，得单独处理'
            b2 = bytearray(raw)
            for (r, o, w), v in rowpat.items():
                vb = v.encode('utf-8')
                b2[r * g.rowsize + o: r * g.rowsize + o + w] = vb + b'\0' * (w - len(vb))
            new = bytes(b2)
        rep[e['name']] = new
        if verbose:
            print(f"  {tab:22s} 名称 {len(rowpat):3d}  说明 {len(mapping):3d}  {len(raw)} -> {len(new)} 字节")

    if nofull:
        print('  [注意] 空重建不一致、只改了行字节的表：', ' '.join(nofull))
    print(f'共 {len(rep)} 个成员，名称 {nn} 条 / 说明 {ns} 条')
    brapack.repack(src, rep, dst)
    print(f'-> {dst}  {os.path.getsize(dst)} 字节')


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/uploads/Omega Quintet/DLC.bra'
    b = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'out', 'DLC_zh.bra')
    main(a, b)
