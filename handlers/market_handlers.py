import os
from astrbot.api.event import filter, AstrMessageEvent
from ..utils import format_rarity_display, parse_target_user_id, parse_amount
from ..draw.sell_result import draw_sell_result, draw_coins_balance
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import FishingPlugin


async def _sell_image_result(plugin, event, result, prefix: str):
    """通用出售结果图片输出辅助函数"""
    user_id = plugin._get_effective_user_id(event)
    user = plugin.user_repo.get_by_id(user_id)
    nickname = user.nickname if user else user_id
    image = await draw_sell_result(
        result["message"],
        user_id=user_id,
        nickname=nickname,
        data_dir=plugin.data_dir
    )
    image_path = os.path.join(plugin.tmp_dir, f"{prefix}_{user_id}.png")
    image.save(image_path)
    return image_path


async def sell_all(plugin: "FishingPlugin", event: AstrMessageEvent):
    """卖出用户所有鱼"""
    user_id = plugin._get_effective_user_id(event)
    if result := plugin.inventory_service.sell_all_fish(user_id):
        image_path = await _sell_image_result(plugin, event, result, "sell_all")
        yield event.image_result(image_path)
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def sell_keep(plugin: "FishingPlugin", event: AstrMessageEvent):
    """卖出用户鱼，但保留每种鱼一条"""
    user_id = plugin._get_effective_user_id(event)
    if result := plugin.inventory_service.sell_all_fish(user_id, keep_one=True):
        image_path = await _sell_image_result(plugin, event, result, "sell_keep")
        yield event.image_result(image_path)
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def sell_everything(plugin: "FishingPlugin", event: AstrMessageEvent):
    """砸锅卖铁：出售所有未锁定且未装备的鱼竿、饰品和全部鱼类"""
    user_id = plugin._get_effective_user_id(event)
    if result := plugin.inventory_service.sell_everything_except_locked(user_id):
        if result["success"]:
            image_path = await _sell_image_result(plugin, event, result, "sell_everything")
            yield event.image_result(image_path)
        else:
            yield event.plain_result(f"❌ 砸锅卖铁失败：{result['message']}")
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def sell_by_rarity(plugin: "FishingPlugin", event: AstrMessageEvent):
    """按一个或多个稀有度出售鱼"""
    user_id = plugin._get_effective_user_id(event)
    args = event.message_str.split()  # 使用 split() 可以更好地处理多个空格

    # 至少需要 "出售稀有度" + 1个数字
    if len(args) < 2:
        yield event.plain_result(
            "❌ 用法：出售稀有度 <稀有度1> [稀有度2] ...\n例如：出售稀有度 3 4 5"
        )
        return

    try:
        # 从第二个参数开始，解析所有数字
        rarities = [int(num) for num in args[1:]]

        # 验证所有数字是否在1-10之间
        if not all(1 <= r <= 10 for r in rarities):
            yield event.plain_result("❌ 稀有度必须是1到10之间的数字，请检查后重试。")
            return

        # 根据解析出的稀有度数量，调用不同的服务
        if len(rarities) == 1:
            # 只有一个稀有度，调用单稀有度出售方法
            result = plugin.inventory_service.sell_fish_by_rarity(
                user_id, rarities[0]
            )
        else:
            # 有多个稀有度，调用多稀有度出售方法
            result = plugin.inventory_service.sell_fish_by_rarities(user_id, rarities)

        # 统一处理返回结果
        if result:
            image_path = await _sell_image_result(plugin, event, result, "sell_rarity")
            yield event.image_result(image_path)
        else:
            yield event.plain_result("❌ 出错啦！请稍后再试。")

    except ValueError:
        yield event.plain_result("❌ 请确保输入的是有效的数字，并用空格隔开。")
    except Exception as e:
        yield event.plain_result(f"❌ 处理命令时发生未知错误: {e}")


async def sell_all_rods(plugin: "FishingPlugin", event: AstrMessageEvent):
    """出售用户所有鱼竿"""
    user_id = plugin._get_effective_user_id(event)
    result = plugin.inventory_service.sell_all_rods(user_id)
    if result:
        image_path = await _sell_image_result(plugin, event, result, "sell_rods")
        yield event.image_result(image_path)
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def sell_all_accessories(plugin: "FishingPlugin", event: AstrMessageEvent):
    """出售用户所有饰品"""
    user_id = plugin._get_effective_user_id(event)
    result = plugin.inventory_service.sell_all_accessories(user_id)
    if result:
        image_path = await _sell_image_result(plugin, event, result, "sell_accessories")
        yield event.image_result(image_path)
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def shop(plugin: "FishingPlugin", event: AstrMessageEvent):
    """查看商店：/商店 [商店ID]"""
    args = event.message_str.split(" ")
    # /商店 → 列表 → 图片输出
    if len(args) == 1:
        result = plugin.shop_service.get_shops()
        if not result or not result.get("success"):
            yield event.plain_result("❌ 出错啦！请稍后再试。")
            return
        shops = result.get("shops", [])
        if not shops:
            yield event.plain_result("🛒 当前没有开放的商店。")
            return

        # 对商店列表进行排序：按 sort_order 升序，然后按 shop_id 升序
        shops.sort(key=lambda x: (x.get("sort_order", 999), x.get("shop_id", 999)))

        try:
            from ..draw.shop import draw_shop_list_image

            image = await draw_shop_list_image(shops)
            image_path = os.path.join(plugin.tmp_dir, "shop_list.png")
            image.save(image_path)
            yield event.image_result(image_path)
        except Exception as e:
            from astrbot.api import logger
            logger.error(f"生成商店列表图片时发生错误: {e}", exc_info=True)
            # 回退到文本输出
            msg = "【🛒 商店列表】\n"
            for s in shops:
                stype = s.get("shop_type", "normal")
                type_name = "普通" if stype == "normal" else ("高级" if stype == "premium" else "限时")
                status = "🟢 营业中" if s.get("is_active") else "🔴 已关闭"
                msg += f" - {s.get('name')} (ID: {s.get('shop_id')}) [{type_name}] {status}\n"
                if s.get("description"):
                    msg += f"   - {s.get('description')}\n"
            msg += "\n💡 使用「商店 商店ID」查看详情；使用「商店购买 商店ID 商品ID [数量]」购买\n"
            yield event.plain_result(msg)
        return

    # /商店 <ID> → 详情 → 图片输出
    shop_id = args[1]
    if not shop_id.isdigit():
        yield event.plain_result("❌ 商店ID必须是数字")
        return
    detail = plugin.shop_service.get_shop_details(int(shop_id))
    if not detail.get("success"):
        yield event.plain_result(f"❌ {detail.get('message','查询失败')}")
        return
    shop = detail["shop"]
    items = detail.get("items", [])

    if not items:
        msg = f"【🛒 {shop.get('name')}】(ID: {shop.get('shop_id')})\n"
        if shop.get("description"):
            msg += f"📖 {shop.get('description')}\n"
        msg += "\n📭 当前没有在售商品。"
        yield event.plain_result(msg)
        return

    try:
        from ..draw.shop import draw_shop_image

        image = await draw_shop_image(shop, items, plugin.item_template_repo, plugin.data_dir)
        image_path = os.path.join(plugin.tmp_dir, f"shop_{shop_id}.png")
        image.save(image_path)
        yield event.image_result(image_path)
    except Exception as e:
        from astrbot.api import logger
        logger.error(f"生成商店图片时发生错误: {e}", exc_info=True)
        # 回退到文本输出
        msg = f"【🛒 {shop.get('name')}】(ID: {shop.get('shop_id')})\n"
        if shop.get("description"):
            msg += f"📖 {shop.get('description')}\n"
        for i, e in enumerate(items):
            item = e["item"]
            costs = e["costs"]
            msg += f"\n - {item['name']} (ID: {item['item_id']})\n"
            for c in costs:
                if c["cost_type"] == "coins":
                    msg += f"   💰 {c['cost_amount']}金币\n"
            if item.get("description"):
                msg += f"   {item['description']}\n"
        msg += "\n💡 购买：商店购买 商店ID 商品ID [数量]"
        yield event.plain_result(msg)


async def buy_in_shop(plugin: "FishingPlugin", event: AstrMessageEvent):
    """按商店池购买：/商店购买 <商店ID> <商品ID> [数量]"""
    user_id = plugin._get_effective_user_id(event)
    args = event.message_str.split(" ")
    if len(args) < 3:
        yield event.plain_result("❌ 用法：商店购买 商店ID 商品ID [数量]\n💡 支持中文数字，如：商店购买 1 2 五")
        return
    shop_id, item_id = args[1], args[2]
    if not shop_id.isdigit() or not item_id.isdigit():
        yield event.plain_result("❌ 商店ID与商品ID必须是数字")
        return
    # 默认购买1个，如果指定了数量则使用指定数量
    qty = 1
    if len(args) >= 4:
        try:
            qty = parse_amount(args[3])
            if qty <= 0:
                yield event.plain_result("❌ 数量必须是正整数")
                return
        except Exception as e:
            yield event.plain_result(f"❌ 无法解析数量：{str(e)}。示例：1 或 五 或 一千")
            return
    result = plugin.shop_service.purchase_item(user_id, int(item_id), qty)
    if result.get("success"):
        yield event.plain_result(result["message"])
    else:
        error_message = result.get("message", "购买失败")
        # 检查错误消息是否已经包含❌符号，避免重复添加
        if error_message.startswith("❌"):
            yield event.plain_result(error_message)
        else:
            yield event.plain_result(f"❌ {error_message}")


async def market(plugin: "FishingPlugin", event: AstrMessageEvent):
    """查看市场"""
    result = plugin.market_service.get_market_listings()
    if not result.get("success"):
        yield event.plain_result(
            f"❌ 查看市场失败：{result.get('message', '未知错误')}"
        )
        return

    # 将所有商品分类
    grouped_items = {
        "rod": result.get("rods", []),
        "accessory": result.get("accessories", []),
        "commodity": result.get("commodities", []),
        "item": result.get("items", []),
        "fish": result.get("fish", []),
    }

    if not any(grouped_items.values()):
        yield event.plain_result("🛒 市场中没有商品可供购买。")
        return

    # --- 帮助函数：用于格式化单个分区 ---
    def format_section(title_emoji, title_text, listings):
        if not listings:
            return ""

        msg = f"【{title_emoji} 市场 - {title_text}】\n\n"
        for item in listings[:15]:  # 每个分区最多显示15个
            display_code = _get_display_code_for_market_item(item)
            seller_display = (
                "🎭 匿名卖家" if item.is_anonymous else item.seller_nickname
            )
            refine_level_str = (
                f" 精{item.refine_level}"
                if hasattr(item, "refine_level") and item.refine_level > 1
                else ""
            )
            quantity_text = (
                f" x{item.quantity}"
                if hasattr(item, "quantity") and item.quantity > 1
                else ""
            )

            # 为鱼类添加品质显示
            quality_str = ""
            if item.item_type == "fish" and hasattr(item, "quality_level") and item.quality_level == 1:
                quality_str = "✨高品质"
            
            msg += f" - {item.item_name}{quality_str}{refine_level_str}{quantity_text} (ID: {display_code}) - 价格: {item.price} 金币\n"
            msg += f" - 售卖人： {seller_display}"

            # 为大宗商品添加腐败时间显示
            if (
                item.item_type == "commodity"
                and hasattr(item, "expires_at")
                and item.expires_at
            ):
                from datetime import datetime

                time_left = item.expires_at - datetime.now()
                if time_left.total_seconds() <= 0:
                    msg += f"\n - 状态: 💀 已腐败"
                elif time_left.total_seconds() <= 86400:  # 24小时内
                    hours = int(time_left.total_seconds() // 3600)
                    minutes = int((time_left.total_seconds() % 3600) // 60)
                    msg += f"\n - 腐败倒计时: ⚠️ {hours}小时{minutes}分钟"
                else:
                    days = time_left.days
                    hours = int(time_left.seconds // 3600)
                    msg += f"\n - 腐败倒计时: ⏰ {days}天{hours}小时"

            msg += "\n\n"
        return msg

    # --- 构建并发送消息 ---
    final_message_parts = []
    final_message_parts.append(format_section("🎣", "鱼竿", grouped_items["rod"]))
    final_message_parts.append(format_section("💍", "饰品", grouped_items["accessory"]))
    final_message_parts.append(
        format_section("📦", "大宗商品", grouped_items["commodity"])
    )
    final_message_parts.append(format_section("🎁", "道具", grouped_items["item"]))
    final_message_parts.append(format_section("🐟", "鱼类", grouped_items["fish"]))

    full_message = "".join([part for part in final_message_parts if part])

    if not full_message.strip():
        yield event.plain_result("🛒 市场中没有商品可供购买。")
        return

    full_message += "💡 挂单有效期为5天，过期将自动下架返还\n"
    full_message += "💡 使用「购买 ID」购买，例如：购买 C5"

    # 为避免消息过长，进行分割发送
    if len(full_message) > 1800:
        # 简单的按分区（双换行）分割
        parts = full_message.split("\n\n")
        current_part = ""
        for part in parts:
            # 如果当前部分加上新部分超过长度限制，就先发送当前部分
            if len(current_part) + len(part) + 2 > 1800 and current_part:
                yield event.plain_result(current_part)
                current_part = part + "\n\n"
            else:
                current_part += part + "\n\n"

        # 发送最后剩余的部分
        if current_part.strip():
            yield event.plain_result(current_part.strip())
    else:
        yield event.plain_result(full_message)


async def list_any(
    plugin: "FishingPlugin", event: AstrMessageEvent, is_anonymous: bool = False
):
    """统一上架命令：/上架 <ID> <价格> [数量] [匿名]
    - Rxxxx: 魚竿實例
    - Axxxx: 飾品實例
    - Dxxxx: 道具模板
    - Fxxxx: 魚類模板
    - Cxxxx: 大宗商品實例
    """
    user_id = plugin._get_effective_user_id(event)
    args = event.message_str.split(" ")
    if len(args) < 3:
        yield event.plain_result(
            "❌ 用法：/上架 ID 价格 [数量] [匿名]\n示例：/上架 R2N9C 1000、/上架 D1 1万 10、/上架 F3 五十 5 匿名\n💡 挂单有效期为5天，过期将自动下架返还\n💡 匿名参数必须在最后\n💡 支持中文数字，如：一千、1万、五十等"
        )
        return
    token = args[1].strip().upper()
    price_str = args[2]

    # 解析数量和匿名参数
    quantity = 1
    is_anonymous = is_anonymous  # 保持传入的匿名状态

    # 检查最后一个参数是否为匿名参数
    if len(args) > 3:
        last_arg = args[-1].strip().lower()
        if last_arg in ["匿名", "anonymous"]:
            is_anonymous = True
            # 如果最后一个参数是匿名，那么数量参数在倒数第二个位置
            if len(args) > 4:
                try:
                    quantity = parse_amount(args[-2])
                    if quantity <= 0:
                        yield event.plain_result("❌ 数量必须是正整数。")
                        return
                except Exception as e:
                    yield event.plain_result(f"❌ 无法解析数量：{str(e)}")
                    return
        else:
            # 如果最后一个参数不是匿名，那么它就是数量参数
            try:
                quantity = parse_amount(args[-1])
                if quantity <= 0:
                    yield event.plain_result("❌ 数量必须是正整数。")
                    return
            except Exception:
                # 如果解析失败，可能不是数量参数，保持默认值1
                quantity = 1

    # 解析价格，支持中文数字
    try:
        price = parse_amount(price_str)
        if price <= 0:
            yield event.plain_result("❌ 上架价格必须是正整数，请检查后重试。")
            return
    except Exception as e:
        yield event.plain_result(f"❌ 无法解析价格：{str(e)}。示例：1000 或 1万 或 一千")
        return

    # 检查是否为数字ID（旧格式）
    if token.isdigit():
        yield event.plain_result(
            "❌ 请使用正确的物品ID！\n\n📝 短码格式：\n• R开头：鱼竿（如 R2N9C）\n• A开头：饰品（如 A7K3Q）\n• D开头：道具（如 D1）\n• F开头：鱼类（如 F3）\n• C开头：大宗商品（如 C1234）\n\n💡 提示：使用 /背包 查看您的物品短码"
        )
        return

    def _from_base36(s: str) -> int:
        s = (s or "").strip().upper()
        return int(s, 36)

    # 判别类型并解析
    result = None
    if token.startswith("R"):
        instance_id = plugin.inventory_service.resolve_rod_instance_id(user_id, token)
        if instance_id is None:
            yield event.plain_result("❌ 无效的鱼竿ID，请检查后重试。")
            return
        result = plugin.market_service.put_item_on_sale(
            user_id,
            "rod",
            int(instance_id),
            price,
            is_anonymous=is_anonymous,
            quantity=quantity,
        )
    elif token.startswith("A"):
        instance_id = plugin.inventory_service.resolve_accessory_instance_id(
            user_id, token
        )
        if instance_id is None:
            yield event.plain_result("❌ 无效的饰品ID，请检查后重试。")
            return
        result = plugin.market_service.put_item_on_sale(
            user_id,
            "accessory",
            int(instance_id),
            price,
            is_anonymous=is_anonymous,
            quantity=quantity,
        )
    elif token.startswith("D"):
        try:
            item_id = int(token[1:])
        except Exception:
            yield event.plain_result("❌ 无效的道具ID，请检查后重试。")
            return
        result = plugin.market_service.put_item_on_sale(
            user_id,
            "item",
            int(item_id),
            price,
            is_anonymous=is_anonymous,
            quantity=quantity,
        )
    elif token.startswith("F"):
        try:
            # 解析鱼类ID，支持品质标识（F3H = ✨高品质，F3 = 普通品质）
            quality_level = 0  # 默认普通品质
            if token.endswith("H"):
                quality_level = 1  # ✨高品质
                fish_id = int(token[1:-1])  # 去掉F前缀和H后缀
            else:
                fish_id = int(token[1:])  # 去掉F前缀
        except Exception:
            yield event.plain_result("❌ 无效的鱼类ID，请检查后重试。\n💡 支持格式：F3（普通品质）、F3H（✨高品质）")
            return
        result = plugin.market_service.put_item_on_sale(
            user_id,
            "fish",
            int(fish_id),
            price,
            is_anonymous=is_anonymous,
            quantity=quantity,
            quality_level=quality_level,
        )
    elif token.startswith("C"):
        try:
            instance_id = _from_base36(token[1:])
        except Exception:
            yield event.plain_result("❌ 无效的大宗商品ID，请检查后重试。")
            return
        result = plugin.market_service.put_item_on_sale(
            user_id,
            "commodity",
            instance_id,
            price,
            is_anonymous=is_anonymous,
            quantity=quantity,
        )
    else:
        yield event.plain_result("❌ 无效ID，请使用以 R/A/D/F/C 开头的短码")
        return

    if result:
        if result.get("success"):
            message = result["message"]
            if is_anonymous:
                message = f"🎭 {message} (匿名上架)"
            yield event.plain_result(message)
        else:
            yield event.plain_result(f"❌ 上架失败：{result['message']}")
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def buy_item(plugin: "FishingPlugin", event: AstrMessageEvent):
    """购买市场上的物品"""
    user_id = plugin._get_effective_user_id(event)
    args = event.message_str.split(" ")
    if len(args) < 2:
        yield event.plain_result(
            "❌ 请指定要购买的商品ID，例如：/购买 MC 或 /购买 R1A2B\n💡 使用「市场」命令查看商品列表"
        )
        return

    try:
        market_id = _parse_market_code(args[1], plugin.market_service)
    except ValueError as e:
        yield event.plain_result(f"❌ {e}\n💡 使用「市场」命令查看商品列表")
        return

    result = plugin.market_service.buy_market_item(user_id, market_id)
    if result:
        if result["success"]:
            yield event.plain_result(result["message"])
        else:
            yield event.plain_result(f"❌ 购买失败：{result['message']}")
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


async def my_listings(plugin: "FishingPlugin", event: AstrMessageEvent):
    """查看我在市场上架的商品"""
    user_id = plugin._get_effective_user_id(event)
    result = plugin.market_service.get_user_listings(user_id)
    if result["success"]:
        listings = result["listings"]
        if not listings:
            yield event.plain_result("📦 您还没有在市场上架任何商品。")
            return

        total_count = len(listings)

        # 限制最多显示15件商品，超过则分多次发送
        display_count = min(total_count, 15)
        listings_to_show = listings[:display_count]

        # 分页显示，每页最多8件商品
        page_size = 8
        total_pages = (display_count + page_size - 1) // page_size

        for page in range(total_pages):
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, display_count)
            page_listings = listings_to_show[start_idx:end_idx]

            message = f"【🛒 我的上架商品】第 {page + 1}/{total_pages} 页 (共 {total_count} 件，显示前 {display_count} 件)\n\n"

            for listing in page_listings:
                message += f"🆔 ID: {listing.market_id}\n"
                message += f"📦 {listing.item_name}"
                if listing.refine_level > 1:
                    message += f" 精{listing.refine_level}"
                message += f"\n💰 价格: {listing.price} 金币\n"
                message += (
                    f"📅 上架时间: {listing.listed_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                )

            message += "💡 使用「下架 ID」命令下架指定商品"

            yield event.plain_result(message)
    else:
        yield event.plain_result(f"❌ 查询失败：{result['message']}")


async def delist_item(plugin: "FishingPlugin", event: AstrMessageEvent):
    """下架市场上的商品"""
    user_id = plugin._get_effective_user_id(event)
    args = event.message_str.split(" ")
    if len(args) < 2:
        yield event.plain_result(
            "❌ 请指定要下架的商品 ID或ID，例如：/下架 MC 或 /下架 R2N9C\n💡 使用「我的上架」命令查看您的商品列表"
        )
        return
    code = args[1]
    # 支持 Mxxxx（市场）、Rxxxx/Axxxx（通过实例查当前用户上架）或纯数字
    if code.isdigit():
        market_id = int(code)
    else:
        try:
            market_id = _parse_market_code(code, plugin.market_service)
        except ValueError as e:
            yield event.plain_result(f"❌ {e}\n💡 使用「我的上架」命令查看您的商品列表")
            return
    result = plugin.market_service.delist_item(user_id, market_id)
    if result:
        if result["success"]:
            yield event.plain_result(result["message"])
        else:
            yield event.plain_result(f"❌ 下架失败：{result['message']}")
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")


def _to_base36(n: int) -> str:
    """将数字转换为base36字符串"""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return "0"
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = []
    while n:
        n, rem = divmod(n, 36)
        out.append(digits[rem])
    return "".join(reversed(out))


def _get_display_code_for_market_item(item) -> str:
    """为市场商品生成显示ID"""
    item_type = item.item_type
    item_instance_id = item.item_instance_id

    if item_type == "rod" and item_instance_id:
        return f"R{_to_base36(item_instance_id)}"
    elif item_type == "accessory" and item_instance_id:
        return f"A{_to_base36(item_instance_id)}"
    elif item_type == "item" or item_type == "fish":
        # 道具和鱼类在市场中使用Base36编码的市场ID
        # 品质信息通过物品名称的"✨高品质"标识来展示，ID保持统一格式
        return f"M{_to_base36(item.market_id)}"
    elif item_type == "commodity" and item_instance_id:
        return f"C{_to_base36(item_instance_id)}"
    else:
        # 其他情况，使用Base36编码的市场ID
        return f"M{_to_base36(item.market_id)}"


def _from_base36(s: str) -> int:
    """将base36字符串转换为数字"""
    if not s:
        raise ValueError("Empty string")
    s = s.upper()
    result = 0
    for char in s:
        if char.isdigit():
            result = result * 36 + int(char)
        elif "A" <= char <= "Z":
            result = result * 36 + ord(char) - ord("A") + 10
        else:
            raise ValueError(f"Invalid character: {char}")
    return result


def _parse_market_code(code: str, market_service=None) -> int:
    """解析市场ID，返回市场ID"""
    code = code.strip().upper()

    if code.startswith("M") and len(code) > 1:
        # M开头的ID，后面是Base36编码的市场ID
        try:
            return _from_base36(code[1:])
        except ValueError:
            raise ValueError(f"无效的市场ID: {code}")
    elif code.startswith("R") and len(code) > 1:
        # R开头的ID，需要根据实例ID查找市场ID
        try:
            instance_id = _from_base36(code[1:])
            if market_service:
                market_id = market_service.get_market_id_by_instance_id(
                    "rod", instance_id
                )
                if market_id is not None:
                    return market_id
                else:
                    raise ValueError(f"未找到鱼竿ID {code} 对应的市场商品")
            else:
                raise ValueError("无法解析鱼竿ID，请稍后重试")
        except ValueError as e:
            raise ValueError(f"无效的鱼竿ID: {code}")
    elif code.startswith("A") and len(code) > 1:
        # A开头的ID，需要根据实例ID查找市场ID
        try:
            instance_id = _from_base36(code[1:])
            if market_service:
                market_id = market_service.get_market_id_by_instance_id(
                    "accessory", instance_id
                )
                if market_id is not None:
                    return market_id
                else:
                    raise ValueError(f"未找到饰品ID {code} 对应的市场商品")
            else:
                raise ValueError("无法解析饰品ID，请稍后重试")
        except ValueError as e:
            raise ValueError(f"无效的饰品ID: {code}")
    elif code.startswith("C") and len(code) > 1:
        # C开头的ID，需要根据实例ID查找市场ID
        try:
            instance_id = _from_base36(code[1:])
            if market_service:
                market_id = market_service.get_market_id_by_instance_id(
                    "commodity", instance_id
                )
                if market_id is not None:
                    return market_id
                else:
                    raise ValueError(f"未找到大宗商品ID {code} 对应的市场商品")
            else:
                raise ValueError("无法解析大宗商品ID，请稍后重试")
        except ValueError as e:
            raise ValueError(f"无效的大宗商品ID: {code}")
    else:
        raise ValueError(
            f"无效的市场ID: {code}，请使用短码（如 R1A2B、A3C4D、MC、C5E6F）"
        )