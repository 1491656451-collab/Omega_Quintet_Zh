# 工具链与译文

这里是做这个汉化补丁用到的全部东西：归档与文本格式的解析器、构建脚本、校验闸，以及译文本身。

## ⚠ 仓库不含游戏的英文原文

`menu_en.json` / `gstr_en.json` / `event_text_en.json` / `db/db_src.json` 这四个文件
**不在仓库里** —— 那是游戏本体的文本。构建之前先从**你自己那份游戏**里抽出来：

```bash
python3 extract_en.py "D:/SteamLibrary/steamapps/common/Omega Quintet"
```

只读 `System.bra` 和 `Event.bra`，不改任何东西。
哪些表、哪些列算「要翻译的文本」记在 `db_tables.json` 里（只是表结构，不含游戏文本）。

## 依赖

```bash
pip install pillow numpy zopfli
# 字体重渲染需要 Noto Sans CJK：
#   Debian/Ubuntu: apt install fonts-noto-cjk fonts-noto-cjk-extra
#   路径写在 patchfont.py 开头的 BOLD 常量里，按你的系统改
```

## 构建

```bash
# 主包：菜单 + 系统文本 + 数据库 + 贴图 + 中文字体
python3 build_system.py  <原版 System.bra>  out/System.bra

# 剧情 274 个事件 / 11039 条
python3 build_event_all.py  <原版 Event.bra>  out/Event.bra

# DLC
python3 build_dlc.py  <原版 DLC.bra>  out/DLC.bra

# 两个贴图差分补丁（OQPATCH2，原地替换）
python3 build_game1_all.py   <原版 Game1.bra>  out/Game1_all_zh.oqpatch
python3 build_game4_patch.py <原版 Game4.bra>  out/Game4_all_zh.oqpatch
```

`build_system.py` 产出的是完整的 `.bra`；发布用的差分补丁由 `oqp3.py` 拿
「原版 + 汉化版」两个包做差生成。

## 校验闸（出包前必须全绿）

| 脚本 | 查什么 |
|---|---|
| **`check_fmt.py`** | **`%s` / `%d` 等转换符的种类与顺序序列**必须与英文一致。只比个数是不够的 —— v1.4 那个「打开委托必崩」就是顺序反了而个数相同 |
| `check_gstr.py` | `#Icon[..]` 等控制码与占位符的数量、真实换行数 |
| `check_width2.py` | 按「同一个显示框」的粒度比中英文像素宽度与行数 |
| `check_places.py` | 17 个地名在数据库与剧情里的写法一致（容许断行切开） |
| `audit_terms.py` | 跨层术语统一，同形不同义记成精确条数 |
| `check_glyphs.py` | **从构建好的 `.bra` 里取出字体**，查五个文本层的字符覆盖 |
| `tex/checkbleed.py` | 改动像素必须落在自己的框内（游戏按框取 UV，画出框就会串） |
| `verify_dlc.py` | DLC 四道闸：回读 / 定长字节宽 / 像素宽 / 字形 |
| `sim_apply.py` | 拿真包完整跑一遍差分补丁的应用流程 |

## 文件导览

**格式解析**

| 文件 | 内容 |
|---|---|
| `bra.py` / `brapack.py` | `.bra` 归档（magic `PDA\0`，索引在文件尾部，成员 raw deflate）读 / 重打 |
| `gbnl.py` | GBNL 表：`[行 \| 列描述 \| 字符串池 \| 64 字节页脚]`。**两种文本**：类型 5 走字符串池；类型 1 且与下一列间隔 ≥32/64 字节是定长内嵌字段（所有**名称**都在这儿） |
| `cl3.py` / `cl3w.py` | CL3 容器（`database.cl3` 是 45 张 GBNL 表打在一起）。段描述符的 tbl 字段在 **+40** 不是 +44 |
| `gstr.py` | GSTL 字符串表（`strMenu` / `strSystem` / `strRpg` / `strEvent`），按 id 索引 |
| `ffu.py` | 游戏自有的点阵字体格式 |
| `oqp3.py` | OQPATCH3 差分补丁：按成员名寻址、带原始/新 MD5 双校验、塞不下就追加到文件末尾并改索引、自带撤销文件 |

**译文**

| 文件 | 内容 |
|---|---|
| `tr_menu.py` | strMenu 410 条 |
| `tr_gstr.py` | strSystem / strRpg / strEvent 699 条 |
| `db/db_zh_fixed.json` | 数据库说明文 8,396 条（`db_zh.json` 是修正层叠加前的原稿） |
| `db/_b4_en2zh.json` | 数据库名称 1,869 条 |
| `work/batch_*_zh.py` + `tr_event_pilot.py` | 剧情 274 个事件 / 11,039 条 |
| `tr_speakers.py` | 说话人名 |
| `tr_dlc.py` | DLC 名称 158 条 + 说明文 181 条 |
| `db/fix_zh.py` | 修正层：术语统一 1,333 处、地名 170 处、整条重写、行数收敛。**不改原稿，回填时在内存里叠加** |

**贴图**（`tex/`）

`build_tex.py` 是总入口，`map_*.py` 是各张图的框位与文字映射，
`platefix.py` 是底板擦除（三种确定性擦法：`clear` / `rows` / `prof`，`rows` 首选），
`autostyle.py` 从原文采样字色与描边，`ddsenc.py` 做 BC7→BC3 转码
（DX10 头里 `dxgiFormat` 改成 77，两种格式都是 16 字节 / 4×4 块，体积一字节不差）。

## 几条踩过的坑

- **`assert g.rebuild({}) == raw` 是必过的闸** —— 45 张主表里只有 25 张空重建是字节一致的。
  不一致的（`stDungeon` / `stMaterial` / DLC 的 4 张 `stDungeon0NN`）只能原地改行字节，不能重建字符串池。
- **`.gstr` 三套 locale 一起换**（按 id 索引，对得上）；**`database.cl3` 只能改 `database_en\`**
  （日/韩版 6,952 行 vs 英文版 7,059 行，行号对不上）。
- **CJK 字号要对齐英文的字身高（cap height），不是落笔框高** ——
  拉丁字母的墨迹带下伸部，框高比字身高一大截；汉字没有下伸部。`字号 = 字身高 − 2 × 描边宽`。
- **同一组标签必须同一个字号**（`map_*.py` 里的 `ONE_SIZE`），逐框算会导致同一列里条条大小不一。
- **无 BOM 的 `.ps1` 必须是纯 ASCII** —— PowerShell 5.1 按系统 ANSI（GBK）读无 BOM 的 `.ps1`。
  要在 `.ps1` 里写中文就存 UTF-8 + BOM。`.bat` 用 GBK + CRLF，且要逐字节检查 GBK 尾字节
  有没有撞上 cmd 元字符（`| ^ \ " & < > % ( )`）。
