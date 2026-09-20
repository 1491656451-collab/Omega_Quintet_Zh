#!/usr/bin/env python3
"""用法:  python3 work/verify.py 03        检查单批
          python3 work/verify.py all       检查全部 12 批 + 完整性汇总
在工具包根目录（含 gbnl.py 的那一层）运行。不依赖字体文件，宽度查 work/advfont_width.json。"""
import sys, json, importlib.util, re, os, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(os.path.join(BASE, 'work/advfont_width.json'), encoding='utf-8'))
def px(s): return sum(W.get(c, 36) for c in s)

LINE_MAX_PX = 22 * 36      # 每显示行上限：22 个全角字
MAX_LINES   = 3            # 每条对白最多 3 个显示行
NARR_MIN    = 60           # 原文单行且超过 60 字符 = 全屏旁白，译文必须保持单行

BAN = {"塔克托":"塔克特","奏音":"奏子","涅涅":"祢祢","咏唱少女":"歌姬","歌唱少女":"歌姬",
       "亚里亚":"艾莉亚","阿莉亚":"艾莉亚","布雷尔":"Blare","布莱尔":"Blare","桃花":"桃香",
       "MAD":"ＭＡＤ","麦克风":"音器","光盘":"唱片","碟片":"唱片","塔克脱":"塔克特"}
PH = re.compile(r'%(?:[0-9]+)?(?:ll)?[sdufx]')

def load(n):
    p = os.path.join(BASE, f'work/batch_{n}_zh.py')
    if not os.path.exists(p): return None
    spec = importlib.util.spec_from_file_location("z_"+n, p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.T

def check_batch(n):
    src = json.load(open(os.path.join(BASE, f'work/batch_{n}_in.json'), encoding='utf-8'))
    T = load(n)
    if T is None: return [f"batch {n}: 输出文件 work/batch_{n}_zh.py 不存在"], 0
    probs = []; ok = 0
    for fn, items in src.items():
        if fn not in T: probs.append(f"{fn}: 整个文件缺失"); continue
        got = T[fn]
        for row, sp, en in items:
            if row not in got: probs.append(f"{fn}[{row}]: 漏译"); continue
            zh = got[row]
            if not isinstance(zh, str) or not zh.strip():
                probs.append(f"{fn}[{row}]: 空译文"); continue
            zl = zh.split('\n'); el = en.split('\n')
            if len(zl) > MAX_LINES:
                probs.append(f"{fn}[{row}]: {len(zl)} 个显示行 > {MAX_LINES}")
            narr = (len(el) == 1 and len(en) > NARR_MIN)
            if narr and len(zl) > 1:
                probs.append(f"{fn}[{row}]: 全屏旁白必须保持单行")
            if not narr:
                for k, L in enumerate(zl):
                    if px(L) > LINE_MAX_PX:
                        probs.append(f"{fn}[{row}] 第{k+1}行超宽 {px(L)}px>{LINE_MAX_PX}px: {L[:26]}")
            if sorted(PH.findall(en)) != sorted(PH.findall(zh)):
                probs.append(f"{fn}[{row}]: 占位符不匹配 {PH.findall(en)} -> {PH.findall(zh)}")
            for bad, good in BAN.items():
                if bad in zh: probs.append(f"{fn}[{row}]: 术语错误 '{bad}' 应为 '{good}'")
            ok += 1
        extra = set(got) - {r for r, _, _ in items}
        if extra: probs.append(f"{fn}: 多出行号 {sorted(extra)[:5]}")
    for x in T:
        if x not in src: probs.append(f"{x}: 不属于本批次")
    return probs, ok

def main(arg):
    nums = [f"{i:02d}" for i in range(1, 13)] if arg == 'all' else [f"{int(arg):02d}"]
    total_ok = 0; bad = 0
    for n in nums:
        probs, ok = check_batch(n)
        total_ok += ok
        if probs:
            bad += 1
            print(f"batch {n}: {len(probs)} 个问题 (通过 {ok} 条)")
            for x in probs[:80]: print("   -", x)
            if len(probs) > 80: print(f"   ... 还有 {len(probs)-80} 个")
        else:
            print(f"batch {n}: OK  {ok} 条全部通过")
    if arg == 'all':
        print(f"\n合计通过 {total_ok} / 10712 条；{bad} 个批次有问题")
        return 1 if (bad or total_ok != 10712) else 0
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'all'))
