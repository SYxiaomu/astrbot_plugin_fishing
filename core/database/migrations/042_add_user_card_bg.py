"""
迁移 042: 添加用户自定义卡片背景字段

添加 card_bg_path 字段用于存储用户自定义的信息卡片背景图路径。
"""


def up(cursor):
    """执行数据库迁移（向上迁移）

    Args:
        cursor: SQLite 游标对象，已在事务中
    """
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if "card_bg_path" not in columns:
            print("[MIGRATION 042] 添加 card_bg_path 字段...")
            cursor.execute(
                "ALTER TABLE users ADD COLUMN card_bg_path TEXT"
            )
            print("[MIGRATION 042] 字段添加成功")
        else:
            print("[MIGRATION 042] card_bg_path 字段已存在，跳过")

    except Exception as e:
        print(f"[MIGRATION 042] 迁移失败: {e}")
        raise
