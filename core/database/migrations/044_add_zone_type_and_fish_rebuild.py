"""
迁移 044: 添加区域类型、背景图和鱼类表改造

为 fishing_zones 表添加 zone_type, required_ship_level, bg_image_path 字段。
重建 fish 表以支持8级稀有度（移除 rarity <= 5 约束），添加 zone_tag 字段。
"""


def up(cursor):
    """执行数据库迁移（向上迁移）

    Args:
        cursor: SQLite 游标对象，已在事务中
    """
    try:
        # ==========================================
        # 1. fishing_zones 表新增字段
        # ==========================================
        cursor.execute("PRAGMA table_info(fishing_zones)")
        columns = [row[1] for row in cursor.fetchall()]

        if "zone_type" not in columns:
            print("[MIGRATION 044] 添加 zone_type 字段到 fishing_zones 表...")
            cursor.execute("ALTER TABLE fishing_zones ADD COLUMN zone_type TEXT DEFAULT 'land'")
            print("[MIGRATION 044] zone_type 字段添加成功")
        else:
            print("[MIGRATION 044] zone_type 字段已存在，跳过")

        if "required_ship_level" not in columns:
            print("[MIGRATION 044] 添加 required_ship_level 字段到 fishing_zones 表...")
            cursor.execute("ALTER TABLE fishing_zones ADD COLUMN required_ship_level INTEGER DEFAULT 0")
            print("[MIGRATION 044] required_ship_level 字段添加成功")
        else:
            print("[MIGRATION 044] required_ship_level 字段已存在，跳过")

        if "bg_image_path" not in columns:
            print("[MIGRATION 044] 添加 bg_image_path 字段到 fishing_zones 表...")
            cursor.execute("ALTER TABLE fishing_zones ADD COLUMN bg_image_path TEXT")
            print("[MIGRATION 044] bg_image_path 字段添加成功")
        else:
            print("[MIGRATION 044] bg_image_path 字段已存在，跳过")

        # ==========================================
        # 2. 重建 fish 表以支持8级稀有度和 zone_tag
        # ==========================================
        print("[MIGRATION 044] 检查 fish 表是否需要重建...")

        # 先检查旧 fish 表的结构
        cursor.execute("PRAGMA table_info(fish)")
        fish_columns = {row[1]: row for row in cursor.fetchall()}

        needs_rebuild = False
        if "zone_tag" not in fish_columns:
            needs_rebuild = True
            print("[MIGRATION 044] fish 表缺少 zone_tag 字段，需要重建表...")

        # 检查是否需要更新稀有度约束
        # 由于 SQLite 的 CHECK 约束无法通过 ALTER TABLE 修改，我们通过表名是否含有限制来判断
        # 只要需要添加 zone_tag 字段，就同时重建表
        if needs_rebuild:
            print("[MIGRATION 044] 正在重建 fish 表（添加 zone_tag，移除旧稀有度约束）...")

            # 先清除外键引用数据（玩家库存和钓鱼记录中的鱼类引用）
            print("[MIGRATION 044] 清除旧鱼类引用数据...")
            cursor.execute("DELETE FROM user_fish_inventory")
            cursor.execute("DELETE FROM user_aquarium")
            cursor.execute("DELETE FROM fishing_records")
            cursor.execute("DELETE FROM zone_fish_mapping")
            cursor.execute("DELETE FROM user_fish_stats")

            # 创建新 fish 表（支持稀有度1-8，添加 zone_tag 字段）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fish_new (
                    fish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    rarity INTEGER NOT NULL CHECK (rarity >= 1 AND rarity <= 8),
                    base_value INTEGER NOT NULL,
                    min_weight INTEGER NOT NULL CHECK (min_weight >= 0),
                    max_weight INTEGER NOT NULL CHECK (max_weight > min_weight),
                    icon_url TEXT,
                    zone_tag TEXT
                )
            """)

            # 不需要复制旧数据（即将全部重写）
            print("[MIGRATION 044] 旧 fish 表数据已被清除")

            # 删除旧表
            cursor.execute("DROP TABLE IF EXISTS fish")
            # 重命名新表
            cursor.execute("ALTER TABLE fish_new RENAME TO fish")
            print("[MIGRATION 044] fish 表重建完成")

            # 重建索引
            print("[MIGRATION 044] 重建鱼表索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fish_rarity ON fish(rarity)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fish_zone_tag ON fish(zone_tag)
            """)
            print("[MIGRATION 044] 鱼表索引重建完成")
        else:
            print("[MIGRATION 044] fish 表已包含所需字段，跳过")

    except Exception as e:
        print(f"[MIGRATION 044] 迁移失败: {e}")
        raise
