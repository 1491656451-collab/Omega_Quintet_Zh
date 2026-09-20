#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1：把 database.cl3 的 8396 条译文回填，重打包 System.bra。

用法：
    python3 db_backfill.py <原始System.bra> <译稿目录> <输出System.bra>

流程（每一步都有硬校验，任何一步不过就直接抛异常，不会写出坏包）：
    1. 解析译稿 db_*_润色稿.md（EN/ZH 都可能跨行，必须按多行解析）
    2. 和源文逐条对齐：条数 / 主键 / EN 逐字 / 内联标记数量
    3. 只重建「有译文的那 23 张表」，其余 22 张原样拷贝
    4. 用 cl3w 重组 database.cl3
    5. **回读**：从新 CL3 里把 8396 条重新解出来，和译文逐条比对
    6. 重打包 System.bra，再从包里回读一次
"""
import sys, os, re, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bra as B, brapack, cl3w
from cl3 import CL3
from gbnl import GBNL

TARGET = 'database_en\\database.cl3'   # 只改英文版：日/韩版行数不同（6952 vs 7059），键对不上


def parse_md(path):
    """EN 续到遇见 ZH:，ZH 续到空行或下一个 ###。
       只读第一行会把 3000 条多行条目截断 —— 这个坑踩过。"""
    out, tbl, i = [], None, 0
    lines = open(path, encoding='utf-8').read().split('\n')
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('##### '):
            tbl = ln[6:].strip(); i += 1; continue
        m = re.match(r'### \[([^\]]+)\]\s*$', ln)
        if not m:
            i += 1; continue
        key = m.group(1); i += 1
        if i >= len(lines) or not lines[i].startswith('EN:'):
            continue
        en = [lines[i][4:] if lines[i].startswith('EN: ') else lines[i][3:]]; i += 1
        while i < len(lines) and not lines[i].startswith('ZH:'):
            en.append(lines[i]); i += 1
        if i >= len(lines): break
        zh = [lines[i][4:] if lines[i].startswith('ZH: ') else lines[i][3:]]; i += 1
        while i < len(lines) and lines[i].strip() != '' \
                and not lines[i].startswith('### ') and not lines[i].startswith('##### '):
            zh.append(lines[i]); i += 1
        out.append((tbl, key, '\n'.join(en), '\n'.join(zh)))
    return out


def tagcount(s):
    return (s.count('\\n'), s.count('#FontColor'), s.count('['), s.count(']'),
            s.count('{'), s.count('}'), len(re.findall(r'%[sd]', s)))


def load_and_check(zhdir, src):
    rows = []
    for f in sorted(os.listdir(zhdir)):
        if re.match(r'db_.*_润色稿\.md$', f):
            r = parse_md(os.path.join(zhdir, f))
            print(f'  {f:28s} {len(r):5d} 条')
            rows += r
    n_src = sum(len(v) for v in src.values())
    assert len(rows) == n_src, f'条数不符：译稿 {len(rows)}，源文 {n_src}'

    zh, dup = {}, []
    for t, k, e, z in rows:
        if (t, k) in zh: dup.append((t, k))
        zh[(t, k)] = (e, z)
    assert not dup, f'重复主键 {len(dup)}: {dup[:5]}'

    miss, enbad, empty, tagbad = [], [], [], []
    for t, d in src.items():
        for k, en in d.items():
            kk = (t, k)
            if kk not in zh: miss.append(kk); continue
            e2, z2 = zh[kk]
            if e2 != en: enbad.append(kk)
            if not z2.strip(): empty.append(kk)
            if tagcount(en) != tagcount(z2): tagbad.append(kk)
    assert not miss,   f'缺条 {len(miss)}: {miss[:5]}'
    assert not enbad,  f'EN 与源文不一致 {len(enbad)}: {enbad[:5]}'
    assert not empty,  f'空译文 {len(empty)}: {empty[:5]}'
    assert not tagbad, f'内联标记数量不一致 {len(tagbad)}: {tagbad[:5]}'
    print(f'  校验通过：{len(rows)} 条，缺条/重复/空译/EN差异/标记差异 全为 0')

    # 叠加修正层：术语统一 + 漏译重写 + 行数收敛（C1）+ 断行再平衡（C2）
    sys.path.insert(0, os.path.join(HERE, 'db'))
    import fix_zh
    flat_zh = {f'{t}|{k}': z for (t, k), (e, z) in zh.items()}
    flat_en = {f'{t}|{k}': e for t, d in src.items() for k, e in d.items()}
    fixed, stat = fix_zh.apply(flat_zh, flat_en)
    print(f'  修正层：术语 {stat["术语"]} 处 / 整条重写 {stat["重写"]} 条 / '
          f'行数收敛 {stat["收敛行数"]} 条（失败 {stat["收敛失败"]}）/ '
          f'断行再平衡 {stat["再平衡"]} 条（失败 {stat["再平衡失败"]}）')
    return {tuple(k.split('|', 1)): v for k, v in fixed.items()}


def main(src_bra, zhdir, out_bra):
    src = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    print('[1/6] 解析译稿')
    zh = load_and_check(zhdir, src)

    print('[2/6] 取出 database.cl3')
    d = open(src_bra, 'rb').read()
    ver, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    raw, _ = B.get(d, byname[TARGET])
    c = CL3(data=raw)
    idx = {nm.replace('.gbin', ''): i for i, (nm, _, _) in enumerate(c.files)}

    print('[3/6] 重建有译文的表（其余原样保留）')
    rep = {}
    for t in src:
        i = idx[t]
        b = c.get(i)
        g = GBNL(data=b)
        assert g.rebuild({}) == b, f'{t}: 空修改往返不一致，不能碰这张表'
        mapping = {}
        for k, en in src[t].items():
            r, o = k.split(':')
            mapping[(int(r), int(o))] = zh[(t, k)]
        nb = g.rebuild(mapping)
        rep[c.files[i][0]] = nb
        print(f'  {t:18s} {len(b):8d} -> {len(nb):8d}  ({len(mapping)} 条)')
    print(f'  改了 {len(rep)} 张，保留 {len(c.files)-len(rep)} 张')

    print('[4/6] 重组 database.cl3')
    newcl3 = cl3w.rebuild(raw, rep)
    print(f'  {len(raw)} -> {len(newcl3)} 字节')

    print('[5/6] 回读校验（从新 CL3 里重新解字符串）')
    c2 = CL3(data=newcl3)
    idx2 = {nm.replace('.gbin', ''): i for i, (nm, _, _) in enumerate(c2.files)}
    bad = 0
    for t in src:
        g = GBNL(data=c2.get(idx2[t]))
        got = {}
        for i2, o, rel, ob in g.cells():
            if ob is None: continue
            got[f'{i2}:{o}'] = GBNL.dec(ob)[0]
        for k in src[t]:
            want = zh[(t, k)]
            if got.get(k) != want:
                bad += 1
                if bad <= 5: print(f'   !! {t} {k}: 期望 {want[:40]!r} 实际 {got.get(k, None)!r}')
    assert bad == 0, f'回读不一致 {bad} 条'
    # 没被翻译的那 22 张表必须一字节没动
    for i, (nm, off, sz) in enumerate(c.files):
        if nm in rep: continue
        assert c.get(i) == c2.get(idx2[nm.replace('.gbin', '')]), f'{nm} 被动过了'
    print(f'  8396 条全部回读一致；未翻译的 {len(c.files)-len(rep)} 张表字节未变')

    print('[6/6] 重打包 System.bra')
    brapack.repack(src_bra, {TARGET: newcl3}, out_bra)
    d2 = open(out_bra, 'rb').read()
    ver2, ents2 = B.read_index(d2)
    badm = sum(1 for e in ents2 if (lambda o: o is None or len(o) != e['usz'])(B.get(d2, e)[0]))
    assert badm == 0, f'{badm} 个成员解不出来'
    r2, _ = B.get(d2, {e['name']: e for e in ents2}[TARGET])
    assert r2 == newcl3, '从包里读回来的 CL3 和写进去的不一致'
    print(f'  成员 {len(ents2)}，解包失败 0，CL3 回读一致')
    print(f'\n完成 -> {out_bra}  {os.path.getsize(out_bra)} 字节')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
