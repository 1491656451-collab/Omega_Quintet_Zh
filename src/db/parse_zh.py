# -*- coding: utf-8 -*-
"""解析另一个 agent 的润色稿，独立校验一遍（不看它自己的校验报告）。"""
import re, json, glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(os.path.join(HERE, 'db_src.json'), encoding='utf-8'))
# 源文按「表 -> 行号:列偏移 -> 英文」；拍平成 key -> (表, 英文)
flat = {}
for tbl, d in SRC.items():
    for k, en in d.items():
        flat.setdefault(k, []).append((tbl, en))


def parse(path):
    """EN / ZH 都可能跨行（源文里是真换行符）。
       EN 续到遇见 ZH: 为止；ZH 续到空行或下一个 ### 为止。
       —— 只读第一行会把 3000 条多行条目截断，回填进去就是灾难。"""
    out = []
    lines = open(path, encoding='utf-8').read().split('\n')
    tbl = None
    i = 0
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
        en = [lines[i][4:] if lines[i].startswith('EN: ') else lines[i][3:]]
        i += 1
        while i < len(lines) and not lines[i].startswith('ZH:'):
            en.append(lines[i]); i += 1
        if i >= len(lines):
            break
        zh = [lines[i][4:] if lines[i].startswith('ZH: ') else lines[i][3:]]
        i += 1
        while i < len(lines) and lines[i].strip() != '' \
                and not lines[i].startswith('### ') and not lines[i].startswith('##### '):
            zh.append(lines[i]); i += 1
        out.append((tbl, key, '\n'.join(en), '\n'.join(zh)))
    return out


def main():
    rows = []
    for f in sorted(glob.glob('/mnt/user-data/uploads/欧米伽五重奏/db_*_润色稿.md')):
        r = parse(f)
        print(f'{os.path.basename(f):28s} {len(r):5d} 条')
        rows += r
    print(f'--- 合计 {len(rows)} 条，源文 {sum(len(v) for v in SRC.values())} 条')

    keys = {}
    dup = []
    for tbl, k, en, zh in rows:
        kk = (tbl, k)
        if kk in keys: dup.append(kk)
        keys[kk] = (en, zh)
    print(f'重复主键 {len(dup)}', dup[:5])

    # 逐条对齐：源文的每个 (表,key) 都要有译文，且 EN 要一字不差
    miss, enbad, empty = [], [], []
    for tbl, d in SRC.items():
        for k, en in d.items():
            kk = (tbl, k)
            if kk not in keys: miss.append(kk); continue
            e2, z2 = keys[kk]
            if e2 != en: enbad.append((kk, en, e2))
            if not z2 or not z2.strip(): empty.append(kk)
    extra = [kk for kk in keys if kk[0] not in SRC or kk[1] not in SRC.get(kk[0], {})]
    print(f'缺条 {len(miss)}  EN 不一致 {len(enbad)}  空译文 {len(empty)}  多余条目 {len(extra)}')
    for x in miss[:5]: print('   缺:', x)
    for x in enbad[:3]: print('   EN差异:', x[0], repr(x[1][:60]), '->', repr(x[2][:60]))
    for x in extra[:5]: print('   多余:', x)

    # 内联标记完整性
    def counts(s):
        return (s.count('\\n'), s.count('#FontColor'), s.count('['), s.count(']'),
                s.count('{'), s.count('}'), len(re.findall(r'%[sd]', s)))
    tagbad = []
    for tbl, k, en, zh in rows:
        if counts(en) != counts(zh):
            tagbad.append(((tbl, k), counts(en), counts(zh)))
    print(f'内联标记数量不一致 {len(tagbad)}')
    for x in tagbad[:8]: print('   ', x)

    json.dump({f'{t}|{k}': z for t, k, e, z in rows},
              open(os.path.join(HERE, 'db_zh.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    print('已导出 db/db_zh.json')


if __name__ == '__main__':
    main()
