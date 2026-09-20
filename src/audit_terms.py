# -*- coding: utf-8 -*-
"""跨层术语审计：同一个英文词，在菜单 / 系统文本 / 数据库 / 剧情 四层里
   各自译成了什么。只要有一层不一样就报出来。"""
import sys, os, json, re, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tr_menu, tr_gstr

def load_layers():
    L = {}
    # 1 菜单 strMenu
    men = {e[0]: e[2] for e in json.load(open(os.path.join(HERE, 'menu_en.json'), encoding='utf-8'))}
    L['菜单'] = [(men[i], v) for i, v in tr_menu.ZH.items() if i in men and v]
    # 2 系统文本
    gen = json.load(open(os.path.join(HERE, 'gstr_en.json'), encoding='utf-8'))
    sysl = []
    for fn, tab in (('strSystem', tr_gstr.SYSTEM), ('strRpg', tr_gstr.RPG), ('strEvent', tr_gstr.EVENT)):
        for i, v in tab.items():
            e = gen[fn].get(str(i))
            if e and v: sysl.append((e, v))
    L['系统'] = sysl
    # 3 数据库
    src = json.load(open(os.path.join(HERE, 'db', 'db_src.json'), encoding='utf-8'))
    zh0 = json.load(open(os.path.join(HERE, 'db', 'db_zh.json'), encoding='utf-8'))
    sys.path.insert(0, os.path.join(HERE, 'db'))
    import fix_zh                       # 审的必须是真正打进包里的文本，不是原稿
    enm = {f'{t}|{k}': e for t, d in src.items() for k, e in d.items()}
    zh, _ = fix_zh.apply(zh0, enm)
    L['数据库'] = [(en, zh[f'{t}|{k}']) for t, d in src.items() for k, en in d.items()
                   if f'{t}|{k}' in zh]
    # 4 剧情（只用来查中文用词，英文对照在 event_text_en.json）
    try:
        ev = json.load(open(os.path.join(HERE, 'event_text_en.json'), encoding='utf-8'))
    except Exception:
        ev = None
    return L, ev


# 只看「整词出现」的情况，避免 Quest 匹配到 Question
TERMS = [
 'Mic','Disc','Amp','Arcanium','Blare','Verse Maiden','Harmonics','Voltage',
 'Mission','Quest','Collection','Workshop','Makeup Room','Exchange','Training Facility',
 'Live Concert Mode','Song Power','Stamina','Knowledge','Divinity','Technique','Vitality',
 'Hammer','Spear','Fist','Gun','Fan','Shield','Accessory','Outfit',
 'Contamination','Sleep','Paralysis','Seal','Panic','Darkness','Virus',
 'Skill','Ability','Bonus','Rewards','Approval','Proficiency',
 'Sacred Zone','Dowsing','Removal','Analyze','Elimination',
 'Takt','Otoha','Kyouka','Kanadeko','Nene','Aria','Momoka','Ayumi','Shiori','Tomekichi','Godou',
]
# 每个术语允许的中文（第一个是正式口径）
CANON = {
 'Mic':'音器','Disc':'唱片','Amp':'增幅器','Arcanium':'幻素','Verse Maiden':'歌姬',
 'Harmonics':'和声','Voltage':'电压','Mission':'任务','Quest':'委托',
 'Workshop':'工房','Makeup Room':'化妆室','Training Facility':'训练设施',
 'Live Concert Mode':'演唱会模式','Song Power':'歌力','Stamina':'耐力','Knowledge':'知识',
 'Divinity':'神力','Technique':'技巧','Vitality':'活力',
 'Hammer':'战锤','Spear':'长枪','Fist':'拳套','Gun':'枪械','Fan':'战扇',
 'Contamination':'污染','Sleep':'睡眠','Paralysis':'麻痹','Seal':'封印','Panic':'恐慌',
 'Darkness':'黑暗','Virus':'病毒',
 'Sacred Zone':'圣域','Dowsing':'探物','Removal':'清除',
 'Analyze':'解析','Elimination':'消除',
 'Takt':'塔克特','Otoha':'音羽','Kyouka':'响歌','Kanadeko':'奏子','Nene':'祢祢',
 'Aria':'艾莉亚','Momoka':'桃香','Ayumi':'亚由美','Shiori':'诗织',
 'Tomekichi':'留吉','Godou':'五道',
}


# ── 已人工复核的「同形不同义」 ────────────────────────────────
# 英文同一个词在别处是另一个意思，译文没跟正式口径是对的。
# 记成精确条数而不是放行规则：条数一变就说明译文动过，会重新报出来。
REVIEWED = {
 ('Knowledge', '菜单'):   (1,  'IDS_MENU_SKILL_TITLE_LEARNING，技能画面的「习得」页签，不是知识属性'),
 ('Hammer',   '数据库'):  (27, '「Hammer-type Mic」在说明文里是「锤式音器」，不是分类名「战锤」'),
 ('Spear',    '数据库'):  (18, '技能名「Spear Storm」= 枪风暴'),
 ('Fist',     '数据库'):  (3,  '「Fist Pump」= 挥拳，是动作'),
 ('Gun',      '数据库'):  (4,  '「Gun-type Mic」= 枪式音器'),
 ('Fan',      '系统'):    (1,  'strSystem 230 在「单体/圆形/十字/扇形/一列」里，是范围形状'),
 ('Fan',      '数据库'):  (101,'扇式音器 / 扇形范围 / 粉丝（观众），都不是武器分类名'),
 ('Seal',     '数据库'):  (1,  '「清爽印章」是道具贴纸，不是异常状态「封印」'),
 ('Removal',  '数据库'):  (1,  '「Limiter Removal」= 限制器解除，不是野外行动「清除」'),
}


def main():
    L, ev = load_layers()
    print('各层条数:', {k: len(v) for k, v in L.items()})
    print()
    bad = []
    for t in TERMS:
        pat = re.compile(r'(?<![A-Za-z])' + re.escape(t) + r'(?![A-Za-z])')
        canon = CANON.get(t)
        row = {}
        for lname, pairs in L.items():
            hits = [(e, z) for e, z in pairs if pat.search(e)]
            if not hits: continue
            if canon:
                miss = [(e, z) for e, z in hits if canon not in z]
                row[lname] = (len(hits), len(miss), miss[:2])
            else:
                row[lname] = (len(hits), 0, [])
        if canon and any(v[1] for v in row.values()):
            bad.append((t, canon, row))
    unreviewed = 0
    for t, canon, row in bad:
        head = []
        for lname, (n, m, ex) in row.items():
            if not m:
                continue
            k = REVIEWED.get((t, lname))
            if k and k[0] == m:
                head.append(f'  ~ {lname}: {m} 条同形不同义，已复核 —— {k[1]}')
            else:
                unreviewed += 1
                head.append(f'  ✗ {lname}: 出现 {n} 条，其中 {m} 条没用正式口径'
                            + (f'（复核记录是 {k[0]} 条，对不上）' if k else ''))
                for e, z in ex:
                    head.append(f'        原 {e[:60]!r}')
                    head.append(f'        译 {z[:60]!r}')
        print(f'■ {t} → 正式口径「{canon}」')
        print('\n'.join(head))
    print()
    if unreviewed:
        print(f'>>> 还有 {unreviewed} 处未复核的术语不一致')
    else:
        print('>>> 术语审计通过：正式口径全部一致，同形不同义的 '
              f'{sum(v[0] for v in REVIEWED.values())} 条已逐条复核')
    return unreviewed


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
