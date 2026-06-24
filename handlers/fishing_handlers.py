import os
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger
from ..core.utils import get_now
from ..utils import safe_datetime_handler, to_percentage, safe_get_file_path, format_rarity_display
from ..draw.pokedex import draw_pokedex
from ..draw.message_renderer import draw_message_image, save_message_image
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
        user = self.plugin.user_repo.get_by_id(user_id)
        nickname = user.nickname if user else user_id
        status = "success" if result["success"] else "error"
        image = await draw_message_image(
            result["message"], title_text="🎣自动钓鱼",
            user_id=user_id, nickname=nickname, data_dir=self.plugin.data_dir,
            status_type=status
        )
        image_path = save_message_image(image, "auto_fish", self.plugin.data_dir)
        yield event.image_result(image_path)

    async def fish_pokedex(self, event: AstrMessageEvent):
        """查看鱼类图鉴"""
        user_id = self.plugin._get_effective_user_id(event)
        user = self.plugin.user_repo.get_by_id(user_id)
        if not user:
            yield event.plain_result("❌ 您还没有注册，请先使用 /注册 命令注册。")
            return

        # 解析页数参数
        args = event.message_str.strip().split()
        page = 1
        if len(args) >= 2:
            try:
                page = int(args[1])
                if page < 1:
                    page = 1
            except ValueError:
                yield event.plain_result("❌ 页码格式错误！用法：/图鉴 [页码]")
                return

        # 获取图鉴数据
        pokedex_data = self.fishing_service.get_user_pokedex(user_id)
        if not pokedex_data.get("success", False):
            yield event.plain_result(f"❌ {pokedex_data.get('message', '获取图鉴数据失败')}")
            return

        pokedex_list = pokedex_data.get("pokedex", [])
        if not pokedex_list:
            yield event.plain_result("🐟 您还没有钓到任何鱼，快去钓鱼吧！")
            return

        # 生成图鉴图片
        try:
            user_info = {
                'user_id': user_id,
                'nickname': user.nickname or user_id,
            }
            output_path = os.path.join(self.plugin.tmp_dir, "pokedex.png")
            await draw_pokedex(pokedex_data, user_info, output_path, page=page, data_dir=self.plugin.data_dir)
            yield event.image_result(output_path)
        except Exception as e:
            logger.error(f"生成图鉴图片时发生错误: {e}", exc_info=True)
            # 回退到文本消息
            message = "📖 **鱼类图鉴**\n\n"
            total_fish = pokedex_data.get('total_fish_count', 0)
            unlocked = pokedex_data.get('unlocked_fish_count', 0)
            # 简单分页文本
            FISH_PER_PAGE = 20
            start_idx = (page - 1) * FISH_PER_PAGE
            end_idx = start_idx + FISH_PER_PAGE
            page_fishes = pokedex_list[start_idx:end_idx]
            for fish in page_fishes:
                message += f"- {fish['name']} ({format_rarity_display(fish['rarity'])})\n"
            total_pages = (len(pokedex_list) + FISH_PER_PAGE - 1) // FISH_PER_PAGE
            message += f"\n📊 收集进度: {unlocked}/{total_fish}\n"
            message += f"◈ 第 {page}/{total_pages} 页 - 使用 /图鉴 [页码] 查看更多 ◈"
            yield event.plain_result(message)

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

            try:
                from ..draw.fishing_area import draw_fishing_area_image

                # 准备用户数据（带头像支持）
                user_data = {
                    'user_id': user_id,
                    'nickname': user.nickname or user_id,
                    'current_zone_name': current_zone['name'] if current_zone else '无',
                }

                # 生成图片
                image = await draw_fishing_area_image(zones, user_data, self.plugin.data_dir)
                image_path = os.path.join(self.plugin.tmp_dir, "fishing_area.png")
                image.save(image_path)
                yield event.image_result(image_path)
            except Exception as e:
                from astrbot.api import logger
                logger.error(f"生成钓鱼区域图片时发生错误: {e}", exc_info=True)

                # 回退到文本消息
                message = "🗺️**钓鱼区域列表**\n\n"
                if current_zone:
                    message += f"📍当前区域：{current_zone['name']}\n\n"

                for zone in zones:
                    status_icon = "📍"if zone["whether_in_use"] else "⬜"
                    active_icon = "✅"if zone["is_active"] else "❌"

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
            user = self.plugin.user_repo.get_by_id(user_id)
            nickname = user.nickname if user else user_id
            status = "success" if result["success"] else "error"
            image = await draw_message_image(
                result["message"], title_text="🗺️切换区域",
                user_id=user_id, nickname=nickname, data_dir=self.plugin.data_dir,
                status_type=status
            )
            image_path = save_message_image(image, "fishing_zone", self.plugin.data_dir)
            yield event.image_result(image_path)

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

            image = await draw_fishing_result_image(fish_data, user_data, data_dir=self.plugin.data_dir)
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
