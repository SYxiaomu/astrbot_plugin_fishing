"""
迁移 041: 添加自动钓鱼启动时间字段

添加 auto_fishing_start_time 字段用于追踪自动钓鱼的启动时间，
实现单次自动钓鱼最多运行12小时后自动停止的功能。
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

        if "auto_fishing_start_time" not in columns:
            print("[MIGRATION 041] 添加 auto_fishing_start_time 字段...")
            cursor.execute(
                "ALTER TABLE users ADD COLUMN auto_fishing_start_time TEXT"
            )
            print("[MIGRATION 041] 字段添加成功")
        else:
            print("[MIGRATION 041] auto_fishing_start_time 字段已存在，跳过")

    except Exception as e:
        print(f"[MIGRATION 041] 迁移失败: {e}")
        raise
