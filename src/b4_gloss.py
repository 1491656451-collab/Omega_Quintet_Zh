# -*- coding: utf-8 -*-
"""从已译好的 8396 条说明文里，挖出「英文名 -> 中文名」的既成译法。

唱片/技能说明里大量出现 `Learn Mic Skill [Stecca Staccato]` 这种带方括号的
专名，译文里也在同样的位置带方括号。按位置配对就能白捡一份术语表，
B4 的名称字段直接沿用，天然和说明文一致。
"""
import json, os, re, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'db'))
import fix_zh

BR = re.compile(r'\[([^\[\]]{2,40})\]|\{([^{}]{1,40})\}')


def toks(s):
    return [(m.group(1) or m.group(2)) for m in BR.finditer(s)]


def build():
    src = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    zh0 = json.load(open(os.path.join(HERE, 'db', 'db_zh.json'), encoding='utf-8'))
    enm = {f'{t}|{k}': v for t, d in src.items() for k, v in d.items()}
    zh, _ = fix_zh.apply(zh0, enm)
    votes = defaultdict(Counter)
    for k, e in enm.items():
        z = zh.get(k)
        if not z: continue
        te, tz = toks(e), toks(z)
        if len(te) != len(tz) or not te: continue
        for a, b in zip(te, tz):
            a = a.strip(); b = b.strip()
            if not a or not b: continue
            if not re.search(r'[A-Za-z]', a): continue          # 英文侧必须是英文
            if re.search(r'[A-Za-z]{3}', b): continue           # 中文侧别是原样没译
            votes[a][b] += 1
    gloss = {}
    for a, c in votes.items():
        b, n = c.most_common(1)[0]
        gloss[a] = (b, n, sum(c.values()), dict(c) if len(c) > 1 else None)
    return gloss


if __name__ == '__main__':
    g = build()
    print('挖到专名', len(g), '条')
    amb = {a: v for a, v in g.items() if v[3]}
    print('其中译法不唯一的', len(amb))
    for a, (b, n, tot, alt) in list(amb.items())[:15]:
        print(f'  {a:28s} -> {b}  ({n}/{tot})  其它: {alt}')
    print()
    for a, (b, n, tot, alt) in sorted(g.items())[:30]:
        print(f'  {a:32s} -> {b}   x{tot}')
