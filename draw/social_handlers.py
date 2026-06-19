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
from .star_renderer import draw_text_with_stars

def format_rarity_display(rarity: int) -> str:
    """格式化稀有度显示"""
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★★★★★★★★★★+'

async def draw_steal_result_image(steal_data: Dict[str, Any]) -> Image.Image:
    """
    绘制偷鱼结果图片

    Args:
        steal_data: 偷鱼结果数据，包括：
            - success: 是否成功
            - thief_name: 偷窃者昵称
            - victim_name: 受害者昵称
            - message: 结果消息
            - stolen_fish: 偷到的鱼列表（可选）
    """
    import asyncio

    try:
        return await asyncio.wait_for(
            _draw_steal_result_impl(steal_data),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return _create_steal_fallback_image(steal_data)


async def _draw_steal_result_impl(steal_data: Dict[str, Any]) -> Image.Image:
    """偷鱼结果图片生成的实际实现"""
    width = 600

    # 计算动态高度
    base_height = 350  # 增加基础高度以容纳更多信息
    message = steal_data.get('message', '')
    stolen_fish = steal_data.get('stolen_fish', [])

    # 估算消息占用的高度
    message_lines = len(message.split('\n')) if message else 0
    message_height = min(message_lines, 6) * 25 + 30 if message and not stolen_fish else 0

    # 估算鱼列表占用的高度 - 每个鱼需要更多空间显示详细信息
    fish_count = len(stolen_fish)
    fish_height = 30 + min(fish_count, 5) * 80 + (30 if fish_count > 5 else 0) if stolen_fish else 0

    height = base_height + message_height + fish_height + 50  # 50是底部边距
    height = max(height, 450)  # 最小高度
    height = min(height, 900)  # 最大高度限制

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

    title_text = "🎭 偷鱼结果"
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

    thief_name = steal_data.get('thief_name', '未知用户')
    victim_name = steal_data.get('victim_name', '未知用户')

    action_text = f"{thief_name} → {victim_name}"
    draw.text((col1_x, row1_y), action_text, font=subtitle_font, fill=primary_medium)

    success = steal_data.get('success', False)
    status_text = "✅ 偷鱼成功" if success else "❌ 偷鱼失败"
    status_color = success_color if success else error_color
    draw.text((col1_x, row2_y), status_text, font=small_font, fill=status_color)

    current_y += card_height + 25

    # 显示偷到的鱼列表 - 采用与钓鱼结果一致的卡片式布局
    stolen_fish = steal_data.get('stolen_fish', [])
    if stolen_fish:
        fish_count = len(stolen_fish)

        for i, fish in enumerate(stolen_fish[:6]):
            fish_name = fish.get('name', '未知鱼')
            quantity = fish.get('quantity', 1)
            value = fish.get('value', 0)
            rarity = fish.get('rarity', 1)
            quality_level = fish.get('quality_level', 0)
            fish_id = fish.get('fish_id', 0)

            # 鱼卡片高度
            fish_card_height = 80

            draw_rounded_rectangle(draw,
                                 (30, current_y, width - 30, current_y + fish_card_height),
                                 10, fill=card_bg)

            # 稀有度显示 - 靠左，添加"稀有度:"前缀
            rarity_text = format_rarity_display(rarity)

            if rarity >= 7:
                rarity_color = COLOR_REFINE_RED
            elif rarity >= 5:
                rarity_color = COLOR_REFINE_ORANGE
            elif rarity >= 3:
                rarity_color = COLOR_RARE
            else:
                rarity_color = text_secondary

            rarity_label = f"稀有度: {rarity_text}"
            draw_text_with_stars(image, draw, (50, current_y + 12), rarity_label, 
                                 font=small_font, fill=rarity_color, star_size=16)

            # 鱼名和品质
            info_y = current_y + 38
            quality_display = "✨" if quality_level == 1 else ""

            fcode = f"F{fish_id}H" if quality_level == 1 else f"F{fish_id}"

            name_line = f"{fish_name}{quality_display}"
            draw.text((50, info_y), name_line, font=content_font, fill=text_primary)

            # 详细信息行
            detail_y = info_y + 25

            quality_text = "高品质" if quality_level == 1 else "普通"

            details = [
                f"数量: {quantity}",
                f"ID: {fcode}",
                f"品质: {quality_text}",
                f"价值: {value} 金币"
            ]

            detail_text = " | ".join(details)
            draw.text((50, detail_y), detail_text, font=tiny_font, fill=text_secondary)

            current_y += fish_card_height + 15

            if i >= 5:
                remaining = fish_count - 6
                if remaining > 0:
                    more_text = f"... 还有 {remaining} 种鱼未显示"
                    more_w, _ = get_text_size(more_text, tiny_font)
                    more_x = (width - more_w) // 2
                    draw.text((more_x, current_y), more_text, font=tiny_font, fill=text_secondary)
                    current_y += 25
                break

    # 如果没有鱼列表但有消息，显示消息
    message = steal_data.get('message', '')
    if message and not stolen_fish:
        card_width = width - 60
        lines = []
        for line in message.split('\n'):
            if len(line) > 40:
                lines.append(line[:40])
                lines.append(line[40:])
            else:
                lines.append(line)

        max_lines = min(len(lines), 6)
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


def _create_steal_fallback_image(steal_data: Dict[str, Any]) -> Image.Image:
    """创建简化的回退图像"""
    width, height = 600, 350
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = load_font(28)
    content_font = load_font(18)

    primary_dark = (52, 73, 94)

    draw.text((50, 30), "🎭 偷鱼结果", font=title_font, fill=primary_dark)

    thief_name = steal_data.get('thief_name', '未知用户')
    victim_name = steal_data.get('victim_name', '未知用户')
    message = steal_data.get('message', '')

    draw.text((50, 100), f"{thief_name} → {victim_name}", font=content_font, fill=primary_dark)
    draw.text((50, 140), message[:100], font=content_font, fill=primary_dark)

    return image
