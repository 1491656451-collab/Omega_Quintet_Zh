#!/usr/bin/env python3
"""把机翻底稿 .md 解析成结构化数据，并与 batch_NN_in.json 对齐校验。

用法: python3 work/parse_draft.py <底稿.md> <批次号NN>
输出: work/batch_NN_draft.json   {文件号: {行号: [说话人, EN, 机翻ZH]}}

底稿格式（保持不变即可）:
    ## 事件 1006
    ### [0] Ayumi
    EN: Now then, has everyone shed their <br>exhaustion?
    ZH: 那么现在大家都脱掉了吗 <br>疲惫不堪？
"""
import re, json, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse(path):
    data, fn, cur, en = {}, None, None, None
    for ln in open(path, encoding='utf-8').read().split('\n'):
        if ln.startswith('## 事件 '):
            fn = ln[len('## 事件 '):].strip(); data[fn] = {}; cur = None
        elif ln.startswith('### ['):
            m = re.match(r'### \[(\d+)\]\s*(.*)', ln); cur = (int(m.group(1)), m.group(2).strip())
        elif ln.startswith('EN: ') and cur: en = ln[4:]
        elif ln.startswith('ZH: ') and cur:
            data[fn][cur[0]] = (cur[1], en, ln[4:]); cur = None
    return data

def main(draft, n):
    n = f"{int(n):02d}"
    d = parse(draft)
    src = json.load(open(f'{BASE}/work/batch_{n}_in.json', encoding='utf-8'))
    probs = []
    for fn, items in src.items():
        got = d.get(fn, {})
        for r, sp, en in items:
            if r not in got: probs.append(f"{fn}[{r}] 底稿缺失"); continue
            if got[r][1].replace('<br>', '\n').strip() != en.strip():
                probs.append(f"{fn}[{r}] EN 原文与源数据不一致")
    for fn in d:
        if fn not in src: probs.append(f"{fn} 不属于批次 {n}")
    json.dump({fn: {str(r): list(v) for r, v in rows.items()} for fn, rows in d.items()},
              open(f'{BASE}/work/batch_{n}_draft.json', 'w'), ensure_ascii=False)
    tot = sum(len(v) for v in d.values())
    exp = sum(len(v) for v in src.values())
    print(f"批次 {n}: 解析 {len(d)} 个文件 / {tot} 条（应有 {exp} 条）")
    if probs:
        print(f"对齐问题 {len(probs)} 处：")
        for p in probs[:20]: print("   -", p)
        return 1
    print("与源数据完全对齐 ✓  已写出 work/batch_%s_draft.json" % n)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))
