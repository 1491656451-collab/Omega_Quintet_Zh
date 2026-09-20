# -*- coding: utf-8 -*-
"""校验 gstr 译文：占位符/控制码必须与原文完全一致；并列出「故意保留英文」的条目。"""
import json, re, sys
import tr_gstr

EN = json.load(open('gstr_en.json', encoding='utf-8'))
ZH = {'strSystem': tr_gstr.SYSTEM, 'strRpg': tr_gstr.RPG, 'strEvent': tr_gstr.EVENT}

# 必须逐个一致的控制码 / 占位符
PAT = re.compile(r'#Icon\[[^\]]*\]|#FontPos\[[^\]]*\]|#FontColor\[[^\]]*\]|#n|%ll?[udsx]|%\d*[udsx]|%02u')


def sig(s):
    return tuple(PAT.findall(s)) + (s.count('\n'),)


def main():
    bad, kept, done = [], [], 0
    for f, d in EN.items():
        z = ZH[f]
        for k, en in d.items():
            if not en.strip():
                continue
            v = z.get(int(k))
            if v is None:
                kept.append((f, k, en)); continue
            done += 1
            if sig(en) != sig(v):
                bad.append((f, k, en, v, sig(en), sig(v)))
    print(f'已译 {done} 条，保留原文 {len(kept)} 条，控制码/占位符不一致 {len(bad)} 条')
    for b in bad[:20]:
        print(f'  !! {b[0]} {b[1]}\n     原 {b[2]!r}\n     译 {b[3]!r}\n     {b[4]} vs {b[5]}')
    if '-v' in sys.argv:
        print('\n--- 保留原文的条目 ---')
        for f, k, en in kept:
            print(f'  {f} {k}: {en!r}')
    return len(bad)


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
