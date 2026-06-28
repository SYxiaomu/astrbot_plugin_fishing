# 此文件包含所有游戏的基础数据定义
# 鱼类数据从独立模块导入，保持文件精炼

from .fish_data import FISH_DATA
from .ship_data import SHIP_DATA

# BAIT_DATA 的新结构化定义
# 格式: (name, description, rarity, effect_description, duration_minutes, cost, required_rod_rarity,
#        success_rate_modifier, rare_chance_modifier, garbage_reduction_modifier,
#        value_modifier, quantity_modifier, is_consumable)
BAIT_DATA = [
    # --- Rarity 1 (基础) ---
    ("普通蚯蚓", "最基础的鱼饵，随处可见。", 1, "无特殊效果",
     0, 5, 0, 0.0, 0.0, 0.0, 1.0, 1.0, True),

    ("面包团", "用面包捏成的简单鱼饵。", 1, "略微提高钓鱼成功率",
     0, 3, 0, 0.02, 0.0, 0.0, 1.0, 1.0, True),

    ("玉米粒", "甜甜的玉米粒，有些鱼喜欢。", 1, "略微提高钓鱼成功率",
     0, 4, 0, 0.02, 0.0, 0.0, 1.0, 1.0, True),

    # --- Rarity 2 (进阶) ---
    ("红虫", "营养丰富的鱼饵，很多鱼都爱吃。", 2, "提高中小型鱼上钩率",
     0, 20, 0, 0.05, 0.0, 0.0, 1.0, 1.0, True),

    ("亮片拟饵", "旋转时能反光的基础金属拟饵。", 2, "略微提高稀有鱼几率, 无消耗",
     0, 50, 1, 0.0, 0.01, 0.0, 1.0, 1.0, False),  # is_consumable = False

    ("腥味颗粒饵", "商业生产的鱼饵，气味浓烈。", 2, "提高多种鱼上钩率",
     0, 30, 1, 0.08, 0.0, 0.0, 1.0, 1.0, True),

    # --- Rarity 3 (高级) ---
    ("万能饵", "精心调配，对大多数鱼类都有效果。", 3, "显著提高所有鱼种上钩率",
     0, 100, 0, 0.15, 0.0, 0.0, 1.0, 1.0, True),

    ("活虾", "活蹦乱跳的虾，是许多鱼类的美味。", 3, "显著提高稀有鱼几率",
     0, 80, 1, 0.05, 0.03, 0.0, 1.0, 1.0, True),

    ("驱散垃圾饵", "散发着垃圾鱼讨厌的气味。", 3, "显著降低钓上垃圾的概率",
     30, 250, 1, 0.0, 0.0, 0.8, 1.0, 1.0, True),  # garbage_reduction_modifier = 0.8 (80%几率)

    # --- Rarity 4 (稀有) ---
    ("秘制香饵", "用特殊配方制成，对稀有鱼类极具诱惑力。", 4, "大幅提高稀有鱼上钩率",
     0, 500, 2, 0.0, 0.05, 0.0, 1.0, 1.0, True),

    ("价值连城饵", "散发着财富的气息。", 4, "钓上的鱼基础价值+10%",
     0, 700, 3, 0.0, 0.0, 0.0, 1.1, 1.0, True),  # value_modifier = 1.1

    ("大师拟饵", "由钓鱼大师制作的完美拟饵。", 4, "大幅提高钓鱼成功率, 无消耗",
     0, 1000, 3, 0.20, 0.0, 0.0, 1.0, 1.0, False),  # is_consumable = False

    # --- Rarity 5 (传说) ---
    ("巨物诱饵", "蕴含着远古力量，能吸引庞然大物。", 5, "钓上的鱼最大重量潜力+20%",
     0, 2500, 4, 0.0, 0.0, 0.0, 1.0, 1.0, True),

    ("丰饶号角粉末", "从丰收号角上刮下来的一点粉末。", 5, "下一次钓鱼必定获得双倍数量",
     0, 0, 5, 0.0, 0.0, 0.0, 1.0, 2.0, True)  # quantity_modifier = 2.0
]

ROD_DATA = [
    # Format: (name, description, rarity, source, purchase_cost, quality_mod, quantity_mod, rare_mod, durability, icon_url)
    ("新手木竿", "刚入门时的可靠伙伴", 1, "shop", 50, 1.0, 1.0, 0.0, None, None),
    ("竹制鱼竿", "轻巧耐用", 2, "shop", 500, 1.0, 1.0, 0.01, None, None),
    ("碳素纤维竿", "现代工艺的结晶", 3, "shop", 5000, 1.05, 1.0, 0.03, 1000, None),
    ("星辰钓者", "蕴含星光力量的神秘鱼竿", 4, "gacha", None, 1.1, 1.0, 0.08, None, None),
    ("海神之赐", "传说中海神波塞冬使用过的鱼竿", 5, "gacha", None, 1.2, 1.1, 0.15, None, None),
]

ACCESSORY_DATA = [
    # Format: (name, description, rarity, slot_type, quality_mod, quantity_mod, rare_mod, coin_mod, other_desc, icon_url)
    ("幸运四叶草", "带来好运的小饰品", 2, "general", 1.05, 1.0, 0.01, 1.02, None, None),
    ("渔夫的戒指", "刻有古老符文的戒指", 3, "general", 1.0, 1.0, 0.0, 1.10, None, None),
    ("丰收号角", "象征丰收的魔法号角", 4, "general", 1.10, 1.05, 0.03, 1.15, None, None),
    ("海洋之心", "传说中的宝石，能与海洋生物沟通", 5, "general", 1.20, 1.10, 0.05, 1.25, "大幅减少钓鱼等待时间", None),
]

TITLE_DATA = [
    # Format: (id, name, description, display_format)
    (1, "初出茅庐", "完成第一次钓鱼", "{name}"),
    (2, "垂钓新手", "累计钓上100条鱼", "{name}"),
    (3, "钓鱼达人", "累计钓上500条鱼", "钓鱼达人 {username}"),
    (4, "钓鱼大师", "累计钓上2000条鱼", "钓鱼大师 {username}"),
    (5, "钓鱼宗师", "累计钓上5000条鱼", "宗师·{username}"),
    (6, "鱼类学者", "图鉴收集50种鱼", "鱼类学者 {username}"),
    (7, "图鉴专家", "图鉴收集150种鱼", "{username}图鉴专家"),
    (8, "图鉴大师", "图鉴收集300种鱼", "图鉴大师 {username}"),
    (9, "百万富翁", "累计赚取1,000,000金币", "富有的 {username}"),
    (10, "千万富豪", "累计赚取10,000,000金币", "富豪 {username}"),
    (11, "亿万富豪", "累计赚取100,000,000金币", "亿万富豪·{username}"),
    (12, "区域探索者", "探索过3个不同的钓鱼区域", "{username}探索者"),
    (13, "世界旅行家", "探索过5个不同的钓鱼区域", "旅行家 {username}"),
    (14, "海洋征服者", "探索过全部10个钓鱼区域", "征服者·{username}"),
    (15, "船主", "购买第一艘船", "{name}的船主"),
    (16, "航海家", "拥有3级船舶", "航海家 {username}"),
    (17, "海洋霸主", "拥有5级船舶", "海洋霸主 {username}"),
    (18, "幸运星", "钓到任意8星鱼", "幸运星 {username}"),
    (19, "传说猎手", "钓到全部8星鱼", "传说猎手 {username}"),
    (20, "巨物捕手", "钓到重量超过100kg的鱼", "{username}巨物捕手"),
    (21, "深渊垂钓者", "钓到20种不同的深海鱼类", "深渊垂钓者 {username}"),
]

GACHA_POOL = [
    # Format: (pool_id, name, description, cost_coins, cost_premium_currency)
    (1, "稀有鱼竿池", "有机会获得传说中的鱼竿。", 5000, 0),
    (2, "珍贵饰品池", "有机会获得强大的渔夫饰品。", 10000, 0),
    (3, "每日补给池", "每天可以免费抽取一次，获得实用的消耗品。", 0, 0),
]

ITEM_DATA = [
    # Format: (item_id, name, description, rarity, effect_description, cost, is_consumable, icon_url, effect_type, effect_payload)
    (
        0,
        "小钱袋",
        "一个装有少量金币的袋子。",
        1,
        "使用：获得 1000 金币。",
        0,
        False,
        None,
        "ADD_COINS",
        '{"amount": 1000}',
    ),
    (
        0,
        "幸运药水",
        "一种神奇的药水，能暂时提升你的运气。",
        3,
        "使用：10分钟内，钓到稀有鱼的概率提升5%。",
        0,
        False,
        None,
        "RARE_FISH_BOOST",
        '{"duration_seconds": 600, "multiplier": 0.05}',
    ),
    (
        0,
        "便携式声呐",
        "高科技产品，可以立即执行一次钓鱼。",
        3,
        "使用：立即执行一次钓鱼。",
        0,
        True,
        None,
        "RESET_FISHING_COOLDOWN",
        '{}',
    ),
    (
        0,
        "侠盗的符文",
        "一块刻有模糊不清符文的石片，可以让你再次抓住机会。",
        3,
        "使用：立即重置偷鱼冷却。",
        0,
        True,
        None,
        "RESET_STEAL_COOLDOWN",
        '{}',
    ),
    # 通行证道具
    (
        0,
        "前往神秘海域的通行证",
        "一张神秘的通行证，允许进入未知的神秘海域。",
        5,
        "进入特定钓鱼区域时自动消耗。",
        0,
        False,  # 设置为不可消耗
        None,
        None,  # 移除效果类型
        None,  # 移除效果载荷
    ),
    (
        0,
        "中号钱袋",
        "一个沉甸甸的钱袋，里面装着不少金币。",
        2,
        "使用：获得 10000 金币。",
        0,
        True,
        None,
        "ADD_COINS",
        '{"amount": 10000}',
    ),
    (
        0,
        "大号钱袋",
        "一个鼓鼓囊囊的大钱袋，非常重。",
        3,
        "使用：获得 50000 金币。",
        0,
        True,
        None,
        "ADD_COINS",
        '{"amount": 50000}',
    ),
    (
        0,
        "神秘钱袋",
        "一个会变换重量的神秘钱袋，谁也不知道里面有多少钱。",
        3,
        "使用：随机获得 5000 至 20000 金币。",
        0,
        True,
        None,
        "ADD_COINS",
        '{"min_amount": 5000, "max_amount": 20000}',
    ),
    (
        0,
        "巨型钱袋",
        "一个仿佛装满了全世界财富的巨大袋子。",
        4,
        "使用：随机获得 100000 至 500000 金币！",
        0,
        True,
        None,
        "ADD_COINS",
        '{"min_amount": 100000, "max_amount": 500000}',
    ),
    (
        0,
        "破厄护符·守",
        "铭刻止厄符文，于炼境崩毁之际护其本体无损。",
        4,
        "获得1次精炼保护（放在背包自动生效，毁坏时改判为普通失败，本体保留不降级）。[仅对5星及以下装备生效]",
        0,
        False,
        None,
        "REFINE_DESTRUCTION_SHIELD",
        '{"mode": "keep", "max_rarity": 5}',
    ),
    (
        0,
        "破厄护符·折",
        "折锋化险，代价换生机，于崩毁边缘拉回一线。",
        4,
        "获得1次精炼保护（放在背包自动生效，毁坏时改为降一级并保留本体）。",
        0,
        False,
        None,
        "REFINE_DESTRUCTION_SHIELD",
        '{"mode": "downgrade"}',
    ),
    (
        0,
        "天命护符·神佑",
        "神佑加身，破而不灭。传闻能庇佑至关的一炼。",
        5,
        "获得1次至高保护（放在背包自动生效，任何失败时必改为普通失败，本体保留不降级）。[对所有星级装备均有效]",
        0,
        False,
        None,
        "REFINE_DESTRUCTION_SHIELD",
        '{"mode": "keep"}',
    ),
    (
        0,
        "守护海灵",
        "召唤一个温和的海灵守护你的鱼塘。",
        3,
        "使用：4小时内你的鱼塘不会被其他玩家偷窃。",
        0,
        True,
        None,
        "STEAL_PROTECTION_BUFF",
        '{"duration_hours": 4}',
    ),
    (
        0,
        "时运沙漏",
        "一个能窥见未来片刻的奇妙沙漏。",
        4,
        "拨动命运的流沙，一窥未来的吉凶祸福。",
        0,
        True,
        None,
        "FORECAST_WIPE_BOMB",
        None,
    ),
    # 反制海灵守护的道具
    (
        0,
        "破灵符",
        "一张古老的符咒，蕴含着破除守护的力量。",
        4,
        "使用：1小时内可以穿透海灵守护进行偷窃。",
        0,
        True,
        None,
        "STEAL_PENETRATION_BUFF",
        '{"duration_hours": 1}',
    ),
    (
        0,
        "驱灵香",
        "神秘的香料，能够驱散一切守护之力。",
        5,
        "神秘的香料，能够驱散一切守护之力。",
        0,
        False,
        None,
        "STEAL_PROTECTION_REMOVAL",
        None,
    ),
    (
        0,
        "暗影斗篷",
        "一件神秘的斗篷，能够让你在阴影中行动。",
        3,
        "使用：获得无视海灵守护的反制能力，使用后立即失效。",
        0,
        True,
        None,
        "SHADOW_CLOAK_BUFF",
        '{}',
    ),
]

SHOP_DATA = [
    # Format: (shop_id, name, description, shop_type, is_active, start_time, end_time, sort_order)
    (1, "海鸥港杂货铺", "为水手们提供基础补给的杂货铺。", "normal", True, None, None, 100),
    (2, "七海珍宝阁", "传闻中收藏着来自七个海洋的奇珍异宝。", "premium", True, None, None, 200),
    (3, "幽灵船黑市", "一艘神出鬼没的幽灵船，只在特定的时间出现。", "limited", True, "1492-10-12 00:00:00", "1492-10-12 23:59:59", 300),
]
