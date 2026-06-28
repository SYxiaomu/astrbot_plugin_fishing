"""
迁移 045: 更新钓鱼区域为10个完整区域

替换旧的3个区域（新手港湾、深海峡谷、传说之海）为完整的10个区域，
包括区域类型(zone_type)、船舶等级要求(required_ship_level)、
稀有度分布配置、钓鱼消耗等。
"""

import json
import sqlite3


def up(cursor: sqlite3.Cursor):
    # ==========================================
    # 1. 清空旧区域关联数据和区域数据
    # ==========================================
    cursor.execute("DELETE FROM zone_fish_mapping")
    cursor.execute("DELETE FROM fishing_zones")

    # ==========================================
    # 2. 插入10个新区域
    # ==========================================
    zones = [
        # (id, name, description, daily_rare_fish_quota, zone_type, required_ship_level, fishing_cost, is_active, configs_json)
        # --- 陆地区域 (1-5) ---
        (1, "热带雨林溪流",
         "高温多雨的热带雨林溪流，物种极其丰富，适合新手钓鱼。",
         50, 'land', 0, 10, 1,
         json.dumps({"rarity_distribution": [0.60, 0.30, 0.08, 0.02, 0.00, 0.00]})),

        (2, "亚热带河口湿地",
         "温暖湿润的河口湿地，咸淡水交汇处鱼种丰富。",
         50, 'land', 0, 20, 1,
         json.dumps({"rarity_distribution": [0.55, 0.30, 0.10, 0.04, 0.01, 0.00]})),

        (3, "温带平原湖泊",
         "四季分明的温带大型湖泊，水域广阔，鱼类多样。",
         50, 'land', 0, 30, 1,
         json.dumps({"rarity_distribution": [0.50, 0.30, 0.12, 0.06, 0.02, 0.00]})),

        (4, "寒带针叶林河流",
         "寒冷漫长的寒带河流，水质清澈，生长着耐寒鱼类。",
         50, 'land', 0, 40, 1,
         json.dumps({"rarity_distribution": [0.45, 0.30, 0.15, 0.08, 0.02, 0.00]})),

        (5, "干旱区内陆盐湖",
         "干旱少雨的内陆盐湖，高盐碱度环境下生存着特殊鱼类。",
         50, 'land', 0, 50, 1,
         json.dumps({"rarity_distribution": [0.40, 0.30, 0.18, 0.10, 0.02, 0.00]})),

        # --- 海洋区域 (6-10) ---
        (6, "近岸浅湾",
         "风平浪静的近岸浅湾，阳光充足，适合近海垂钓。",
         100, 'ocean', 1, 60, 1,
         json.dumps({"rarity_distribution": [0.35, 0.30, 0.20, 0.12, 0.03, 0.00]})),

        (7, "大陆架渔场",
         "营养丰富的大陆架渔场，鱼群密集，是重要的渔业区。",
         150, 'ocean', 2, 80, 1,
         json.dumps({"rarity_distribution": [0.30, 0.25, 0.20, 0.18, 0.05, 0.02]})),

        (8, "寒带峡湾",
         "冰川侵蚀形成的深邃峡湾，宁静而神秘。",
         150, 'ocean', 3, 100, 1,
         json.dumps({"rarity_distribution": [0.25, 0.25, 0.20, 0.20, 0.08, 0.02]})),

        (9, "远洋海岭",
         "远离大陆的深海海岭，巨型鱼类出没的深海孤寂之地。",
         200, 'ocean', 4, 150, 1,
         json.dumps({"rarity_distribution": [0.20, 0.20, 0.20, 0.22, 0.13, 0.05]})),

        (10, "极地冰缘海",
         "极寒刺骨的极地冰缘海域，浮冰遍布，隐藏着远古生物。",
         200, 'ocean', 5, 200, 1,
         json.dumps({"rarity_distribution": [0.10, 0.15, 0.25, 0.25, 0.15, 0.10]})),
    ]

    for z in zones:
        zone_id, name, description, quota, zone_type, ship_lv, cost, active, configs = z
        cursor.execute("""
            INSERT INTO fishing_zones
                (id, name, description, daily_rare_fish_quota, rare_fish_caught_today,
                 configs, is_active, required_item_id, requires_pass,
                 fishing_cost, zone_type, required_ship_level, bg_image_path)
            VALUES (?, ?, ?, ?, 0, ?, ?, NULL, 0, ?, ?, ?, NULL)
        """, (zone_id, name, description, quota, configs, active, cost, zone_type, ship_lv))

    print("[MIGRATION 045] 已更新10个钓鱼区域数据")


def down(cursor: sqlite3.Cursor):
    cursor.execute("DELETE FROM zone_fish_mapping")
    cursor.execute("DELETE FROM fishing_zones")

    zones_to_add = [
        (1, "区域一：新手港湾", "只能钓到0-4星鱼，4星鱼概率很低。", 50),
        (2, "区域二：深海峡谷", "4星鱼概率提升，有极小概率钓到5星鱼。", 2000),
        (3, "区域三：传说之海", "5星鱼概率大幅提升。", 500)
    ]
    cursor.executemany(
        "INSERT INTO fishing_zones (id, name, description, daily_rare_fish_quota) VALUES (?, ?, ?, ?)",
        zones_to_add
    )
    print("[MIGRATION 045] 已恢复旧的3个钓鱼区域")
