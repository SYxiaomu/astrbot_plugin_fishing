import os
from datetime import datetime
from typing import Dict, Any
from PIL import Image, ImageDraw
from .styles import (
    IMG_WIDTH, PADDING, CORNER_RADIUS,
    COLOR_TEXT_DARK, COLOR_CARD_BG,
    COLOR_GOLD, COLOR_RARE, COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    COLOR_CORNER, COLOR_SUCCESS, COLOR_ERROR, load_font
)

def format_rarity_display(rarity: int) -> str:
    """格式化稀有度显示"""
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★★★★★★★★★★+'

async def draw_electric_fish_result_image(electric_data: Dict[str, Any]) -> Image.Image:
    """
    绘制电鱼结果图片

    Args:
        electric_data: 电鱼结果数据，包括：
            - success: 是否成功
            - thief_name: 使用者昵称
            - victim_name: 目标用户昵称
            - message: 结果消息
            - success_type: 成功类型（大成功/普通成功/小成功）
            - stolen_count: 偷到的鱼数量
            - total_value: 总价值
            - stolen_fish: 偷到的鱼列表（可选）
            - penalty_coins: 惩罚金币（失败时）
            - success_rate: 成功率
    """
    import asyncio

    try:
        return await asyncio.wait_for(
            _draw_electric_fish_result_impl(electric_data),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return _create_electric_fallback_image(electric_data)


async def _draw_electric_fish_result_impl(electric_data: Dict[str, Any]) -> Image.Image:
    """电鱼结果图片生成的实际实现"""
    width = 600
    height = 500

    from .gradient_utils import create_vertical_gradient

    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(20)
    small_font = load_font(18)
    tiny_font = load_font(16)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    text_primary = (55, 71, 79)
    text_secondary = (120, 144, 156)
    success_color = (46, 125, 50)
    error_color = (220, 53, 69)
    gold_color = (218, 165, 32)
    lightning_color = (255, 165, 0)
    card_bg = (255, 255, 255, 240)

    from .text_utils import get_text_size_cached, create_text_cache
    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    def draw_rounded_rectangle(draw, bbox, radius, fill=None, outline=None, width=1):
        x1, y1, x2, y2 = bbox
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
        draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill, outline=outline, width=width)
        draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill, outline=outline, width=width)
        draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill, outline=outline, width=width)
        draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill, outline=outline, width=width)

    current_y = 20

    title_text = "⚡ 电鱼结果"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    draw.text((title_x, current_y), title_text, font=title_font, fill=primary_dark)
    current_y += title_h + 20

    user_card_margin = 30
    card_height = 80
    draw_rounded_rectangle(draw,
                         (user_card_margin, current_y, width - user_card_margin, current_y + card_height),
                         10, fill=card_bg)

    col1_x = user_card_margin + 20
    row1_y = current_y + 12
    row2_y = current_y + 45

    thief_name = electric_data.get('thief_name', '未知用户')
    victim_name = electric_data.get('victim_name', '未知用户')

    action_text = f"{thief_name} → {victim_name}"
    draw.text((col1_x, row1_y), action_text, font=subtitle_font, fill=primary_medium)

    success = electric_data.get('success', False)
    if success:
        success_type = electric_data.get('success_type', '')
        status_text = f"✅ {success_type}"
        status_color = success_color
    else:
        penalty_coins = electric_data.get('penalty_coins', 0)
        status_text = f"❌ 电鱼失败（损失 {penalty_coins} 金币）"
        status_color = error_color

    draw.text((col1_x, row2_y), status_text, font=small_font, fill=status_color)

    current_y += card_height + 25

    # 显示详细信息卡片
    details = []
    if success:
        stolen_count = electric_data.get('stolen_count', 0)
        total_value = electric_data.get('total_value', 0)
        success_rate = electric_data.get('success_rate', 0)

        details.append(f"🐟 捕获: {stolen_count} 条鱼")
        details.append(f"💰 价值: {total_value} 金币")
        details.append(f"🎯 成功率: {success_rate*100:.1f}%")
    else:
        success_rate = electric_data.get('success_rate', 0)
        details.append(f"🎯 成功率: {success_rate*100:.1f}%")

    detail_text = " | ".join(details)
    detail_w, detail_h = get_text_size(detail_text, small_font)
    detail_x = (width - detail_w) // 2
    draw.text((detail_x, current_y), detail_text, font=small_font, fill=text_secondary)
    current_y += detail_h + 20

    # 显示偷到的鱼列表
    stolen_fish = electric_data.get('stolen_fish', [])
    if stolen_fish:
        fish_count = len(stolen_fish)
        fish_title = f"📦 捕获清单（共 {fish_count} 种）"
        fish_title_w, _ = get_text_size(fish_title, small_font)
        fish_title_x = (width - fish_title_w) // 2
        draw.text((fish_title_x, current_y), fish_title, font=small_font, fill=gold_color)
        current_y += 25

        for i, fish in enumerate(stolen_fish[:6]):
            fish_name = fish.get('name', '未知鱼')
            quantity = fish.get('quantity', 1)
            value = fish.get('value', 0)
            rarity = fish.get('rarity', 1)

            rarity_text = format_rarity_display(rarity)
            fish_info = f"{rarity_text} {fish_name} x{quantity} ({value}金币)"

            if rarity >= 7:
                rarity_color = COLOR_REFINE_RED
            elif rarity >= 5:
                rarity_color = COLOR_REFINE_ORANGE
            elif rarity >= 3:
                rarity_color = COLOR_RARE
            else:
                rarity_color = text_secondary

            info_w, _ = get_text_size(fish_info, tiny_font)
            info_x = (width - info_w) // 2
            draw.text((info_x, current_y), fish_info, font=tiny_font, fill=rarity_color)
            current_y += 20

            if i >= 5:
                remaining = fish_count - 6
                if remaining > 0:
                    more_text = f"... 还有 {remaining} 种鱼"
                    more_w, _ = get_text_size(more_text, tiny_font)
                    more_x = (width - more_w) // 2
                    draw.text((more_x, current_y), more_text, font=tiny_font, fill=text_secondary)
                    current_y += 20
                break

    # 显示消息文本（如果有的话）
    message = electric_data.get('message', '')
    if message and not stolen_fish:
        card_width = width - 60
        lines = []
        for line in message.split('\n'):
            if len(line) > 45:
                lines.append(line[:45])
                lines.append(line[45:])
            else:
                lines.append(line)

        max_lines = min(len(lines), 5)
        message_height = max_lines * 25 + 30

        draw_rounded_rectangle(draw,
                             (30, current_y, width - 30, current_y + message_height),
                             10, fill=card_bg)

        text_y = current_y + 15
        for i, line in enumerate(lines[:max_lines]):
            draw.text((50, text_y + i * 25), line, font=content_font, fill=text_primary)

        current_y += message_height + 20

    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer_w, footer_h = get_text_size(footer_text, tiny_font)
    footer_x = (width - footer_w) // 2
    draw.text((footer_x, current_y), footer_text, font=tiny_font, fill=text_secondary)

    corner_size = 15
    corner_color = COLOR_CORNER
    draw.ellipse([8, 8, 8 + corner_size, 8 + corner_size], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, 8, width - 8, 8 + corner_size], fill=corner_color)
    draw.ellipse([8, height - 8 - corner_size, 8 + corner_size, height - 8], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, height - 8 - corner_size, width - 8, height - 8], fill=corner_color)

    return image


def _create_electric_fallback_image(electric_data: Dict[str, Any]) -> Image.Image:
    """创建简化的回退图像"""
    width, height = 600, 350
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = load_font(28)
    content_font = load_font(18)

    primary_dark = (52, 73, 94)

    draw.text((50, 30), "⚡ 电鱼结果", font=title_font, fill=primary_dark)

    thief_name = electric_data.get('thief_name', '未知用户')
    victim_name = electric_data.get('victim_name', '未知用户')
    message = electric_data.get('message', '')

    draw.text((50, 100), f"{thief_name} → {victim_name}", font=content_font, fill=primary_dark)
    draw.text((50, 140), message[:100], font=content_font, fill=primary_dark)

    return image
