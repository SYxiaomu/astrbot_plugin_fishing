import json
from typing import Optional, Dict, Any, List

from astrbot.api import logger

from ..domain.models import User, Ship, UserShip, FishingZone
from ..repositories.abstract_repository import (
    AbstractUserRepository,
    AbstractShipRepository,
    AbstractItemTemplateRepository,
    AbstractInventoryRepository,
)


class ShipService:
    """船舶系统业务服务"""

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        ship_repo: AbstractShipRepository,
        item_template_repo: AbstractItemTemplateRepository,
        inventory_repo: AbstractInventoryRepository,
    ):
        self.user_repo = user_repo
        self.ship_repo = ship_repo
        self.item_template_repo = item_template_repo
        self.inventory_repo = inventory_repo

    def get_user_ship_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户的船舶信息"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        user_ship = self.ship_repo.get_user_ship(user_id)
        current_level = user_ship.ship_level if user_ship else 0

        all_ships = self.ship_repo.get_all_ships()

        ship_info = []
        for ship in all_ships:
            status = "已拥有" if ship.level <= current_level else "未拥有"
            if ship.level == current_level:
                status = "当前使用"
            elif ship.level == current_level + 1:
                status = "可升级"

            can_afford = False
            if ship.level > current_level:
                cost_coins = ship.cost_coins
                required_fish_info = self._parse_required_fish(ship.required_fish)
                can_afford = user.coins >= cost_coins
            else:
                cost_coins = 0
                required_fish_info = []

            ship_info.append({
                "level": ship.level,
                "name": ship.name,
                "description": ship.description,
                "cost_coins": cost_coins,
                "required_fish": required_fish_info,
                "max_ocean_zone": ship.max_ocean_zone_level,
                "status": status,
                "can_afford": can_afford,
            })

        return {
            "success": True,
            "current_level": current_level,
            "ships": ship_info,
        }

    def buy_or_upgrade_ship(self, user_id: str) -> Dict[str, Any]:
        """用户购买船舶（从0→1）或升级船舶（n→n+1）"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        user_ship = self.ship_repo.get_user_ship(user_id)
        current_level = user_ship.ship_level if user_ship else 0

        # 检查是否已满级
        if current_level >= 5:
            return {"success": False, "message": "⚠️ 您已经拥有最高级船舶，无需升级！"}

        target_level = current_level + 1
        target_ship = self.ship_repo.get_ship_by_level(target_level)
        if not target_ship:
            return {"success": False, "message": "❌ 船舶数据不存在，请联系管理员。"}

        # 检查金币
        if user.coins < target_ship.cost_coins:
            return {
                "success": False,
                "message": f"❌ 金币不足！需要 {target_ship.cost_coins} 金币，您当前有 {user.coins} 金币。"
            }

        # 检查所需鱼类
        if target_ship.required_fish:
            try:
                requirements = json.loads(target_ship.required_fish)
            except (json.JSONDecodeError, TypeError):
                requirements = []

            for req in requirements:
                fish_tag = req.get("fish_tag")
                quantity = req.get("quantity", 1)

                # 通过 zone_tag 查找对应的鱼
                fish_list = self._get_fish_by_tag(fish_tag)
                if not fish_list:
                    return {
                        "success": False,
                        "message": f"❌ 找不到标签为 {fish_tag} 的鱼类数据。"
                    }

                # 检查用户是否拥有足够的该类鱼
                total_quantity = 0
                user_inventory = self.inventory_repo.get_fish_inventory(user_id)
                for inv_item in user_inventory:
                    fish = self.item_template_repo.get_fish_by_id(inv_item.fish_id)
                    if fish and fish.zone_tag == fish_tag:
                        total_quantity += inv_item.quantity

                if total_quantity < quantity:
                    return {
                        "success": False,
                        "message": f"❌ 需要 {quantity} 条 {fish_tag}区域的鱼，当前拥有 {total_quantity} 条。"
                    }

            # 扣除所需鱼类
            for req in requirements:
                fish_tag = req.get("fish_tag")
                quantity = req.get("quantity", 1)
                deducted = 0
                user_inventory = self.inventory_repo.get_fish_inventory(user_id)
                for inv_item in user_inventory:
                    if deducted >= quantity:
                        break
                    fish = self.item_template_repo.get_fish_by_id(inv_item.fish_id)
                    if fish and fish.zone_tag == fish_tag:
                        to_deduct = min(quantity - deducted, inv_item.quantity)
                        self.inventory_repo.update_fish_quantity(
                            user_id, inv_item.fish_id, -to_deduct, inv_item.quality_level
                        )
                        deducted += to_deduct

        # 扣除金币
        user.coins -= target_ship.cost_coins
        self.user_repo.update(user)

        # 更新用户船舶信息
        from datetime import datetime
        new_user_ship = UserShip(
            user_id=user_id,
            ship_level=target_level,
            obtained_at=datetime.now()
        )
        self.ship_repo.upsert_user_ship(new_user_ship)

        # 同步更新 User 模型的 ship_level
        user.ship_level = target_level
        self.user_repo.update(user)

        action = "购买" if current_level == 0 else "升级"
        return {
            "success": True,
            "message": f"✅ 成功{action}【{target_ship.name}】（等级 {target_level}）！"
        }

    def can_access_zone(self, user_id: str, zone: FishingZone) -> bool:
        """检查用户是否可以访问指定区域"""
        # 陆地区域总是可访问（不需要船）
        if zone.zone_type == "land":
            return True

        # 海洋区域需要检查船舶等级
        required_level = zone.required_ship_level or 0
        if required_level == 0:
            # ocean zone 1 (coastal_bay) - 一级船即可
            required_level = 1

        user_ship = self.ship_repo.get_user_ship(user_id)
        current_level = user_ship.ship_level if user_ship else 0

        return current_level >= required_level

    def get_required_ship_for_zone(self, zone: FishingZone) -> Optional[int]:
        """获取访问区域所需的船舶等级"""
        if zone.zone_type == "land":
            return 0
        return max(zone.required_ship_level or 0, 1)

    def _parse_required_fish(self, required_fish_str: Optional[str]) -> List[Dict[str, Any]]:
        """解析 required_fish JSON 字符串"""
        if not required_fish_str:
            return []
        try:
            return json.loads(required_fish_str)
        except (json.JSONDecodeError, TypeError):
            return []

    def _get_fish_by_tag(self, tag: str) -> List:
        """根据 zone_tag 获取鱼类模板列表"""
        all_fish = self.item_template_repo.get_all_fish()
        return [f for f in all_fish if f.zone_tag == tag]
