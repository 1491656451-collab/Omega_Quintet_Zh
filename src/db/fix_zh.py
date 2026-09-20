# -*- coding: utf-8 -*-
"""database 译稿的修正层（C1 交叉术语审计的产物）。

不改另一个 agent 的 .md 原稿，回填时在内存里叠加，改动可审计、可回滚。
每条改动都先用「该条英文里确实含对应原词」验证过，不是盲目全局替换。
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
_W = json.load(open(os.path.join(HERE, '..', 'work', 'fontwidth.json'), encoding='utf-8'))['sys']


def px(s):
    return sum(_W.get(c, 24) for c in s)


# ── 1. 术语统一 ────────────────────────────────────────────────
# (错误用词, 正确用词, 用来确认的英文原词)
# 正式口径来自系统文本 / 贴图 / 剧情三层，数据库这一层跑偏了
TERMS = [
    ('歌唱力', '歌力',  'Song Power'),
    ('神性',   '神力',  'Divinity'),
    ('生命力', '活力',  'Vitality'),
    ('化妆间', '化妆室', 'Makeup Room'),
    ('护堂',   '五道',  'Godou'),          # 人名，剧情里一直是「五道」
    ('女主角', '歌姬',  None),             # Verse Maiden 的既定译法
    ('神圣领域', '圣域', 'Sacred Zone'),    # 野外行动名，和系统文本的动作轮盘对齐
]


# ── 1b. 地名统一（第 12 轮）────────────────────────────────
# 迷宫名横幅贴图已经交付，用户拍板以贴图为准。数据库说明文里有 167 条跑偏。
# 用正则是因为「水晶洞」不能盲替换 —— 会把已经对的「水晶洞窟」变成「水晶洞窟窟」。
# (正则, 正确写法, 用来确认的英文原词)
def _loose(word, tail=''):
    """专名可能被断行切开（翠绿\\n绿化带），字与字之间容许一个换行。"""
    return r'\n?'.join(word) + tail


PLACES = [
 (_loose('翠绿绿化带'),      '翠绿地带',    'Verdant Greenbelt'),
 (_loose('干旱荒野'),        '干涸荒野',    'Arid Wilderness'),
 (_loose('摩天楼避难所'),    '摩天避难所',  'Skyscraper Shelter'),
 (_loose('山手町废墟'),      '山手町遗迹',  'Yamate'),
 (_loose('山手废墟'),        '山手町遗迹',  'Yamate'),
 (_loose('湾畔工厂'),        '湾岸工厂',    'Bayside Plant'),
 (_loose('山谷补给基地'),    '溪谷补给基地', 'Valley Supply Base'),
 (_loose('新桥', r'(?=\n?商业区)'), '二桥',  'Nibashi'),
 (_loose('水晶洞', r'(?!\n?窟)'),   '水晶洞窟', 'Crystal Cave'),
 (_loose('观星者场'),        '观星者之地',  'Stargazers'),
]


# ── 2. 整条重写：漏译 ──────────────────────────────────────────
# stArchive 29 的英文有 899 字符，原稿只译出了 7 个字（只有标题）。
OVERRIDE = {
 'stArchive|29:40':
 "[管理人员] \n"
 "\n"
 "致有意支援守护本町的歌姬的各位，\n"
 "以及对「主席」一职感兴趣的各位，\n"
 "要不要一起来守护这座城镇？\n"
 "我们招募的是从事务工作到主席职务\n"
 "一应俱全的全能岗位。\n"
 "本事务所成立的宗旨，\n"
 "在于支援歌姬、维持城镇的秩序。\n"
 "若能与我们共事，\n"
 "那些你曾经只能隔着屏幕仰望的歌姬，\n"
 "说不定会比想象中离你更近！？\n"
 "提供住宿与福利！\n"
 "对自己的体力与抗压能力有自信的人，\n"
 "以及判断力过人的人——\n"
 "让我们一起并肩作战吧！\n"
 "薪资面议！工作地点将在正式录用后告知。\n"
 "\n"
 "电话号码 ○○○―○○○○\n"
 "——招聘负责人 亚由美",
}


# ── 3. 行数收敛 ────────────────────────────────────────────────
# 中文比英文密，原稿里有 37 条断出的行数比原文还多，有溢出风险。
# 把相邻两行里最窄的一对并起来，直到行数不超过原文；
# 并完再校一次每行像素宽不超过原文最宽行。
def rewrap(zh, en):
    el = en.split('\n')
    lines = zh.split('\n')
    if len(lines) <= len(el):
        return zh
    limit = max(px(x) for x in el)
    while len(lines) > len(el):
        i = min(range(len(lines) - 1), key=lambda i: px(lines[i]) + px(lines[i + 1]))
        lines[i:i + 2] = [lines[i] + lines[i + 1]]
    if max(px(x) for x in lines) > limit:
        return zh                      # 合并后反而超宽就不动，交给人工
    return '\n'.join(lines)


# ── 4. 断行再平衡 ──────────────────────────────────────────────
# 行数没超、用词也对，但断行偏了：第一行特别长、后两行很短。
# 逐条比看不出来（它自己的英文首行也长），按「表+列」粒度（一列 = 一个
# UI 字段 = 一个框）复查才暴露。值 = 该列英文最宽行像素数，即框宽下界。
# 见 check_width2.py。
REBALANCE = {'stNpc|203:136': 667}

_PUNC = '。！？，、；：…）」』】》'


def _segs(t):
    """按标点切成不可再分的片段；连续标点（……！）算一处。"""
    out, cur = [], ''
    for i, ch in enumerate(t):
        cur += ch
        if ch in _PUNC and (i + 1 >= len(t) or t[i + 1] not in _PUNC):
            out.append(cur); cur = ''
    if cur:
        out.append(cur)
    return out


def balance(zh, limit, maxlines):
    """重新断行：在不超过 maxlines 行的前提下，让最宽的那行尽可能窄。"""
    segs = _segs(zh.replace('\n', ''))
    if not segs:
        return zh
    for w in range(max(px(s) for s in segs), limit + 1, 8):
        lines, cur = [], ''
        for s in segs:
            if cur and px(cur) + px(s) > w:
                lines.append(cur); cur = s
            else:
                cur += s
        if cur:
            lines.append(cur)
        if len(lines) <= maxlines:
            return '\n'.join(lines)
    return zh                          # 怎么断都超宽，不动，交给人工


def apply(zh_map, en_map):
    """zh_map / en_map: {'表|键': 文本}。返回 (新的zh_map, 改动统计)。"""
    out = dict(zh_map)
    stat = {'术语': 0, '重写': 0, '收敛行数': 0, '收敛失败': 0, '再平衡': 0, '再平衡失败': 0}
    for wrong, right, word in TERMS:
        for k, v in list(out.items()):
            if wrong not in v:
                continue
            if word and not re.search(r'(?<![A-Za-z])' + re.escape(word) + r'(?![A-Za-z])',
                                      en_map.get(k, ''), re.I):
                continue               # 英文里没有这个词，说明是同形不同义，不动
            out[k] = v.replace(wrong, right)
            stat['术语'] += 1
    stat['地名'] = 0
    for pat, right, word in PLACES:
        rx = re.compile(pat)
        for k, v in list(out.items()):
            if not rx.search(v):
                continue
            if word.lower() not in en_map.get(k, '').lower():
                continue          # 英文里没提这个地名，不动
            nv = rx.sub(right, v)
            if nv != v:
                out[k] = nv; stat['地名'] += 1
    for k, v in OVERRIDE.items():
        out[k] = v
        stat['重写'] += 1
    for k, v in list(out.items()):
        e = en_map.get(k, '')
        if v.count('\n') > e.count('\n'):
            nv = rewrap(v, e)
            if nv != v:
                out[k] = nv; stat['收敛行数'] += 1
            else:
                stat['收敛失败'] += 1
    for k, limit in REBALANCE.items():
        e = en_map.get(k, '')
        nv = balance(out[k], limit, len(e.split('\n')))
        if nv != out[k]:
            out[k] = nv; stat['再平衡'] += 1
        else:
            stat['再平衡失败'] += 1
    return out, stat
