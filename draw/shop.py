import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
from .styles import (
    IMG_WIDTH, PADDING, CORNER_RADIUS,
    COLOR_BACKGROUND, COLOR_HEADER_BG, COLOR_TEXT_WHITE, COLOR_TEXT_DARK,
    COLOR_TEXT_GRAY, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_LOCK,
    COLOR_GOLD, COLOR_RARE, COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    COLOR_CORNER, load_font
)
from .star_renderer import draw_text_with_stars

def format_rarity_display(rarity: int) -> str:
    """格式化稀有度显示"""
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★★★★★★★★★★+'


def calculate_dynamic_height(shop: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
    """计算商店详情动态画布高度"""
    base_height = 200  # 标题 + 商店信息卡片 + 底部提示 + 底部
    item_count = len(items)
    if item_count > 0:
        rows = (item_count + 1) // 2
        item_section_height = 35 + rows * 180 + (rows - 1) * 15
    else:
        item_section_height = 35 + 50
    return base_height + item_section_height + 80  # 多预留底部提示空间


def calculate_shop_list_height(shops: List[Dict[str, Any]]) -> int:
    """计算商店列表动态画布高度"""
    base_height = 200  # 标题 + 底部
    shop_count = len(shops)
    if shop_count > 0:
        rows = (shop_count + 1) // 2
        shop_section_height = 35 + rows * 100 + (rows - 1) * 15
    else:
        shop_section_height = 35 + 50
    return base_height + shop_section_height + 80


def get_item_emoji(reward_type: str, item_name: str = "") -> str:
    """根据奖励类型和名称获取emoji"""
    emoji_map = {
        "rod": "🎣",
        "accessory": "💍",
        "bait": "🪱",
        "fish": "🐟",
        "coins": "💰",
        "item": "📦",
    }
    if reward_type in emoji_map:
        return emoji_map[reward_type]
    return "📦"


def _create_base_image(width: int, height: int):
    """创建基础渐变背景图像"""
    from .gradient_utils import create_vertical_gradient

    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    return image, bg_top, bg_bot


def _setup_fonts():
    """设置字体"""
    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(18)
    small_font = load_font(16)
    tiny_font = load_font(14)
    return title_font, subtitle_font, content_font, small_font, tiny_font


def _setup_colors():
    """设置颜色"""
    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    primary_light = (108, 142, 191)
    text_primary = (55, 71, 79)
    text_secondary = (120, 144, 156)
    text_muted = (176, 190, 197)
    gold_color = COLOR_GOLD
    rare_color = COLOR_RARE
    warning_color = COLOR_WARNING
    error_color = COLOR_ERROR
    success_color = COLOR_SUCCESS
    card_bg = (255, 255, 255, 240)
    return {
        'primary_dark': primary_dark, 'primary_medium': primary_medium,
        'primary_light': primary_light, 'text_primary': text_primary,
        'text_secondary': text_secondary, 'text_muted': text_muted,
        'gold_color': gold_color, 'rare_color': rare_color,
        'warning_color': warning_color, 'error_color': error_color,
        'success_color': success_color, 'card_bg': card_bg,
    }


def draw_rounded_rectangle(draw, bbox, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill, outline=outline, width=width)


def _draw_corner_decorations(draw, width, height):
    """绘制四角装饰"""
    corner_size = 15
    corner_color = COLOR_CORNER
    draw.ellipse([8, 8, 8 + corner_size, 8 + corner_size], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, 8, width - 8, 8 + corner_size], fill=corner_color)
    draw.ellipse([8, height - 8 - corner_size, 8 + corner_size, height - 8], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, height - 8 - corner_size, width - 8, height - 8], fill=corner_color)


def _draw_footer(draw, current_y, width, small_font, text_secondary):
    """绘制底部信息和购买提示"""
    # 购买提示
    hint1 = "💡 购买：/商店购买 商店ID 商品ID [数量]"
    hint2 = "示例：/商店购买 1 2 5"
    
    hint1_w, hint1_h = draw.textbbox((0, 0), hint1, font=small_font)[2:4]
    hint1_x = (width - hint1_w) // 2
    draw.text((hint1_x, current_y), hint1, font=small_font, fill=text_secondary)
    current_y += hint1_h + 4
    
    hint2_w, hint2_h = draw.textbbox((0, 0), hint2, font=small_font)[2:4]
    hint2_x = (width - hint2_w) // 2
    draw.text((hint2_x, current_y), hint2, font=small_font, fill=text_secondary)
    current_y += hint2_h + 10

    # 生成时间
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer_w, footer_h = draw.textbbox((0, 0), footer_text, font=small_font)[2:4]
    footer_x = (width - footer_w) // 2
    draw.text((footer_x, current_y), footer_text, font=small_font, fill=text_secondary)
    current_y += footer_h + 15

    return current_y


async def draw_shop_list_image(shops: List[Dict[str, Any]]) -> Image.Image:
    """
    绘制商店列表图像

    Args:
        shops: 商店列表，每个包含：
            - shop_id: 商店ID
            - name: 商店名称
            - shop_type: 商店类型 (normal/premium/limited)
            - is_active: 是否启用
            - description: 描述

    Returns:
        PIL.Image.Image: 生成的商店列表图像
    """
    from .text_utils import get_text_size_cached, create_text_cache

    width = 800
    height = calculate_shop_list_height(shops)

    image, bg_top, bg_bot = _create_base_image(width, height)
    draw = ImageDraw.Draw(image)
    title_font, subtitle_font, content_font, small_font, tiny_font = _setup_fonts()
    colors = _setup_colors()

    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    def ensure_height(needed_height):
        nonlocal image, draw, height
        if needed_height <= height:
            return
        new_h = needed_height
        new_image = Image.new('RGB', (width, new_h), (255, 255, 255))
        from .gradient_utils import create_vertical_gradient
        bg = create_vertical_gradient(width, new_h, bg_top, bg_bot)
        new_image.paste(bg, (0, 0))
        new_image.paste(image, (0, 0))
        image = new_image
        draw = ImageDraw.Draw(image)
        height = new_h

    current_y = 20

    # 标题
    title_text = "🛒 商店列表"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    draw.text((title_x, current_y), title_text, font=title_font, fill=colors['primary_dark'])
    current_y += title_h + 20

    if not shops:
        draw.text((30, current_y), "🛒 当前没有开放的商店。", font=content_font, fill=colors['text_muted'])
        return image

    # 商店列表标题
    draw.text((30, current_y), "🏪 所有商店", font=subtitle_font, fill=colors['primary_medium'])
    current_y += 35

    card_width = (width - 90) // 2
    card_margin = 15
    row_start_y = current_y
    next_row_start_y = current_y

    for i, s in enumerate(shops):
        row = i // 2
        col = i % 2
        x = 30 + col * (card_width + card_margin)

        # 简单高度计算
        card_h = 100

        if col == 0:
            row_start_y = next_row_start_y
            y = row_start_y
            next_row_start_y = row_start_y + card_h + card_margin
        else:
            y = row_start_y

        ensure_height(y + card_h + 40)
        draw_rounded_rectangle(draw, (x, y, x + card_width, y + card_h), 8, fill=colors['card_bg'])

        # 商店名称和状态
        stype = s.get("shop_type", "normal")
        type_name = "普通" if stype == "normal" else ("高级" if stype == "premium" else "限时")
        status = "🟢" if s.get("is_active") else "🔴"
        
        shop_name = s.get('name', f"商店#{s.get('shop_id')}")
        name_w, name_h = get_text_size(shop_name, content_font)
        draw.text((x + 15, y + 12), shop_name, font=content_font, fill=colors['text_primary'])

        # 状态标签在右侧
        status_text = f"{status} {type_name}"
        status_w, status_h = get_text_size(status_text, tiny_font)
        draw.text((x + card_width - 15 - status_w, y + 15), status_text, font=tiny_font, 
                 fill=colors['success_color'] if s.get("is_active") else colors['error_color'])

        # ID
        draw.text((x + 15, y + 36), f"ID: {s.get('shop_id')}", font=tiny_font, fill=colors['primary_light'])

        # 描述
        detail_y = y + 55
        if s.get("description"):
            desc = s['description'][:25] + "..." if len(s['description']) > 25 else s['description']
            draw.text((x + 15, detail_y), f"📖 {desc}", font=tiny_font, fill=colors['text_secondary'])
        else:
            draw.text((x + 15, detail_y), "📖 暂无描述", font=tiny_font, fill=colors['text_muted'])

        # 底部提示查看详情
        draw.text((x + 15, y + card_h - 18), f"使用 /商店 {s.get('shop_id')} 查看详情", font=tiny_font, fill=colors['primary_light'])

    current_y = next_row_start_y
    current_y += 15

    _draw_footer(draw, current_y, width, small_font, colors['text_secondary'])

    needed = current_y + 30
    if needed > height:
        new_image = Image.new('RGB', (width, needed), (255, 255, 255))
        from .gradient_utils import create_vertical_gradient
        bg = create_vertical_gradient(width, needed, bg_top, bg_bot)
        new_image.paste(bg, (0, 0))
        new_image.paste(image, (0, 0))
        image = new_image
        draw = ImageDraw.Draw(image)
        height = needed

    _draw_corner_decorations(draw, width, height)
    return image


async def draw_shop_image(shop: Dict[str, Any], items: List[Dict[str, Any]], 
                          item_template_repo, data_dir: str) -> Image.Image:
    """
    绘制商店详情图像

    Args:
        shop: 商店信息
        items: 商品列表（包含 item, costs, rewards）
        item_template_repo: 物品模板仓库
        data_dir: 数据目录

    Returns:
        PIL.Image.Image: 生成的商店图像
    """
    from .gradient_utils import create_vertical_gradient
    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache

    width = 800
    height = calculate_dynamic_height(shop, items)

    image, bg_top, bg_bot = _create_base_image(width, height)
    draw = ImageDraw.Draw(image)
    title_font, subtitle_font, content_font, small_font, tiny_font = _setup_fonts()
    colors = _setup_colors()

    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    def wrap_text_by_width(text, font, max_width):
        return wrap_text_by_width_optimized(text, font, max_width, text_cache)

    def ensure_height(needed_height):
        nonlocal image, draw, height
        if needed_height <= height:
            return
        new_h = needed_height
        new_image = Image.new('RGB', (width, new_h), (255, 255, 255))
        bg = create_vertical_gradient(width, new_h, bg_top, bg_bot)
        new_image.paste(bg, (0, 0))
        new_image.paste(image, (0, 0))
        image = new_image
        draw = ImageDraw.Draw(image)
        height = new_h

    # 计算商品卡片动态高度
    def measure_item_card_height(item_data: Dict[str, Any], card_width: int) -> int:
        item = item_data['item']
        rewards = item_data.get('rewards', [])
        costs = item_data.get('costs', [])

        line_h = get_text_size("测", tiny_font)[1] + 2
        lines = 0

        # 描述行
        if item.get('description'):
            desc_lines = len(wrap_text_by_width(item['description'], tiny_font, card_width - 30))
            lines += desc_lines
        # 奖励物品行
        if len(rewards) >= 2:
            lines += len(rewards) + 1  # "包含物品:" + 每个奖励
        elif len(rewards) == 1:
            reward = rewards[0]
            if reward.get('reward_quantity', 1) > 1:
                lines += 1

        header_height = 85  # 名称+星级+价格+库存+ID+限购+时间
        bottom_pad = 15
        card_h = header_height + lines * line_h + bottom_pad
        return max(card_h, 160)

    current_y = 20

    # 标题
    title_text = f"🛒 {shop.get('name', '商店')}"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    draw.text((title_x, current_y), title_text, font=title_font, fill=colors['primary_dark'])
    current_y += title_h + 15

    # 商店信息卡片
    card_margin = 30
    info_card_height = 60
    draw_rounded_rectangle(draw,
                         (card_margin, current_y, width - card_margin, current_y + info_card_height),
                         10, fill=colors['card_bg'])

    col1_x = card_margin + 20
    row1_y = current_y + 15

    # 商店类型
    stype = shop.get("shop_type", "normal")
    type_name = "普通" if stype == "normal" else ("高级" if stype == "premium" else "限时")
    status = "🟢 营业中" if shop.get("is_active") else "🔴 已关闭"
    shop_info = f"类型: {type_name} | ID: {shop.get('shop_id')} | {status}"

    draw.text((col1_x, row1_y), shop_info, font=content_font, fill=colors['text_secondary'])

    current_y += info_card_height + 20

    # 商店描述
    if shop.get("description"):
        desc_text = f"📖 {shop['description']}"
        draw.text((30, current_y), desc_text, font=small_font, fill=colors['text_secondary'])
        current_y += 25

    # 商品列表标题
    if items:
        draw.text((30, current_y), "🛍️在售商品", font=subtitle_font, fill=colors['primary_medium'])
        current_y += 35

        card_width = (width - 90) // 2
        card_margin = 15
        row_start_y = current_y
        next_row_start_y = current_y

        for i, item_data in enumerate(items):
            item = item_data['item']
            costs = item_data['costs']
            rewards = item_data.get('rewards', [])

            row = i // 2
            col = i % 2
            x = 30 + col * (card_width + card_margin)

            if col == 0:
                row_start_y = next_row_start_y
                left_h = measure_item_card_height(item_data, card_width)
                right_index = i + 1
                if right_index < len(items):
                    right_h = measure_item_card_height(items[right_index], card_width)
                else:
                    right_h = 0
                row_h = max(left_h, right_h)
                y = row_start_y
                next_row_start_y = row_start_y + row_h + card_margin
                card_h = row_h
            else:
                y = row_start_y
                card_h = row_h
            ensure_height(y + card_h + 40)

            draw_rounded_rectangle(draw, (x, y, x + card_width, y + card_h), 8, fill=colors['card_bg'])

            # 商品名称
            item_name = item['name'][:15] + "..." if len(item['name']) > 15 else item['name']
            draw.text((x + 15, y + 12), item_name, font=content_font, fill=colors['text_primary'])

            # 稀有度
            rarity = 1
            if rewards:
                if len(rewards) > 2:
                    total_rarity = 0
                    for reward in rewards:
                        if reward["reward_type"] == "rod":
                            rod_template = item_template_repo.get_rod_by_id(reward.get("reward_item_id"))
                            if rod_template:
                                total_rarity += rod_template.rarity
                        elif reward["reward_type"] == "bait":
                            bait_template = item_template_repo.get_bait_by_id(reward.get("reward_item_id"))
                            if bait_template:
                                total_rarity += bait_template.rarity
                        elif reward["reward_type"] == "accessory":
                            accessory_template = item_template_repo.get_accessory_by_id(reward.get("reward_item_id"))
                            if accessory_template:
                                total_rarity += accessory_template.rarity
                        elif reward["reward_type"] == "item":
                            item_tpl = item_template_repo.get_item_by_id(reward.get("reward_item_id"))
                            if item_tpl:
                                total_rarity += item_tpl.rarity
                    rarity = max(1, total_rarity // len(rewards))
                else:
                    reward = rewards[0]
                    if reward["reward_type"] == "rod":
                        rod_template = item_template_repo.get_rod_by_id(reward.get("reward_item_id"))
                        if rod_template:
                            rarity = rod_template.rarity
                    elif reward["reward_type"] == "bait":
                        bait_template = item_template_repo.get_bait_by_id(reward.get("reward_item_id"))
                        if bait_template:
                            rarity = bait_template.rarity
                    elif reward["reward_type"] == "accessory":
                        accessory_template = item_template_repo.get_accessory_by_id(reward.get("reward_item_id"))
                        if accessory_template:
                            rarity = accessory_template.rarity
                    elif reward["reward_type"] == "item":
                        item_tpl = item_template_repo.get_item_by_id(reward.get("reward_item_id"))
                        if item_tpl:
                            rarity = item_tpl.rarity

            star_color = colors['rare_color'] if rarity > 4 else colors['warning_color'] if rarity >= 3 else colors['text_secondary']
            rarity_label = format_rarity_display(rarity)
            draw_text_with_stars(image, draw, (x + 15, y + 35), rarity_label,
                                 font=small_font, fill=star_color, star_size=14)

            # 价格
            cost_parts = []
            for c in costs:
                if c["cost_type"] == "coins":
                    cost_parts.append(f"💰{c['cost_amount']}金币")
                elif c["cost_type"] == "premium":
                    cost_parts.append(f"💎{c['cost_amount']}高级")
                elif c["cost_type"] == "item":
                    item_tpl = item_template_repo.get_item_by_id(c.get("cost_item_id"))
                    item_name_cost = item_tpl.name if item_tpl else f"道具#{c.get('cost_item_id')}"
                    cost_parts.append(f"🎁{item_name_cost}x{c['cost_amount']}")
                elif c["cost_type"] == "fish":
                    fish_tpl = item_template_repo.get_fish_by_id(c.get("cost_item_id"))
                    fish_name = fish_tpl.name if fish_tpl else f"鱼类#{c.get('cost_item_id')}"
                    quality_level = c.get("quality_level", 0)
                    if quality_level == 1:
                        fish_name += "高品质"
                    cost_parts.append(f"🐟{fish_name}x{c['cost_amount']}")
                elif c["cost_type"] == "rod":
                    rod_tpl = item_template_repo.get_rod_by_id(c.get("cost_item_id"))
                    rod_name = rod_tpl.name if rod_tpl else f"鱼竿#{c.get('cost_item_id')}"
                    cost_parts.append(f"🎣{rod_name}x{c['cost_amount']}")
                elif c["cost_type"] == "accessory":
                    acc_tpl = item_template_repo.get_accessory_by_id(c.get("cost_item_id"))
                    acc_name = acc_tpl.name if acc_tpl else f"饰品#{c.get('cost_item_id')}"
                    cost_parts.append(f"💍{acc_name}x{c['cost_amount']}")

            cost_str = " + ".join(cost_parts) if cost_parts else "免费"
            # 检查是否有高品质鱼，单独渲染✨避免emoji逐字符渲染导致偏移
            has_hq_fish = any(c.get("cost_type") == "fish" and c.get("quality_level", 0) == 1 for c in costs)
            if has_hq_fish and "高品质" in cost_str:
                idx = cost_str.index("高品质")
                before = cost_str[:idx]
                after = cost_str[idx:]
                cx_start = x + 15
                draw.text((cx_start, y + 55), before, font=tiny_font, fill=colors['gold_color'])
                from .styles import _get_emoji_font
                emoji_font = _get_emoji_font(tiny_font.size)
                bw = get_text_size(before, tiny_font)[0]
                draw.text((cx_start + bw, y + 55), "✨", font=emoji_font if emoji_font else tiny_font, fill=colors['gold_color'])
                ew = get_text_size("✨", emoji_font if emoji_font else tiny_font)[0]
                draw.text((cx_start + bw + ew, y + 55), after, font=tiny_font, fill=colors['gold_color'])
            else:
                draw.text((x + 15, y + 55), cost_str, font=tiny_font, fill=colors['gold_color'])

            # 库存和ID
            stock_str = "无限" if item.get("stock_total") is None else f"{item.get('stock_sold',0)}/{item.get('stock_total')}"
            detail_y = y + 72
            draw.text((x + 15, detail_y), f"库存: {stock_str} | ID: {item['item_id']}", font=tiny_font, fill=colors['text_secondary'])
            detail_y += 16

            # 限购信息
            limit_info = []
            if item.get("per_user_limit") is not None:
                limit_info.append(f"每人限购{item['per_user_limit']}")
            if item.get("per_user_daily_limit") is not None:
                limit_info.append(f"每日限购{item['per_user_daily_limit']}")

            if limit_info:
                draw.text((x + 15, detail_y), "限购: " + " | ".join(limit_info), font=tiny_font, fill=colors['primary_light'])
                detail_y += 16

            # 限时信息
            current_time = datetime.now()
            time_info = []
            start_time = item.get("start_time")
            end_time = item.get("end_time")

            if start_time:
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    except:
                        pass
                if isinstance(start_time, datetime):
                    if current_time < start_time:
                        time_info.append(f"未开始:{start_time.strftime('%m-%d %H:%M')}")
                    else:
                        time_info.append(f"开始:{start_time.strftime('%m-%d %H:%M')}")

            if end_time:
                if isinstance(end_time, str):
                    try:
                        end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    except:
                        pass
                if isinstance(end_time, datetime):
                    if current_time > end_time:
                        time_info.append(f"已结束:{end_time.strftime('%m-%d %H:%M')}")
                    else:
                        time_info.append(f"结束:{end_time.strftime('%m-%d %H:%M')}")

            if time_info:
                draw.text((x + 15, detail_y), "限时: " + " | ".join(time_info), font=tiny_font, fill=colors['warning_color'])
                detail_y += 16

            # 奖励物品
            if len(rewards) >= 2:
                draw.text((x + 15, detail_y), "包含物品:", font=tiny_font, fill=colors['text_secondary'])
                detail_y += 16
                for reward in rewards:
                    r_name = "未知物品"
                    r_emoji = "📦"
                    if reward["reward_type"] == "rod":
                        rod_tpl = item_template_repo.get_rod_by_id(reward.get("reward_item_id"))
                        if rod_tpl:
                            r_name = rod_tpl.name
                            r_emoji = "🎣"
                    elif reward["reward_type"] == "bait":
                        bait_tpl = item_template_repo.get_bait_by_id(reward.get("reward_item_id"))
                        if bait_tpl:
                            r_name = bait_tpl.name
                            r_emoji = "🪱"
                    elif reward["reward_type"] == "accessory":
                        acc_tpl = item_template_repo.get_accessory_by_id(reward.get("reward_item_id"))
                        if acc_tpl:
                            r_name = acc_tpl.name
                            r_emoji = "💍"
                    elif reward["reward_type"] == "item":
                        item_tpl = item_template_repo.get_item_by_id(reward.get("reward_item_id"))
                        if item_tpl:
                            r_name = item_tpl.name
                            r_emoji = "🎁"
                    elif reward["reward_type"] == "fish":
                        fish_tpl = item_template_repo.get_fish_by_id(reward.get("reward_item_id"))
                        if fish_tpl:
                            r_name = fish_tpl.name
                            r_emoji = "🐟"
                    elif reward["reward_type"] == "coins":
                        r_name = "金币"
                        r_emoji = "💰"

                    reward_text = f"  {r_emoji} {r_name}"
                    if reward.get("reward_quantity", 1) > 1:
                        reward_text += f" x{reward['reward_quantity']}"
                    # 高品质鱼单独渲染✨，避免emoji逐字符渲染导致偏移
                    if reward.get("reward_type") == "fish" and reward.get("quality_level", 0) == 1:
                        rx_start = x + 20
                        draw.text((rx_start, detail_y), reward_text, font=tiny_font, fill=colors['text_secondary'])
                        from .styles import _get_emoji_font
                        emoji_font = _get_emoji_font(tiny_font.size)
                        rw = get_text_size(reward_text, tiny_font)[0]
                        draw.text((rx_start + rw, detail_y), "✨", font=emoji_font if emoji_font else tiny_font, fill=colors['text_secondary'])
                        ew = get_text_size("✨", emoji_font if emoji_font else tiny_font)[0]
                        draw.text((rx_start + rw + ew, detail_y), "高品质", font=tiny_font, fill=colors['text_secondary'])
                    else:
                        draw.text((x + 20, detail_y), reward_text, font=tiny_font, fill=colors['text_secondary'])
                    detail_y += 16

            # 描述
            if item.get('description'):
                desc_lines = wrap_text_by_width(item['description'], tiny_font, card_width - 30)
                line_h = get_text_size("测", tiny_font)[1] + 2
                max_lines = max((y + card_h - 15) - detail_y, 0) // line_h
                if max_lines > 0:
                    for li, line in enumerate(desc_lines[:max_lines]):
                        draw.text((x + 15, detail_y + li * line_h), line, font=tiny_font, fill=colors['text_secondary'])

        current_y = next_row_start_y
    else:
        draw.text((30, current_y), "📭 当前没有在售商品。", font=content_font, fill=colors['text_muted'])
        current_y += 50

    current_y += 15

    # 底部提示（购买提示 + 生成时间）
    current_y = _draw_footer(draw, current_y, width, small_font, colors['text_secondary'])

    needed = current_y + 15
    if needed > height:
        new_image = Image.new('RGB', (width, needed), (255, 255, 255))
        bg = create_vertical_gradient(width, needed, bg_top, bg_bot)
        new_image.paste(bg, (0, 0))
        new_image.paste(image, (0, 0))
        image = new_image
        draw = ImageDraw.Draw(image)
        height = needed

    _draw_corner_decorations(draw, width, height)

    return image