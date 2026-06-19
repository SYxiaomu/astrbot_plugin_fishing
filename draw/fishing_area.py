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


def calculate_dynamic_height(zones: List[Dict[str, Any]]) -> int:
    """计算动态画布高度（单列布局）"""
    base_height = 220  # 标题 + 用户信息卡片 + 底部
    zone_count = len(zones)
    if zone_count > 0:
        zone_section_height = zone_count * 120 + max(zone_count - 1, 0) * 15
    else:
        zone_section_height = 50
    return base_height + zone_section_height + 100


async def draw_fishing_area_image(zones: List[Dict[str, Any]], 
                                   user_data: Dict[str, Any],
                                   data_dir: str = "") -> Image.Image:
    """
    绘制钓鱼区域图像（单列布局，带头像）

    Args:
        zones: 钓鱼区域列表
        user_data: 用户信息，包含：
            - user_id: 用户ID（用于获取头像）
            - nickname: 昵称
            - current_zone_name: 当前区域名称
        data_dir: 数据目录（用于头像缓存）

    Returns:
        PIL.Image.Image: 生成的钓鱼区域图像
    """
    from .gradient_utils import create_vertical_gradient
    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache
    from .utils import get_user_avatar, draw_user_card_bg

    width = 800
    height = calculate_dynamic_height(zones)

    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(18)
    small_font = load_font(16)
    tiny_font = load_font(14)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    primary_light = (108, 142, 191)
    text_primary = (55, 71, 79)
    text_secondary = (120, 144, 156)
    text_muted = (176, 190, 197)
    success_color = COLOR_SUCCESS
    warning_color = COLOR_WARNING
    error_color = COLOR_ERROR
    gold_color = COLOR_GOLD
    rare_color = COLOR_RARE
    card_bg = (255, 255, 255, 240)

    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

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

    def draw_rounded_rectangle(draw, bbox, radius, fill=None, outline=None, width=1):
        x1, y1, x2, y2 = bbox
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
        draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill, outline=outline, width=width)
        draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill, outline=outline, width=width)
        draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill, outline=outline, width=width)
        draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill, outline=outline, width=width)

    current_y = 20

    # 标题
    title_text = "🗺️ 钓鱼区域"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    draw.text((title_x, current_y), title_text, font=title_font, fill=primary_dark)
    current_y += title_h + 15

    # 用户信息卡片（仿背包样式）
    card_margin = 30
    info_card_height = 120
    await draw_user_card_bg(image, draw, user_data.get('user_id', ''), data_dir,
                            (card_margin, current_y, width - card_margin, current_y + info_card_height),
                            10, fallback_fill=card_bg)

    nickname = user_data.get('nickname', '未知用户')
    current_zone_name = user_data.get('current_zone_name', '无')

    col1_x = card_margin + 20
    avatar_size = 60
    col1_x_with_avatar = col1_x + avatar_size + 20

    # 绘制用户头像
    user_id = user_data.get('user_id', '')
    row1_y = current_y + 18
    if user_id and data_dir:
        avatar_image = await get_user_avatar(user_id, data_dir, avatar_size)
        if avatar_image:
            image.paste(avatar_image, (col1_x, row1_y), avatar_image)
            col1_x = col1_x_with_avatar

    # 用户昵称
    draw.text((col1_x, row1_y), nickname, font=subtitle_font, fill=primary_medium)

    # 当前区域（昵称下方）
    row2_y = current_y + 72
    draw.text((col1_x, row2_y), f"📍当前区域: {current_zone_name}", font=small_font, fill=text_secondary)

    current_y += info_card_height + 20

    if not zones:
        draw.text((30, current_y), "❌ 当前没有可用的钓鱼区域。", font=content_font, fill=text_muted)
        return image

    # 区域列表 - 单列布局
    card_width = width - 60
    card_margin = 15

    # 区域列表标题
    draw.text((30, current_y), "🏞️区域列表", font=subtitle_font, fill=primary_medium)
    current_y += 35

    for i, zone in enumerate(zones):
        y = current_y
        card_h = 120
        current_y += card_h + card_margin

        ensure_height(y + card_h + 40)

        is_current = zone.get("whether_in_use", False)
        is_active = zone.get("is_active", True)

        if is_current:
            zone_bg = (240, 248, 255)
        elif not is_active:
            zone_bg = (245, 245, 245)
        else:
            zone_bg = card_bg

        draw_rounded_rectangle(draw, (30, y, 30 + card_width, y + card_h), 8, fill=zone_bg)

        # 第1行：ID + 区域名称 + 状态图标
        zone_id = zone.get('zone_id', '?')
        zone_name = zone.get('name', f"区域#{zone_id}")
        status_icon = "📍" if is_current else ("✅" if is_active else "❌")

        id_text = f"#{zone_id}"
        draw.text((45, y + 12), id_text, font=tiny_font, fill=primary_light)

        name_x = 45 + get_text_size(id_text, tiny_font)[0] + 10
        draw.text((name_x, y + 10), zone_name, font=content_font, fill=text_primary)

        status_w, status_h = get_text_size(status_icon, tiny_font)
        draw.text((30 + card_width - 20 - status_w, y + 12), status_icon, font=tiny_font,
                 fill=success_color if is_active else error_color)

        # 第2行：钓鱼费用
        cost = zone.get('fishing_cost', 0)
        detail_y = y + 42
        cost_text = f"💰 钓鱼费用：{cost}金币"
        draw.text((45, detail_y), cost_text, font=small_font, fill=gold_color)

        # 第3行：稀有鱼剩余
        detail_y += 28
        daily_quota = zone.get("daily_rare_fish_quota", 0)
        if daily_quota > 0:
            remaining = daily_quota - zone.get("rare_fish_caught_today", 0)
            quota_color = success_color if remaining > 0 else error_color
            fish_text = f"🐟 稀有鱼剩余：{remaining}/{daily_quota}"
        else:
            fish_text = "🐟 稀有鱼剩余：无限制"
            quota_color = text_secondary
        draw.text((45, detail_y), fish_text, font=small_font, fill=quota_color)

        # 第4行：通行证要求和开放时间
        detail_y += 28
        extra_parts = []
        if zone.get("requires_pass") and zone.get("required_item_name"):
            extra_parts.append(f"🔑 需要: {zone['required_item_name']}")
        available_from = zone.get("available_from")
        if available_from:
            from_time = available_from.strftime('%m-%d %H:%M') if hasattr(available_from, 'strftime') else str(available_from)
            to_time = ""
            available_until = zone.get("available_until")
            if available_until:
                to_time = available_until.strftime('%m-%d %H:%M') if hasattr(available_until, 'strftime') else str(available_until)
            time_str = f"⏰ {from_time}"
            if to_time:
                time_str += f" ~ {to_time}"
            extra_parts.append(time_str)

        if extra_parts:
            extra_text = " | ".join(extra_parts)
            extra_w, extra_h = get_text_size(extra_text, tiny_font)
            if extra_w <= card_width - 60:
                draw.text((45, detail_y), extra_text, font=tiny_font, fill=primary_light)
            else:
                draw.text((45, detail_y), extra_parts[0], font=tiny_font, fill=primary_light)

    current_y += 10

    # 底部提示
    ensure_height(height - 10)
    hint_text = "💡 使用 /钓鱼区域 <编号> 切换到指定区域"
    hint_w, hint_h = get_text_size(hint_text, small_font)
    hint_x = (width - hint_w) // 2
    draw.text((hint_x, current_y), hint_text, font=small_font, fill=text_secondary)
    current_y += hint_h + 10

    # 底部信息
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer_w, footer_h = get_text_size(footer_text, small_font)
    footer_x = (width - footer_w) // 2

    needed = current_y + footer_h + 30
    if needed > height:
        new_image = Image.new('RGB', (width, needed), (255, 255, 255))
        bg = create_vertical_gradient(width, needed, bg_top, bg_bot)
        new_image.paste(bg, (0, 0))
        new_image.paste(image, (0, 0))
        image = new_image
        draw = ImageDraw.Draw(image)
        height = needed

    draw.text((footer_x, current_y), footer_text, font=small_font, fill=text_secondary)

    corner_size = 15
    corner_color = COLOR_CORNER
    draw.ellipse([8, 8, 8 + corner_size, 8 + corner_size], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, 8, width - 8, 8 + corner_size], fill=corner_color)
    draw.ellipse([8, height - 8 - corner_size, 8 + corner_size, height - 8], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, height - 8 - corner_size, width - 8, height - 8], fill=corner_color)

    return image