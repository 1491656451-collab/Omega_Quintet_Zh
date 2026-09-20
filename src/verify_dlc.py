#!/usr/bin/env python3
"""DLC 汉化包的四道闸：
   1. 回读 —— 从成品包里逐条解出来和译文比
   2. 定长字段字节宽
   3. 像素宽 —— 中文不得宽过**主包同一字段里最宽的英文**（英文是自带的，必然放得下）
   4. 字形覆盖 —— 用到的字在补过的 sysfont / advfont 里都得有
"""
import sys, os, json, re, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bra as B
from gbnl import GBNL
import build_dlc, dlc_extract, tr_dlc

W = json.load(open(os.path.join(HERE, 'work', 'fontwidth.json'), encoding='utf-8'))
CTRL = re.compile(r'#(FontColor|FontPos|Icon)\[[^\]]*\]')


def px(s, font='sysfont'):
    t = CTRL.sub('', s)
    tab = W[font] if font in W else W
    best = 0
    for line in re.split(r'\\n|\n|#n', t):
        best = max(best, sum(tab.get(ch, tab.get('A', 11)) for ch in line))
    return best


def main(orig, patched):
    NAME, STR = build_dlc.load_maps()
    do = open(orig, 'rb').read(); dp = open(patched, 'rb').read()
    _, eo = B.read_index(do); _, ep = B.read_index(dp)
    mo = {e['name']: e for e in eo}; mp = {e['name']: e for e in ep}
    # 主包每个字段最宽的英文（像素）—— 用来当上界
    b4 = json.load(open(os.path.join(HERE, 'db', 'b4_src.json'), encoding='utf-8'))
    bound = {t: max(px(v) for v in b4[t]['rows'].values()) for t in b4}
    bad = 0; nname = nstr = 0; chars = set()
    over = []
    for key in sorted(mo):
        if not key.startswith('database_en\\'):
            continue
        tab = key.split('\\')[1].replace('.gbin', '')
        bt = build_dlc.tbase(tab)
        ro, _ = B.get(do, mo[key]); rp, _ = B.get(dp, mp[key])
        go = GBNL(data=ro); gp = GBNL(data=rp)
        if go.nrows != gp.nrows or go.rowsize != gp.rowsize:
            print(f'!! {tab} 行数/行长变了'); bad += 1; continue
        # 名称
        if bt in dlc_extract.NAMEFIELD:
            off, w = dlc_extract.NAMEFIELD[bt]
            for r in range(go.nrows):
                en = ro[r*go.rowsize+off:r*go.rowsize+off+w].split(b'\x00')[0]
                try: en = en.decode('utf-8')
                except UnicodeDecodeError: continue
                if not en.strip() or en == '-': continue
                want = build_dlc.zh_name(en, bt, NAME)
                got = rp[r*gp.rowsize+off:r*gp.rowsize+off+w].split(b'\x00')[0].decode('utf-8', 'replace')
                nname += 1; chars |= set(got)
                if got != want:
                    print(f'!! {tab} {r} 名称对不上 {got!r} != {want!r}'); bad += 1
                if bt in bound and px(got) > bound[bt]:
                    over.append((tab, r, got, px(got), bound[bt]))
        # 说明
        cp = {(r, o): b for r, o, rel, b in gp.cells() if b}
        for r, o, rel, b in go.cells():
            if not b: continue
            try: en = b.decode('utf-8')
            except UnicodeDecodeError: continue
            if not en.strip() or en == '-': continue
            want = build_dlc.zh_str(en, STR)
            got = cp.get((r, o), b'').decode('utf-8', 'replace')
            nstr += 1; chars |= set(got)
            if got != want:
                print(f'!! {tab} {r}:{o} 说明对不上'); bad += 1
    print(f'回读：名称 {nname} 条 / 说明 {nstr} 条，对不上 {bad}')
    print(f'像素宽超过主包同字段英文上界的：{len(over)}')
    for o in over[:10]:
        print('   ', o)
    # 字形覆盖：从成品 System.bra 里取补过的字体
    import ffu, tempfile
    sysbra = os.path.join(HERE, 'out', 'System_r18.bra')
    if os.path.exists(sysbra):
        ds = open(sysbra, 'rb').read()
        _, es = B.read_index(ds)
        bn = {e['name']: e for e in es}
        tmp = tempfile.mkdtemp()
        cs = set(chars) - set('\n\r\t')
        for fn in ('sysfont.ffu', 'advfont.ffu'):
            raw, _ = B.get(ds, bn[f'window\\font\\{fn}'])
            pth = os.path.join(tmp, fn); open(pth, 'wb').write(raw)
            have = ffu.FFU(pth).chars()
            m = sorted(c for c in cs if c not in have)
            print(f'字形 {fn}: DLC 用到 {len(cs)} 个字符，缺 {len(m)}' + (f' {m[:10]}' if m else ''))
            bad += len(m)
    else:
        print('[跳过] 字形覆盖 —— 没找到 out/System_r18.bra')

    return bad + len(over)


if __name__ == '__main__':
    n = main('/mnt/user-data/uploads/Omega Quintet/DLC.bra',
             os.path.join(HERE, 'out', 'DLC_zh.bra'))
    print('\n>>> ' + ('DLC 校验通过' if n == 0 else f'DLC 校验失败：{n} 处'))
    sys.exit(1 if n else 0)
