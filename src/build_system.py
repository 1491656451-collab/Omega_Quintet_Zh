#!/usr/bin/env python3
"""从原始 System.bra 重新生成汉化版（补中文字形 + 菜单译文）

用法:  python3 build_system.py <原始System.bra路径> <输出System.bra路径>
依赖:  pip install pillow numpy   +  Noto Sans CJK Black 字体
       (Debian/Ubuntu: apt install fonts-noto-cjk fonts-noto-cjk-extra)
"""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'))
import bra as B, brapack, gstr, patchfont, tr_menu, tr_gstr

def main(src, dst):
    d = open(src, 'rb').read()
    ver, ents = B.read_index(d)
    byname = {e['name']: e for e in ents}
    tmp = tempfile.mkdtemp()
    rep = {}

    # 1) 菜单文本：日/英/韩三套一起换
    for db in ("database", "database_en", "database_kr"):
        key = f"{db}\\strMenu.gstr"
        raw, _ = B.get(d, byname[key])
        g = gstr.GStr(data=raw)
        ents_zh = [[i, k, tr_menu.ZH.get(i, v)] for i, k, v in g.ents]
        rep[key] = gstr.build(g, ents_zh)
    print("菜单文本已替换 3 套")

    # 1b) strSystem / strRpg / strEvent 共 699 条
    #     这三个也是按 id 索引的，三套 id 对得上，所以和 strMenu 一样三套一起换
    #     （注意：database.cl3 不能这么干，日/韩版行数不同）
    GS = {"strSystem": tr_gstr.SYSTEM, "strRpg": tr_gstr.RPG, "strEvent": tr_gstr.EVENT}
    ng = 0
    for fn, table in GS.items():
        for db in ("database", "database_en", "database_kr"):
            key = f"{db}\\{fn}.gstr"
            raw, _ = B.get(d, byname[key])
            g = gstr.GStr(data=raw)
            rep[key] = gstr.build(g, [[i, k, table.get(i, v)] for i, k, v in g.ents])
        ng += sum(1 for i, k, v in g.ents if i in table)
    print(f"系统文本已替换 {ng} 条 x 3 套（strSystem / strRpg / strEvent）")

    # 2) 两个字体补中文字形
    for name, kind in (("sysfont.ffu", "sysfont"), ("advfont.ffu", "advfont")):
        key = f"window\\font\\{name}"
        raw, _ = B.get(d, byname[key])
        src_p = os.path.join(tmp, name); open(src_p, 'wb').write(raw)
        out_p = os.path.join(tmp, "patched_" + name)
        patchfont.patch(src_p, out_p, kind)
        rep[key] = open(out_p, 'rb').read()

    # 3) 贴图美术字
    tex_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')
    if os.path.isdir(tex_dir):
        sys.path.insert(0, tex_dir)
        from ddsenc import encode_bc3
        TEX = {'global\\Texture\\grSystemMenuMain.dds': 'menu_zh.png',
               'global\\Texture\\grSystemString.dds':   'string_zh.png',
               'global\\Texture\\grSystemWorld.dds':    'world_zh.png',
               'global\\Texture\\grSystemResult.dds':   'result_zh.png',
               'global\\Texture\\grSystemDungeon.dds':  'dungeon_zh.png',
               'global\\Texture\\grSystemBattle.dds':   'battle_zh.png',
               'global\\Texture\\Sprites.dds':          'sprites_zh.png'}
        for key, png in TEX.items():
            pp = os.path.join(tex_dir, png)
            if not os.path.exists(pp): print("  [跳过]", png); continue
            ref, _ = B.get(d, byname[key])
            rep[key] = encode_bc3(pp, ref)
            print(f"  贴图 {key} <- {png}  BC7->BC3 {len(rep[key])} 字节")

    # 4) database.cl3 回填 8396 条（只改英文版：日/韩版行数不同，键对不上）
    zhdir = os.environ.get('OQ_DBZH', '/mnt/user-data/uploads/欧米伽五重奏')
    if os.path.isdir(zhdir) and any(f.endswith('_润色稿.md') for f in os.listdir(zhdir)):
        import db_backfill as DBF
        srcmap = __import__('json').load(open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'db', 'db_src.json'), encoding='utf-8'))
        zh = DBF.load_and_check(zhdir, srcmap)
        from cl3 import CL3
        from gbnl import GBNL
        import cl3w
        rawcl3, _ = B.get(d, byname[DBF.TARGET])
        c3 = CL3(data=rawcl3)
        idx = {nm.replace('.gbin', ''): i for i, (nm, _, _) in enumerate(c3.files)}

        # 4b) B4：物品名/技能名/怪物名/迷宫名/地图地名/素材名/角色名
        #     这些不是类型 5 字符串列，而是行记录里的定长内嵌字段
        import b4_backfill as B4
        b4src = __import__('json').load(open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'db', 'b4_src.json'), encoding='utf-8'))
        rowpat = B4.rowpatches(b4src, verbose=False)

        tabs = {}
        for t in srcmap:
            g = GBNL(data=c3.get(idx[t]))
            assert g.rebuild({}) == c3.get(idx[t]), t
            mp = {}
            for k in srcmap[t]:
                r, o = k.split(':'); mp[(int(r), int(o))] = zh[(t, k)]
            tabs[c3.files[idx[t]][0]] = g.rebuild(mp, rowpat.get(t))
        # 不在说明文译稿里的四张表：只动行记录，不重建字符串池
        # （stDungeon / stMaterial 空重建不是字节一致的，重建有风险，原地改最稳）
        for t, pat in rowpat.items():
            if t in srcmap or not pat: continue
            b = bytearray(c3.get(idx[t])); g = GBNL(data=bytes(b))
            for (i, o, w), v in pat.items():
                vb = v.encode('utf-8')
                assert len(vb) + 1 <= w, (t, i, v)
                b[i*g.rowsize+o : i*g.rowsize+o+w] = vb + b'\0'*(w-len(vb))
            tabs[c3.files[idx[t]][0]] = bytes(b)
        rep[DBF.TARGET] = cl3w.rebuild(rawcl3, tabs)
        print(f"  database.cl3 回填说明文 {sum(len(v) for v in srcmap.values())} 条 + "
              f"名称 {sum(len(v) for v in rowpat.values())} 条，"
              f"{len(rawcl3)} -> {len(rep[DBF.TARGET])} 字节")
    else:
        print('  [跳过] 没找到 database 译稿目录，database.cl3 保持原样')

    brapack.repack(src, rep, dst)
    print(f"替换 {len(rep)} 个成员 -> {dst}  {os.path.getsize(dst)} 字节")

if __name__ == "__main__":
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
