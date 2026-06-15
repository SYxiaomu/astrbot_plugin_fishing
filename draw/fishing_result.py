import os
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from .styles import (
    IMG_WIDTH, PADDING, CORNER_RADIUS,
    COLOR_BACKGROUND, COLOR_HEADER_BG, COLOR_TEXT_WHITE, COLOR_TEXT_DARK,
    COLOR_TEXT_GRAY, COLOR_CARD_BG, COLOR_CARD_BORDER, COLOR_ACCENT,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_LOCK,
    COLOR_GOLD, COLOR_RARE, COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    COLOR_CORNER, load_font
)

def format_rarity_display(rarity: int) -> str:
    """格式化稀有度显示"""
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★★★★★★★★★★+'

def to_percentage(value: float) -> str:
    """将小数转换为百分比字符串"""
    if value is None or value == 0:
        return "0%"
    if value < 1:
        return f"+{value * 100:.1f}%"
    else:
        return f"+{(value - 1) * 100:.1f}%"

async def draw_fishing_result_image(fish_data: Dict[str, Any], user_data: Dict[str, Any]) -> Image.Image:
    """
    绘制钓鱼结果图片

    Args:
        fish_data: 钓到的鱼信息，包括：
            - name: 鱼名
            - rarity: 稀有度
            - weight: 重量
            - value: 价值
            - quality_level: 品质等级 (0=普通, 1=高品质)
            - fish_id: 鱼ID
            - quantity: 数量
        user_data: 用户信息，包括：
            - user_id: 用户ID
            - nickname: 昵称
            - fishing_cost: 本次消耗金币
            - coins_modifier: 当前金币加成
    """
    import asyncio

    try:
        return await asyncio.wait_for(
            _draw_fishing_result_impl(fish_data, user_data),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return _create_fishing_fallback_image(fish_data, user_data)


async def _draw_fishing_result_impl(fish_data: Dict[str, Any], user_data: Dict[str, Any]) -> Image.Image:
    """钓鱼结果图片生成的实际实现"""
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
    gold_color = (218, 165, 32)
    card_bg = (255, 255, 255, 240)

    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache
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

    title_text = "🎣 钓鱼结果"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    draw.text((title_x, current_y), title_text, font=title_font, fill=primary_dark)
    current_y += title_h + 20

    user_card_margin = 30
    card_height = 70
    draw_rounded_rectangle(draw,
                         (user_card_margin, current_y, width - user_card_margin, current_y + card_height),
                         10, fill=card_bg)

    col1_x = user_card_margin + 20
    row1_y = current_y + 12
    row2_y = current_y + 42

    nickname = user_data.get('nickname', '未知用户')
    draw.text((col1_x, row1_y), nickname, font=subtitle_font, fill=primary_medium)

    fishing_cost = user_data.get('fishing_cost', 0)
    coins_modifier = user_data.get('coins_modifier', 0)

    cost_text = f"💸 消耗: {fishing_cost} 金币"
    modifier_text = f"💹 金币加成: {to_percentage(coins_modifier)}"

    cost_w, _ = get_text_size(cost_text, small_font)
    modifier_w, _ = get_text_size(modifier_text, small_font)

    draw.text((col1_x, row2_y), cost_text, font=small_font, fill=text_secondary)
    draw.text((col1_x + cost_w + 30, row2_y), modifier_text, font=small_font, fill=gold_color)

    current_y += card_height + 25

    card_width = width - 60
    card_height = 180

    draw_rounded_rectangle(draw,
                         (30, current_y, width - 30, current_y + card_height),
                         10, fill=card_bg)

    rarity = fish_data.get('rarity', 1)
    rarity_text = format_rarity_display(rarity)

    if rarity >= 7:
        rarity_color = COLOR_REFINE_RED
    elif rarity >= 5:
        rarity_color = COLOR_REFINE_ORANGE
    elif rarity >= 3:
        rarity_color = COLOR_RARE
    else:
        rarity_color = text_secondary

    # 稀有度靠左显示，添加"稀有度: "前缀
    rarity_label = f"稀有度: {rarity_text}"
    draw.text((50, current_y + 15), rarity_label, font=small_font, fill=rarity_color)

    info_y = current_y + 45

    quality_level = fish_data.get('quality_level', 0)
    quality_display = "✨" if quality_level == 1 else ""
    fish_name = fish_data.get('name', '未知鱼')
    quantity = fish_data.get('quantity', 1)
    fish_id = fish_data.get('fish_id', 0)
    weight = fish_data.get('weight', 0)
    value = fish_data.get('value', 0)

    fcode = f"F{fish_id}H" if quality_level == 1 else f"F{fish_id}"

    name_line = f"{fish_name}{quality_display}"
    draw.text((50, info_y), name_line, font=content_font, fill=text_primary)

    detail_y = info_y + 25

    # 构建品质显示文本
    quality_text = "高品质" if quality_level == 1 else "普通"

    details = [
        f"数量: {quantity}",
        f"ID: {fcode}",
        f"品质: {quality_text}",
        f"重量: {weight}g",
        f"价值: {value} 金币"
    ]

    detail_text = " | ".join(details)
    draw.text((50, detail_y), detail_text, font=tiny_font, fill=text_secondary)

    current_y += card_height + 30

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


def _create_fishing_fallback_image(fish_data: Dict[str, Any], user_data: Dict[str, Any]) -> Image.Image:
    """创建简化的回退图像"""
    width, height = 600, 400
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = load_font(28)
    content_font = load_font(18)

    primary_dark = (52, 73, 94)
    text_secondary = (120, 144, 156)

    title_text = "🎣 钓鱼结果"
    draw.text((50, 30), title_text, font=title_font, fill=primary_dark)

    fish_name = fish_data.get('name', '未知鱼')
    rarity = fish_data.get('rarity', 1)
    value = fish_data.get('value', 0)

    draw.text((50, 100), f"鱼名: {fish_name}", font=content_font, fill=primary_dark)
    draw.text((50, 130), f"稀有度: {'★' * rarity}", font=content_font, fill=primary_dark)
    draw.text((50, 160), f"价值: {value} 金币", font=content_font, fill=primary_dark)

    return image
