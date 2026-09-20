#!/usr/bin/env python3
"""把 tr_event_pilot.py + work/batch_01..12_zh.py 的全部译文打进 Event.bra

用法:  python3 build_event_all.py <原始Event.bra路径> <输出Event.bra路径>
例:    python3 build_event_all.py "D:/.../Event.bra.bak" out/Event.bra
"""
import sys, os, importlib.util, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bra as B, brapack
from gbnl import GBNL
import tr_speakers
import tr_event_pilot

def load_batches():
    T = dict(tr_event_pilot.T)
    for p in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           'work/batch_*_zh.py'))):
        spec = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for fn, rows in m.T.items():
            if fn in T: raise SystemExit(f"文件 {fn} 在多个批次里重复出现")
            T[fn] = rows
    return T

def main(src, dst):
    T = load_batches()
    print(f"译文覆盖 {len(T)} 个事件文件，共 {sum(len(v) for v in T.values())} 条")
    d = open(src, 'rb').read()
    ver, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    rep = {}
    missing_files = []
    for fn, rows in T.items():
        key = f"SCRIPT\\DATA\\{fn}.gbin"
        if key not in byname: missing_files.append(fn); continue
        raw, _ = B.get(d, byname[key])
        g = GBNL(data=raw)
        mapping = {}
        untranslated = 0
        for i, o, rel, b in g.cells():
            if b is None: continue
            s, enc = g.dec(b)
            if o == 0xA8:                      # 说话人
                if s in tr_speakers.SPEAKERS: mapping[(i, o)] = tr_speakers.SPEAKERS[s]
            elif o == 0xB8:                    # 正文
                if i in rows: mapping[(i, o)] = rows[i]
                elif s.strip() and s != '-': untranslated += 1
        if untranslated:
            print(f"  ! {fn} 还有 {untranslated} 条未翻译（将保留原文）")
        nb = g.rebuild(mapping)
        g2 = GBNL(data=nb)                     # 结构自检
        assert (g2.nrows, g2.rowsize, g2.ncols) == (g.nrows, g.rowsize, g.ncols), fn
        rep[key] = nb
    if missing_files: print("警告：原包里找不到这些文件:", missing_files)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    brapack.repack(src, rep, dst)
    print(f"替换 {len(rep)} 个成员 -> {dst}  {os.path.getsize(dst)} 字节")

if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
