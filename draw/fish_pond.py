import os
from datetime import datetime
from typing import Dict, Any, List
from PIL import Image, ImageDraw
from .styles import (
    IMG_WIDTH, PADDING, CORNER_RADIUS,
    COLOR_TEXT_DARK, COLOR_CARD_BG,
    COLOR_GOLD, COLOR_RARE, COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    COLOR_CORNER, load_font
)
from .star_renderer import draw_text_with_stars
from .utils import draw_user_card_bg

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

def calculate_dynamic_height(fishes: List[Dict[str, Any]]) -> int:
    """计算动态画布高度（单列布局）"""
    base_height = 220
    fish_count = len(fishes)
    card_height = 100
    card_margin = 15
    fish_section_height = fish_count * card_height + max(fish_count - 1, 0) * card_margin
    return base_height + fish_section_height + 50

async def draw_fish_pond_image(pond_data: Dict[str, Any], user_data: Dict[str, Any], data_dir: str = None) -> Image.Image:
    """
    绘制鱼塘图片

    Args:
        pond_data: 鱼塘数据，包括：
            - fishes: 鱼类列表，每个包含 name, rarity, quantity, quality_level, fish_id, actual_value
            - stats: 统计信息，包括 total_count, total_value
        user_data: 用户信息，包括：
            - user_id: 用户ID
            - nickname: 昵称
            - coins_modifier: 当前金币加成
    """
    import asyncio

    # 对鱼类进行排序：先按稀有度降序，再按价值降序
    fishes = pond_data.get('fishes', [])
    sorted_fishes = sorted(fishes, key=lambda x: (x.get('rarity', 0), x.get('actual_value', 0)), reverse=True)
    pond_data['fishes'] = sorted_fishes

    timeout = 15.0 if len(sorted_fishes) > 50 else 20.0

    try:
        return await asyncio.wait_for(
            _draw_fish_pond_impl(pond_data, user_data, data_dir),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        return _create_pond_fallback_image(pond_data, user_data)


async def _draw_fish_pond_impl(pond_data: Dict[str, Any], user_data: Dict[str, Any], data_dir: str = None) -> Image.Image:
    """鱼塘图片生成的实际实现"""
    fishes = pond_data.get('fishes', [])
    stats = pond_data.get('stats', {})

    width = 800
    height = calculate_dynamic_height(fishes)

    from .gradient_utils import create_vertical_gradient

    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(20)
    small_font = load_font(18)
    tiny_font = load_font(15)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    text_primary = (55, 71, 79)
    text_secondary = (120, 144, 156)
    gold_color = (218, 165, 32)
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

    title_text = "🐟 鱼塘"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    draw.text((title_x, current_y), title_text, font=title_font, fill=primary_dark)
    current_y += title_h + 15

    user_card_margin = 30
    card_height = 120
    await draw_user_card_bg(image, draw, user_data.get('user_id', ''), data_dir,
                            (user_card_margin, current_y, width - user_card_margin, current_y + card_height),
                            10, fallback_fill=card_bg)

    col1_x = user_card_margin + 20
    row1_y = current_y + 18
    row2_y = current_y + 72

    nickname = user_data.get('nickname', '未知用户')
    draw.text((col1_x, row1_y), nickname, font=subtitle_font, fill=primary_medium)

    total_count = stats.get('total_count', 0)
    total_value = stats.get('total_value', 0)
    coins_modifier = user_data.get('coins_modifier', 0)

    count_text = f"🐟 总鱼数: {total_count} 条"
    value_text = f"💰 总价值: {total_value:,} 金币"
    modifier_text = f"💹 金币加成: {to_percentage(coins_modifier)}"

    count_w, _ = get_text_size(count_text, small_font)
    value_w, _ = get_text_size(value_text, small_font)
    modifier_w, _ = get_text_size(modifier_text, small_font)

    gap = 20
    available_w = (width - user_card_margin - 10) - col1_x

    if count_w + gap + value_w + gap + modifier_w <= available_w:
        draw.text((col1_x, row2_y), count_text, font=small_font, fill=text_secondary)
        draw.text((col1_x + count_w + gap, row2_y), value_text, font=small_font, fill=gold_color)
        draw.text((col1_x + count_w + gap + value_w + gap * 2, row2_y), modifier_text, font=small_font, fill=gold_color)
    else:
        draw.text((col1_x, row2_y), count_text, font=small_font, fill=text_secondary)
        draw.text((col1_x + count_w + gap, row2_y), value_text, font=small_font, fill=gold_color)
        draw.text((col1_x, row2_y + 22), modifier_text, font=small_font, fill=gold_color)

    current_y += card_height + 25

    if not fishes:
        draw.text((30, current_y), "🐟 您的鱼塘是空的，快去钓鱼吧！", font=content_font, fill=text_secondary)
        return image

    card_width = width - 60
    card_margin = 15
    card_start_y = current_y

    for i, fish in enumerate(fishes):
        x = 30
        y = card_start_y + i * (100 + card_margin)
        card_height = 100

        draw_rounded_rectangle(draw,
                             (x, y, x + card_width, y + card_height),
                             8, fill=card_bg)

        rarity = fish.get('rarity', 1)
        rarity_text = format_rarity_display(rarity)

        if rarity >= 7:
            rarity_color = COLOR_REFINE_RED
        elif rarity >= 5:
            rarity_color = COLOR_REFINE_ORANGE
        elif rarity >= 3:
            rarity_color = COLOR_RARE
        else:
            rarity_color = text_secondary

        # 稀有度靠左显示，添加"稀有度: "前缀（使用图片渲染★）
        rarity_label = f"稀有度: {rarity_text}"
        draw_text_with_stars(image, draw, (x + 15, y + 12), rarity_label, 
                             font=small_font, fill=rarity_color, star_size=16)

        info_y = y + 40

        fish_name = fish.get('name', '未知鱼')[:15]
        quality_level = fish.get('quality_level', 0)
        quality_display = "✨" if quality_level == 1 else ""
        quantity = fish.get('quantity', 1)
        fish_id = fish.get('fish_id', 0)
        actual_value = fish.get('actual_value', 0)

        fcode = f"F{fish_id}H" if quality_level == 1 else f"F{fish_id}"

        name_line = f"{fish_name}{quality_display}"
        draw.text((x + 15, info_y), name_line, font=content_font, fill=text_primary)

        detail_y = info_y + 25

        # 构建品质显示文本
        quality_text = "高品质" if quality_level == 1 else "普通"

        details = [
            f"数量: {quantity}",
            f"ID: {fcode}",
            f"品质: {quality_text}",
            f"价值: {actual_value} 金币"
        ]

        detail_text = " | ".join(details)
        draw.text((x + 15, detail_y), detail_text, font=tiny_font, fill=text_secondary)

    current_y = card_start_y + len(fishes) * (100 + card_margin) + 20

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


def _create_pond_fallback_image(pond_data: Dict[str, Any], user_data: Dict[str, Any]) -> Image.Image:
    """创建简化的回退图像"""
    width, height = 600, 400
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = load_font(28)
    content_font = load_font(18)

    primary_dark = (52, 73, 94)

    stats = pond_data.get('stats', {})
    total_count = stats.get('total_count', 0)
    total_value = stats.get('total_value', 0)

    draw.text((50, 30), "鱼塘", font=title_font, fill=primary_dark)
    draw.text((50, 100), f"总鱼数: {total_count} 条", font=content_font, fill=primary_dark)
    draw.text((50, 130), f"总价值: {total_value} 金币", font=content_font, fill=primary_dark)

    return image
