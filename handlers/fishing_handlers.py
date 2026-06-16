import os
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger
from ..core.utils import get_now
from ..utils import safe_datetime_handler, to_percentage, safe_get_file_path
from ..draw.pokedex import draw_pokedex
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import FishingPlugin


def _normalize_now_for(lst_time):
    """根据 lst_time 的时区信息，规范化当前时间的 tzinfo。"""
    now = get_now()
    if lst_time and lst_time.tzinfo is None and now.tzinfo is not None:
        return now.replace(tzinfo=None)
    if lst_time and lst_time.tzinfo is not None and now.tzinfo is None:
        return now.replace(tzinfo=lst_time.tzinfo)
    return now


def _compute_cooldown_seconds(base_seconds, equipped_accessory):
    """根据是否装备海洋之心动态计算冷却时间。"""
    if equipped_accessory and equipped_accessory.get("name") == "海洋之心":
        return base_seconds / 2
    return base_seconds


def _build_fish_message(result, fishing_cost):
    if result["success"]:
        fish = result['fish']
        # 构建品质显示
        quality_display = ""
        if fish.get('quality_level') == 1:
            quality_display = " ✨高品质"

        message = (
            f"🎣 恭喜你钓到了：{fish['name']}{quality_display}\n"
            f"✨稀有度：{'★' * fish['rarity']} \n"
            f"⚖️重量：{fish['weight']} 克\n"
            f"💰价值：{fish['value']} 金币\n"
            f"💸消耗：{fishing_cost} 金币/次"
        )
        if "equipment_broken_messages" in result:
            for broken_msg in result["equipment_broken_messages"]:
                message += f"\n{broken_msg}"
        return message
    return f"{result['message']}\n💸消耗：{fishing_cost} 金币/次"


class FishingHandlers:
    def __init__(self, plugin: "FishingPlugin"):
        self.plugin = plugin
        self.user_service = plugin.user_service
        self.fishing_service = plugin.fishing_service
        self.inventory_service = plugin.inventory_service
        self.gacha_service = plugin.gacha_service
        self.market_service = plugin.market_service
        self.shop_service = plugin.shop_service
        self.item_template_repo = plugin.item_template_repo
        self.achievement_service = plugin.achievement_service
        self.aquarium_service = plugin.aquarium_service
        self.exchange_service = plugin.exchange_service

    def _get_fishing_cost(self, user):
        zone = self.plugin.inventory_repo.get_zone_by_id(user.fishing_zone_id)
        return zone.fishing_cost if zone else 10

    async def auto_fish(self, event: AstrMessageEvent):
        """切换自动钓鱼状态"""
        user_id = self.plugin._get_effective_user_id(event)
        result = self.fishing_service.toggle_auto_fishing(user_id)

        if result["success"]:
            yield event.plain_result(result["message"])
        else:
            yield event.plain_result(result["message"])

    async def fishing_area(self, event: AstrMessageEvent):
        """查看所有钓鱼区域和切换钓鱼区域。用法：钓鱼区域 [区域编号]"""
        user_id = self.plugin._get_effective_user_id(event)

        # 获取用户信息
        user = self.plugin.user_repo.get_by_id(user_id)
        if not user:
            yield event.plain_result("❌ 您还没有注册，请先使用 /注册 命令注册。")
            return

        # 解析参数
        message_str = event.message_str.strip()
        parts = message_str.split()

        # 如果没有参数，显示所有区域
        if len(parts) <= 1:
            zones_info = self.fishing_service.get_user_fishing_zones(user_id)
            if not zones_info["success"]:
                yield event.plain_result(f"❌ {zones_info['message']}")
                return

            zones = zones_info["zones"]
            current_zone = next((z for z in zones if z["whether_in_use"]), None)

            # 构建消息
            message = "🗺️ **钓鱼区域列表**\n\n"
            if current_zone:
                message += f"📍 当前区域：{current_zone['name']}\n\n"

            for zone in zones:
                status_icon = "📍" if zone["whether_in_use"] else "⬜"
                active_icon = "✅" if zone["is_active"] else "❌"

                message += f"{status_icon} {zone['zone_id']}. {zone['name']} {active_icon}\n"
                message += f"   💰 钓鱼费用：{zone['fishing_cost']} 金币\n"

                if zone["requires_pass"]:
                    message += f"   🔑 需要通行证：{zone['required_item_name']}\n"

                if zone["daily_rare_fish_quota"] > 0:
                    remaining = zone["daily_rare_fish_quota"] - zone["rare_fish_caught_today"]
                    message += f"   🐟 稀有鱼剩余：{remaining}/{zone['daily_rare_fish_quota']}\n"

                if zone["available_from"]:
                    message += f"   ⏰ 开放时间：{zone['available_from'].strftime('%m-%d %H:%M')}"
                    if zone["available_until"]:
                        message += f" ~ {zone['available_until'].strftime('%m-%d %H:%M')}"
                    message += "\n"

                message += "\n"

            message += "💡 使用 /钓鱼区域 编号 切换到指定区域"
            yield event.plain_result(message)
        else:
            # 有参数，尝试切换区域
            try:
                zone_id = int(parts[1])
            except ValueError:
                yield event.plain_result("❌ 区域编号必须是数字")
                return

            result = self.fishing_service.set_user_fishing_zone(user_id, zone_id)
            if result["success"]:
                yield event.plain_result(f"✅ {result['message']}")
            else:
                yield event.plain_result(f"❌ {result['message']}")

    async def fish(self, event: AstrMessageEvent):
        """钓鱼"""
        user_id = self.plugin._get_effective_user_id(event)
        user = self.plugin.user_repo.get_by_id(user_id)
        if not user:
            yield event.plain_result("❌ 您还没有注册，请先使用 /注册 命令注册。")
            return
        # 检查用户钓鱼CD
        lst_time = user.last_fishing_time
        info = self.user_service.get_user_current_accessory(user_id)
        if info["success"] is False:
            yield event.plain_result(f"❌ 获取用户饰品信息失败：{info['message']}")
            return
        equipped_accessory = info.get("accessory")
        base_cooldown = self.plugin.game_config["fishing"]["cooldown_seconds"]
        cooldown_seconds = _compute_cooldown_seconds(base_cooldown, equipped_accessory)
        # 修复时区问题
        now = _normalize_now_for(lst_time)
        if lst_time and (now - lst_time).total_seconds() < cooldown_seconds:
            wait_time = cooldown_seconds - (now - lst_time).total_seconds()
            yield event.plain_result(f"⏳ 您还需要等待 {int(wait_time)} 秒才能再次钓鱼。")
            return
        fishing_cost = self._get_fishing_cost(user)
        result = self.fishing_service.go_fish(user_id)
        if not result:
            yield event.plain_result("❌ 出错啦！请稍后再试。")
            return

        # 生成钓鱼结果图片
        try:
            from ..draw.fishing_result import draw_fishing_result_image

            fish = result['fish']
            coins_modifier = self.inventory_service._calculate_coins_modifier(user)

            fish_data = {
                'name': fish['name'],
                'rarity': fish['rarity'],
                'weight': fish['weight'],
                'value': fish['value'],
                'quality_level': fish.get('quality_level', 0),
                'fish_id': fish.get('fish_id', 0),
                'quantity': fish.get('quantity', 1)
            }

            user_data = {
                'user_id': user_id,
                'nickname': user.nickname or user_id,
                'fishing_cost': fishing_cost,
                'coins_modifier': coins_modifier
            }

            image = await draw_fishing_result_image(fish_data, user_data)
            image_path = os.path.join(self.plugin.tmp_dir, "fishing_result.png")
            image.save(image_path)
            yield event.image_result(image_path)

            # 如果有装备损坏消息，额外发送文本提示
            if "equipment_broken_messages" in result:
                for broken_msg in result["equipment_broken_messages"]:
                    yield event.plain_result(broken_msg)
        except Exception as e:
            logger.error(f"生成钓鱼结果图片时发生错误: {e}", exc_info=True)
            # 回退到文本消息
            yield event.plain_result(_build_fish_message(result, fishing_cost))
