import sqlite3
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..domain.models import Ship, UserShip
from .abstract_repository import AbstractShipRepository


class SqliteShipRepository(AbstractShipRepository):
    """船舶仓储的SQLite实现"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()

    def _get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        return conn

    def _row_to_ship(self, row: sqlite3.Row) -> Optional[Ship]:
        if not row:
            return None
        return Ship(
            ship_id=row["ship_id"],
            name=row["name"],
            level=row["level"],
            description=row["description"],
            cost_coins=row["cost_coins"],
            required_fish=row["required_fish"],
            max_ocean_zone_level=row["max_ocean_zone_level"]
        )

    def _row_to_user_ship(self, row: sqlite3.Row) -> Optional[UserShip]:
        if not row:
            return None

        def parse_dt(val):
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        try:
                            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            return None
            return None

        return UserShip(
            user_id=row["user_id"],
            ship_level=row["ship_level"],
            obtained_at=parse_dt(row["obtained_at"]) if "obtained_at" in row.keys() else None
        )

    def get_all_ships(self) -> List[Ship]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ships ORDER BY level ASC")
            return [self._row_to_ship(row) for row in cursor.fetchall()]

    def get_ship_by_level(self, level: int) -> Optional[Ship]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ships WHERE level = ?", (level,))
            return self._row_to_ship(cursor.fetchone())

    def get_ship_by_id(self, ship_id: int) -> Optional[Ship]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ships WHERE ship_id = ?", (ship_id,))
            return self._row_to_ship(cursor.fetchone())

    def add_ship(self, ship_data: Dict[str, Any]) -> Ship:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ships (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
                VALUES (:name, :level, :description, :cost_coins, :required_fish, :max_ocean_zone_level)
            """, {
                "name": ship_data["name"],
                "level": ship_data["level"],
                "description": ship_data.get("description"),
                "cost_coins": ship_data.get("cost_coins", 0),
                "required_fish": ship_data.get("required_fish"),
                "max_ocean_zone_level": ship_data.get("max_ocean_zone_level", 1)
            })
            conn.commit()
            ship_id = cursor.lastrowid
            return self.get_ship_by_id(ship_id)

    def update_ship(self, ship_id: int, ship_data: Dict[str, Any]) -> None:
        ship_data["ship_id"] = ship_id
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ships SET
                    name = :name, level = :level, description = :description,
                    cost_coins = :cost_coins, required_fish = :required_fish,
                    max_ocean_zone_level = :max_ocean_zone_level
                WHERE ship_id = :ship_id
            """, ship_data)
            conn.commit()

    def delete_ship(self, ship_id: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ships WHERE ship_id = ?", (ship_id,))
            conn.commit()

    def get_user_ship(self, user_id: str) -> Optional[UserShip]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_ships WHERE user_id = ?", (user_id,))
            return self._row_to_user_ship(cursor.fetchone())

    def upsert_user_ship(self, user_ship: UserShip) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_ships (user_id, ship_level, obtained_at)
                VALUES (:user_id, :ship_level, :obtained_at)
                ON CONFLICT(user_id) DO UPDATE SET
                    ship_level = :ship_level,
                    obtained_at = :obtained_at
            """, {
                "user_id": user_ship.user_id,
                "ship_level": user_ship.ship_level,
                "obtained_at": user_ship.obtained_at or datetime.now()
            })
            conn.commit()
