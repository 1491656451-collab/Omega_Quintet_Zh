# -*- coding: utf-8 -*-
"""DLC.bra 里那套数据库分表的译文（名称 + 说明文）。

口径全部沿用主包：
  ＭＡＤ / Blare 保持原文 / 歌姬(Verse Maiden) / 幻素(Arcanium) / 音器(Mic) / EP
  歌力·耐力·知识·神力·技巧·活力
  图纸(Blueprints) / 护具(Protector) / 配件(Attachment) / 增幅器(Amp)
  等待时间(Wait Time) / 电压点数(Voltage Point) / 范围：圆(Range: Circle) / HIT / [参考值：X]
  自动防御(Auto-Guard) / 击退(Knockback) / 反转(Reverse) / 状态异常
名称里能在主包 1869 条里查到的**一律沿用**（由 dlc_backfill 自动接过来），
这里只写主包没有的那 104 条。
"""

# ---------------------------------------------------------------- 名称
NAMES = {
    # --- 怪物 ---
    'Shampuru':               '香波璐',
    'Shampuru Loner':         '孤独香波璐',
    'Assault Shampuru':       '突击香波璐',
    'Defense Shampuru':       '防御香波璐',
    'Magic Shampuru':         '魔法香波璐',
    'Support Shampuru':       '支援香波璐',
    'Attack Shampuru':        '攻击香波璐',
    'Ranged Shampuru':        '射击香波璐',
    'Banana Demon':           '香蕉魔',
    'Rabbit Demon':           '兔魔',
    'Slonel':                 '斯洛涅尔',
    'Skeleton Koropokkuru':   '骷髅科罗波库鲁',
    'Darkness Cafard':        '暗黑蜚蠊',
    'Dark Beast Fenrir':      '暗兽芬里尔',
    'Heretic Breaker':        '异端破坏者',
    'Nidhogg':                '尼德霍格',
    'Seraphi':                '撒拉菲',
    'Eternal Dragon':         '永恒龙',
    'Astra':                  '阿斯特拉',

    # --- 迷宫 / 地名 ---
    'Triple Towers':          '三重塔',
    'Centre Plaza':           '中央广场',
    'Meteorological Station': '气象观测站',
    'South Plains':           '南部平原',
    'Fissure Field':          '裂隙原野',
    'Arid Fields':            '干涸原野',
    'Chasm Path':             '深渊小径',

    # --- 技能 ---
    'Rabbit Heaven':          '兔之天国',
    'Libido Splash':          '欲念飞溅',
    'Bubbly Bomber':          '泡沫轰炸',
    'Lyrical Shamble':        '抒情乱舞',

    # --- 图纸 ---
    'Variety Mic Blueprint 01': '异色音器图纸 01',
    'Variety Mic Blueprint 02': '异色音器图纸 02',
    'Variety Mic Blueprint 03': '异色音器图纸 03',
    'Variety Mic Blueprint 04': '异色音器图纸 04',
    'Variety Mic Blueprint 05': '异色音器图纸 05',
    'New Protector Blueprint':  '新型护具图纸',
    'New Attachment Blueprint': '新型配件图纸',

    # --- 音器 ---
    'Cat Paw Hammer':         '猫爪锤',
    'Avenger':                '复仇者',
    'Overdrive':              '超载',
    'Luftgrandza':            '鲁夫特格兰扎',
    'Angel Wing':             '天使之翼',

    # --- 护具 AG（Aurora Generation，极光展开装置，主包通称 AG）---
    'AG II Master':           'AG II 主控',
    'AG II Surge':            'AG II 涌流',
    'AG II Phoenix':          'AG II 凤凰',
    'AG II Serpent':          'AG II 巨蛇',
    'AG II Elf':              'AG II 精灵',
    'AG II Gnome':            'AG II 地精',
    'AG EVE':                 'AG 夏娃',
    'AG ADAM':                'AG 亚当',

    # --- 配件（电池）---
    'Life Walk Battery':      '生机电池',
    'Split Battery':          '分流电池',
    'Freshness Battery':      '清爽电池',
    'Element Battery':        '元素电池',
    'Neutrino Battery':       '中微子电池',

    # --- 服装套装：进行曲 ---
    'Marching Band Notes':    '行进乐队乐谱',
    'Side Drill Ponytail':    '侧钻卷马尾',
    'Striped Mini-Hat':       '条纹小礼帽',
    'Sparkling Earring':      '闪耀耳环',
    'Maiden of the Plateau':  '高原少女',
    'Marching Idol':          '行进偶像',
    'Striped Garter':         '条纹吊袜带',

    # --- 服装套装：薄荷巧克力 ---
    'Chocolate Mint Diary':   '薄荷巧克力手账',
    'Feminine Knot':          '淑女丸子头',
    'Chocolate Mint Hat':     '薄荷巧克力帽',
    'Ice Cream Earring':      '冰淇淋耳环',
    'Chocolate Mint Circus':  '薄荷巧克力马戏',
    'Chocolate Mint Angel':   '薄荷巧克力天使',
    'Chocolate Mint Boots':   '薄荷巧克力短靴',

    # --- 服装套装：机器人 ---
    "Children's Sketch Book": '儿童写生簿',
    'Hoppity Pigtails':       '蹦跳双马尾',
    'Fake Hair Scrunchie':    '假发发圈',
    'Fashionable Transceiver': '时尚对讲机',
    'Inner Protector':        '内衬护具',
    'Robotic Dress':          '机械连衣裙',
    'Robotic Thigh High Boots': '机械过膝靴',

    # --- 服装套装：和服 ---
    'Kimono Encyclopedia':    '和服大全',
    'Geisha Hair':            '艺伎发髻',
    'High-Grade Hairpiece':   '高级发饰',
    'Sakura Paint':           '樱花彩绘',
    'Kimono Bikini':          '和服比基尼',
    'Petite Geisha Dress':    '迷你艺伎装',
    'Two-Toe Slouch Socks':   '分趾堆堆袜',

    # --- 道具 ---
    'Servant Guide II':       '仆从指南II',
    'Bomb Cloth':             '炸弹布',
    'High-Quality Corn Potage':       '高级玉米浓汤',
    'Super High-Quality Stew':        '超高级炖菜',
    'Overwhelming Cleanse Supplement': '极效净化剂',
    'Overwhelming Cleanse Extract':    '极效净化萃取液',
    'Overwhelming Salisbury Steak':    '极品汉堡排',
    'Overwhelming Sweet Curry':        '极品甜味咖喱',
    'Equalizer':              '均衡器',
    'Enhancer':               '强化器',
    'Discord':                '不协和音',
}

# ---------------------------------------------------------------- 说明文
# 主包里一模一样的英文会自动沿用主包译文（dlc_backfill 里做），这里只写剩下的。
STRS = {
"A sample Mic blueprint":
    "音器图纸的样品",
"A blueprint of a newly designed protector.":
    "新设计的护具图纸。",
"A blueprint of a newly designed attachment.":
    "新设计的配件图纸。",

# --- 音器 ---
"A Mic shaped in the form of a cat's paw.\nThis soft, plushy paw has lain waste to many a cat lover.":
    "做成猫爪形状的音器。\n这只柔软蓬松的肉球已经击溃了无数猫奴。",
"As its name states, it seeks vengeance.\nThose who wield it are said to be possessed by a curse within the spear.":
    "正如其名，它渴求复仇。\n据说持枪者会被枪中的诅咒附身。",
"A fist-type Mic with drills attached. It is so powerful that\nit can punch through steel like paper. Do not use against anyone.":
    "装了钻头的拳套型音器。威力大到\n能像捅破纸一样打穿钢铁。切勿对人使用。",
"A rifle-type Mic of formidable size and form.\nDepending on the user, it can reach miles across towns.":
    "体型与外形都极具压迫感的步枪型音器。\n看使用者的本事，射程能跨越数个街区。",
"A graceful Mic designed in the image of an angel's wing.\nIts motto: Wield the Power of the Archangel!":
    "以天使之翼为原型设计的优雅音器。\n它的口号是：挥舞大天使之力！",

# --- 护具 AG ---
"A second-gen Aurora Generation device. Only the wearer can see the aurora.":
    "第二代极光展开装置。只有佩戴者能看见那道极光。",
"A second generation aurora generation device focused on increasing Divinity.":
    "以提升神力为重点的第二代极光展开装置。",
"An AG II etched with the image of a fire spirit. Gain the ability to absorb fire attacks.\nSong Power goes up slightly.":
    "刻有火之精灵纹样的AG II。获得吸收火属性攻击的能力。\n歌力小幅提升。",
"An AG II etched with the image of a water spirit. Gain the ability to absorb water attacks.\nKnowledge goes up slightly.":
    "刻有水之精灵纹样的AG II。获得吸收水属性攻击的能力。\n知识小幅提升。",
"An AG II etched with the image of a wind spirit. Gain the ability to absorb wind attacks.\nVitality goes up slightly.":
    "刻有风之精灵纹样的AG II。获得吸收风属性攻击的能力。\n活力小幅提升。",
"An AG II etched with the image of an earth spirit. Gain the ability to absorb earth attacks.\nTechnique goes up slightly.":
    "刻有土之精灵纹样的AG II。获得吸收土属性攻击的能力。\n技巧小幅提升。",
"A third generation AG that increases both maximum HP and maximum SP.":
    "同时提升HP上限与SP上限的第三代AG。",
"Chance of Auto-Guard activating to halve damage.\nAlso nulls enemy criticals.":
    "有几率发动自动防御，将伤害减半。\n同时无效化敌人的会心一击。",

# --- 配件 ---
"Slightly recovers HP during the wearer's turn. Accuracy increases.":
    "佩戴者的回合中小幅恢复HP。命中率提升。",
"Slightly recovers SP during the wearer's turn. Evasion increases.":
    "佩戴者的回合中小幅恢复SP。回避率提升。",
"Negates all negative status effects.\nAll stats increase.":
    "无效化所有负面状态。\n全能力提升。",
"Greatly increases resistance to all elements.\nSong Power and Knowledge increase.":
    "大幅提升所有属性抗性。\n歌力与知识提升。",
"Negates all HP and SP Break, Knockback and Reverse abnormalities.":
    "无效化HP与SP的击破、击退与反转异常。",

# --- 消耗品 ---
"Recovers 50% of HP and SP for all members within range.\nHome-cooked sweet potage, just the way you like it!":
    "恢复范围内全体成员50%的HP与SP。\n家常的甜味浓汤，正合你的口味！",
"Recovers 50% of HP and SP for all members within range. Home-cooked sweet potage, just the way you like it!":
    "恢复范围内全体成员50%的HP与SP。家常的甜味浓汤，正合你的口味！",
"Recovers all HP and SP for all members within range. A masterpiece of complete self-indulgence.":
    "完全恢复范围内全体成员的HP与SP。一道彻底放纵自我的杰作。",
"Removes all status abnormalities for one member.\nA collaborative item made between Professor Clear and Hassis.":
    "消除1名成员的所有状态异常。\n克利尔博士与哈西斯合作研制的道具。",
"Removes all status abnormalities for one member. A collaborative item made between Professor Clear and Hassis.":
    "消除1名成员的所有状态异常。克利尔博士与哈西斯合作研制的道具。",
"Removes all status abnormalities for all members within range.\nA collaborative item made between Professor Clear and Hassis.":
    "消除范围内全体成员的所有状态异常。\n克利尔博士与哈西斯合作研制的道具。",
"Removes all status abnormalities for all members within range. A collaborative item made between Professor Clear and Hassis.":
    "消除范围内全体成员的所有状态异常。克利尔博士与哈西斯合作研制的道具。",
"Recovers all HP & SP, removes all status abnormalities, and removes all stat changes for one member.\nNow if only it had a sunny-side-up egg on top...":
    "完全恢复1名成员的HP与SP，消除所有状态异常与能力变化。\n要是上面再加个煎蛋就好了……",
"Recovers all HP & SP, removes all status abnormalities, and removes all stat changes for one member. Now if only it had a sunny-side-up egg on top...":
    "完全恢复1名成员的HP与SP，消除所有状态异常与能力变化。要是上面再加个煎蛋就好了……",
"Recovers all HP & SP, removes all status abnormalities, and removes all stat changes for all members within range.\nAn exotic-flavored favorite!":
    "完全恢复范围内全体成员的HP与SP，消除所有状态异常与能力变化。\n异国风味的心头好！",
"Recovers all HP & SP, removes all status abnormalities, and removes all stat changes for all members within range. An exotic-flavored favorite!":
    "完全恢复范围内全体成员的HP与SP，消除所有状态异常与能力变化。异国风味的心头好！",
"Allows the removal of unique Blare that can't be removed by conventional means.":
    "可清除常规手段无法清除的特殊Blare。",
"Disassembling this will create Arcanium and EP, and can also remove unique Blare.":
    "分解后可生成幻素与EP，还能清除特殊Blare。",
"Disassembling this will create Arcanium and EP. A sign of a game master.":
    "分解后可生成幻素与EP。通关者的证明。",
"When decomposed, becomes raw material and can generate Arcanium and EP":
    "分解后成为原料，可生成幻素与EP",

# --- 服装套装：进行曲 ---
"Marching and playing at the same time? Unbelievable... Too much to handle for non-pros.":
    "一边行进一边演奏？简直不可思议……不是专业的根本吃不消。",
"A side ponytail with a drill-like shape. Drill into admirers' hearts with this hairstyle!":
    "钻头造型的侧马尾。用这个发型钻进仰慕者的心里吧！",
"A lovely hat designed with stripes to give it a more refined feel.":
    "以条纹设计出更显精致感的可爱帽子。",
"A very attractive, bright green star for one's ear. May be glow-in-the-dark.":
    "极为吸睛的亮绿色星星耳饰。也许还会夜光。",
"Bright green lining on pure white fabric brings about a sense of grace, just like a maiden on a plateau.":
    "纯白布料配上亮绿滚边，透着一股高原少女般的优雅。",
"Cute, two-toned attire. The yellow-green touch gives it extra depth.":
    "可爱的双色装束。黄绿色的点缀让它更有层次。",
"Wearing this makes the wearer's legs look slender and beautiful.":
    "穿上之后腿会显得又细又美。",

# --- 服装套装：薄荷巧克力 ---
"Comparative data among various store-served chocolate mint ice cream flavors.":
    "各家店的薄荷巧克力冰淇淋口味对比资料。",
"Hair is tied in a knotted bun. Highly feminine. Adds +5 to comeliness.":
    "把头发盘成丸子的发型。非常有女人味。姿色+5。",
"Your love of chocolate mint will be made apparent by wearing this hat.":
    "戴上这顶帽子，你对薄荷巧克力的爱就一目了然了。",
"Ice cream love! Hang it on your ears! Be one with the ice cream!!":
    "冰淇淋大爱！挂到耳朵上！与冰淇淋合为一体！！",
"The chocolate-colored lacing is just gorgeous. If only the white dress wasn't so sheer...":
    "巧克力色的系带实在华美。就是这身白裙子有点太透了……",
"Makes chocolate mint ice cream difficult to melt. Does not work on any other flavors.":
    "能让薄荷巧克力冰淇淋不易融化。对其它口味一概无效。",
"Wear this to feel like chocolate mint...... What would that feeling be like??":
    "穿上它就能体会薄荷巧克力的心情……那到底是什么心情？？",

# --- 服装套装：机器人 ---
"One can see the artist's sense of imagination. You notice a girl-shaped robot drawn often.":
    "能看出作画者的想象力。你注意到少女造型的机器人反复出现。",
"With how it looks, it almost feels like it'll start spinning and take you up into the air...":
    "看那形状，总觉得它随时会转起来把人带上天……",
"No matter how scruffy, this is able to bundle hair in an instant. How it does that is unknown.":
    "再乱的头发也能一瞬间扎好。原理不明。",
"Whether this actually works as a transceiver is a mystery. Well, it looks good.":
    "它究竟能不能当对讲机用是个谜。不过，好看就行。",
"A bit hard. It feels like it might give added protection against blows.":
    "有点硬。感觉能多挡几下打击。",
"A bit robotic. It's great in both resilience and against fire.":
    "有点机械感。韧性与耐火都很出色。",
"Sterilized clean of bacteria and dirt. Surprisingly breathable and dry, but not sized to fit shoe boxes.":
    "细菌与污垢都被杀得干干净净。意外地透气又干爽，只是尺寸塞不进鞋柜。",

# --- 服装套装：和服 ---
"Has everything you need to know about kimonos. Oh, and it's very thick.":
    "关于和服该知道的全在里面。哦，而且很厚。",
"An elegant hairstyle, see? See...? Would you like to see more?":
    "很雅致的发型吧？你看……？还想再多看看吗？",
"Here's a special gift I received from one of my regular patrons.":
    "这是我从一位常客那里得到的特别礼物。",
"Cherry blossoms are so great. But seeing them fall is sad, so I drew some on my face.":
    "樱花真好啊。可看着它落下又难过，所以我把它画在了脸上。",
"The kimono-like design adds style. May be in vogue next year...":
    "和服风的设计很有格调。说不定明年就流行起来了……",
"Geisha-style attire, see? Look... Isn't the ribbon around my chest beautiful?":
    "艺伎风的装束哦？你看……胸前这条带子很漂亮吧？",
"I tried to include the slouchy look into my socks...":
    "我试着把堆堆的感觉做进了袜子里……",

# --- 怪物图鉴 ---
"A normal Shampuru.\nNot very bubbly when used as a soap.":
    "普通的香波璐。\n当肥皂用的话不怎么起泡。",
"A mysterious Shampuru.\nMostly found in servitude of beings of destruction.":
    "神秘的香波璐。\n多半侍奉于破灭之存在。",
"They gather at festivals to drum up excitement.\nA brave and excitable Shampuru.":
    "会聚在祭典上炒热气氛。\n勇敢又爱起哄的香波璐。",
"Maintains a steel defense.\nThe summer months make it too hot to handle.":
    "维持着钢铁般的防御。\n一到夏天就热得没法抱。",
"Dreams of being a mage.\nIt actually is working as a magician's apprentice.":
    "梦想成为魔法师。\n实际上真的在当魔术师的学徒。",
"A plushy Shampuru.\nFirm enough to be a perfect nighttime companion.":
    "毛绒绒的香波璐。\n手感扎实，最适合当抱枕陪睡。",
"The more metal shavings fall from its blade,\nthe better it can ignite oil! Supposedly.":
    "刃上掉下的金属屑越多，\n据说就越容易把油点燃！",
"Meteors or not, it will shave\nanything coming at it. Shavey-shavey.":
    "不管来的是不是陨石，冲它来的东西\n它都要削一削。削削削。",
"A guest appearance from a spectral world!\nIts half-eaten carrot is its trademark.":
    "来自幽界的客串登场！\n啃了一半的胡萝卜是它的标志。",
"A collaboration between a bath and a banana!\nBeware of flying soap suds!":
    "浴室与香蕉的联名！\n小心四处乱飞的肥皂泡！",
"Plants used in Blare research, transformed into MAD. \nThey ensnare prey in their tentacles and consume them as nourishment.":
    "用于Blare研究的植物变成的ＭＡＤ。\n会用触手缠住猎物，吸取养分。",
"Mobile weapon allegedly made to counter Blare, but somehow \ntransformed into MAD. Its equipment is made to kill people.":
    "据说是为对抗Blare而造的机动兵器，不知为何\n变成了ＭＡＤ。它的装备是为杀人而设计的。",
"A weaponized artificial life form found in an ancient ruin. \nBecause it was created based on MAD, it has a bizarre outward appearance.":
    "在古代遗迹中发现的兵器化人造生命体。\n由于是以ＭＡＤ为原型制造的，外形十分怪异。",
"A weaponized, artificial life form found in an ancient ruin. \nBelieved to have been swallowed by the fringe and annihilated, it returned as a MAD.":
    "在古代遗迹中发现的兵器化人造生命体。\n本以为已被边缘吞噬殆尽，却以ＭＡＤ的姿态归来。",
"A draconic MAD that has taken over surrounding machinery. \nNothing is left behind in the wake of its overwhelming power.":
    "夺取了周围机械的龙型ＭＡＤ。\n它压倒性的力量过处，什么都不会留下。",
"MAD named for its appearance, which resembles the immortal bird of legend. \nIt is thought that Verse Maidens who consume its tears do not grow old.":
    "因外形酷似传说中的不死之鸟而得名的ＭＡＤ。\n据说饮下它眼泪的歌姬不会衰老。",
"MAD with the traits of both anthropoids and demonics. \nPurported to make any wish come true in exchange for a person’s life.":
    "兼具类人与魔性特征的ＭＡＤ。\n据称能以人命为代价实现任何愿望。",
"An ancient weapon that moves autonomously via its magical core. \nThe vermillion light that streams from its eyes is excess light from its core.":
    "靠魔力核心自主行动的古代兵器。\n从双眼溢出的朱红色光，是核心多余的光。",
"Oddly-shaped MAD alleged to have been born of the fringe. \nThe fusion of two kinds of huge MAD, it will continue to move even if one of the heads is crushed.":
    "据说诞生自边缘的异形ＭＡＤ。\n由两种巨型ＭＡＤ融合而成，压碎其中一个头它仍会继续行动。",
"Said to be the form of a mountain spirit possessed by Blare. \nIt boasts a size big enough to completely destroy a town within a day.":
    "据说是被Blare附身的山神之姿。\n其体型大到足以在一天之内彻底毁灭一座城镇。",
"Verse Maidens of the past sealed this MAD into a great hole. \nThe area is now being used as a training facility.":
    "过去的歌姬将这只ＭＡＤ封印在大洞中。\n该区域如今被用作训练设施。",
"Thaumatotherian MAD wielding a slew of daggers. \nIt appears to have been born from a child’s drawing, but the truth is unknown.":
    "手持大量短刀的幻兽型ＭＡＤ。\n看上去像是从孩子的画里诞生的，真相不明。",
"Draconic MAD that has slaughtered many Verse Maidens. \nIt has blue scales and usually sleeps at the bottom of the sea.":
    "屠戮过众多歌姬的龙型ＭＡＤ。\n身覆蓝色鳞片，平时沉睡在海底。",
"Giant MAD that appears to be the union of a three-headed dragon \nand another monster-like creature. ":
    "看上去像是三头龙与另一种怪物般的生物\n结合而成的巨型ＭＡＤ。 ",
"Draconic MAD awakened from tens of thousands of years of sleep. \nAlleged to have destroyed the civilization that created a now ancient ruin.":
    "从数万年沉睡中苏醒的龙型ＭＡＤ。\n据说是它毁灭了建造如今那座古代遗迹的文明。",
"Those who witnessed its moment of appearance are extremely few in number. \nThe jewel on its head is treasured as a precious raw material.":
    "目击过它现身瞬间的人极少。\n它头上的宝石被视为珍贵的原料。",
"Draconic MAD that appeared at the same time as Blare. \nThe strongest among all MAD, it destroyed many nations before the fringes began materializing.":
    "与Blare同时出现的龙型ＭＡＤ。\n它是所有ＭＡＤ中最强的，在边缘开始显现之前就毁灭了许多国家。",

# --- 技能效果行（格式沿用主包：{效果} 范围：圆 / NN HIT [参考值：X]）---
"{Sleep & IN.KO: Increase} {Wait Time: Increase} {SP Damage} Range: Circle / 32 HITS [Reference Value: Song Power]":
    "{睡眠＆即死：提升} {等待时间：增加} {SP伤害} 范围：圆 / 32 HIT [参考值：歌力]",
"{Contamination & Panic: Decrease} {Stamina & Knowledge: Decrease} {Voltage Point: Decrease} {Wait Time: Increase} Range: Circle / 64 HITS [Reference Value: Knowledge]":
    "{污染＆恐慌：降低} {耐力＆知识：降低} {电压点数：减少} {等待时间：增加} 范围：圆 / 64 HIT [参考值：知识]",
"{Wait Time: Increase} {Voltage Point: Decrease} {All Stats: Decrease} Range: Circle / 18 HITS [Reference Value: Song Power]":
    "{等待时间：增加} {电压点数：减少} {全能力：降低} 范围：圆 / 18 HIT [参考值：歌力]",
"{Contamination/Sleep/Paralysis/Seal/Panic/Darkness/Virus} {Wait Time: Increase} Range: Circle / 18 HITS [Reference Value: Knowledge]":
    "{污染／睡眠／麻痹／封印／恐慌／黑暗／病毒} {等待时间：增加} 范围：圆 / 18 HIT [参考值：知识]",

# --- 化妆表里的发型名（和道具名同名）---
"Side Drill Ponytail": "侧钻卷马尾",
"Feminine Knot":       "淑女丸子头",
"Hoppity Pigtails":    "蹦跳双马尾",
"Geisha Hair":         "艺伎发髻",
}
