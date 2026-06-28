"""
迁移 043: 添加船舶系统

添加 ships 表、user_ships 表和 users 表的 ship_level 字段。
"""


def up(cursor):
    """执行数据库迁移（向上迁移）

    Args:
        cursor: SQLite 游标对象，已在事务中
    """
    try:
        # 检查 ships 表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ships'")
        if not cursor.fetchone():
            print("[MIGRATION 043] 创建 ships 表...")
            cursor.execute("""
                CREATE TABLE ships (
                    ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
                    description TEXT,
                    cost_coins INTEGER NOT NULL DEFAULT 0,
                    required_fish TEXT,
                    max_ocean_zone_level INTEGER DEFAULT 1
                )
            """)
            print("[MIGRATION 043] ships 表创建成功")

            # 插入5级船舶默认数据
            print("[MIGRATION 043] 插入默认船舶数据...")
            cursor.execute("""
                INSERT INTO ships (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
                VALUES ('独木舟', 1, '最简陋的水上工具，勉强能出海。', 10000, '[{"fish_tag":"tropical_rainforest","quantity":5}]', 1)
            """)
            cursor.execute("""
                INSERT INTO ships (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
                VALUES ('小渔船', 2, '木质渔船，适合近海作业。', 50000, '[{"fish_tag":"subtropical_estuary","quantity":10}]', 2)
            """)
            cursor.execute("""
                INSERT INTO ships (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
                VALUES ('机动渔船', 3, '装备了发动机的渔船，航程更远。', 200000, '[{"fish_tag":"temperate_lake","quantity":15}]', 3)
            """)
            cursor.execute("""
                INSERT INTO ships (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
                VALUES ('远洋渔船', 4, '大型远洋捕捞船，能到达深海区域。', 1000000, '[{"fish_tag":"cold_fjord","quantity":20}]', 4)
            """)
            cursor.execute("""
                INSERT INTO ships (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
                VALUES ('极地破冰船', 5, '专为极寒海域设计的特种船只。', 5000000, '[{"fish_tag":"oceanic_ridge","quantity":25}]', 5)
            """)
            print("[MIGRATION 043] 默认船舶数据插入成功")
        else:
            print("[MIGRATION 043] ships 表已存在，跳过")

        # 检查 user_ships 表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_ships'")
        if not cursor.fetchone():
            print("[MIGRATION 043] 创建 user_ships 表...")
            cursor.execute("""
                CREATE TABLE user_ships (
                    user_id TEXT NOT NULL,
                    ship_level INTEGER NOT NULL DEFAULT 0 CHECK (ship_level >= 0 AND ship_level <= 5),
                    obtained_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            print("[MIGRATION 043] user_ships 表创建成功")
        else:
            print("[MIGRATION 043] user_ships 表已存在，跳过")

        # 检查 ship_level 字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if "ship_level" not in columns:
            print("[MIGRATION 043] 添加 ship_level 字段到 users 表...")
            cursor.execute("ALTER TABLE users ADD COLUMN ship_level INTEGER DEFAULT 0")
            print("[MIGRATION 043] ship_level 字段添加成功")
        else:
            print("[MIGRATION 043] ship_level 字段已存在，跳过")

    except Exception as e:
        print(f"[MIGRATION 043] 迁移失败: {e}")
        raise
