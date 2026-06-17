import os
from datetime import datetime
from typing import Dict, Any, List
from PIL import Image, ImageDraw
from .styles import (
    IMG_WIDTH, PADDING, CORNER_RADIUS,
    COLOR_TEXT_DARK, COLOR_CARD_BG,
    COLOR_GOLD, COLOR_RARE, COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    COLOR_CORNER, COLOR_SUCCESS, COLOR_ERROR, load_font_with_emoji_fallback
)


def format_rarity_display(rarity: int) -> str:
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★★★★★★★★★★+'


async def draw_steal_result_image(steal_data: Dict[str, Any]) -> Image.Image:
    import asyncio
    try:
        return await asyncio.wait_for(
            _draw_steal_result_impl(steal_data),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return _create_steal_fallback_image(steal_data)


async def _draw_steal_result_impl(steal_data: Dict[str, Any]) -> Image.Image:
    from .gradient_utils import create_vertical_gradient
    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache

    width = 600
    stolen_fish = steal_data.get('stolen_fish', [])
    message = steal_data.get('message', '')
    success = steal_data.get('success', False)

    # ---- 预渲染：文本换行 ----
    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    content_font = load_font_with_emoji_fallback(20)
    small_font = load_font_with_emoji_fallback(18)
    tiny_font = load_font_with_emoji_fallback(16)

    max_text_width = width - 100

    message_lines: List[str] = []
    if message:
        # 按 \n 分割消息，每行作为独立的一行显示
        for raw_line in message.split('\n'):
            # 跳过包含"本次成功率"的行（如果有的话）
            if '本次成功率' in raw_line:
                continue
            # 对每行进行宽度换行处理
            wrapped = wrap_text_by_width_optimized(raw_line, content_font, max_text_width, text_cache)
            message_lines.extend(wrapped if wrapped else [''])

    # ---- 动态高度 ----
    CARD_PAD = 30
    TITLE_H = 60
    USER_CARD_H = 80
    FOOTER_H = 60
    LINE_H = 28
    FISH_CARD_H = 100
    FISH_GAP = 15

    y = CARD_PAD
    y += TITLE_H
    y += USER_CARD_H + 20

    fish_display = min(len(stolen_fish), 8)
    fish_section_h = fish_display * (FISH_CARD_H + FISH_GAP) if fish_display else 0
    if fish_display and len(stolen_fish) > 8:
        fish_section_h += 25
    y += fish_section_h

    msg_section_h = 0
    if message_lines and not stolen_fish:
        capped = message_lines[:8]
        msg_section_h = len(capped) * LINE_H + 40
        y += msg_section_h + 15

    y += FOOTER_H + 10
    height = max(y, 380)

    # ---- 创建画布 ----
    image = create_vertical_gradient(width, height, (174, 214, 241), (245, 251, 255))
    draw = ImageDraw.Draw(image)

    title_font = load_font_with_emoji_fallback(32)
    subtitle_font = load_font_with_emoji_fallback(24)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    text_primary = (55, 71, 79)
    text_secondary = (120, 144, 156)
    success_color = (46, 125, 50)
    error_color = (220, 53, 69)
    gold_color = (218, 165, 32)
    card_bg = (255, 255, 255, 240)

    def draw_rounded_rect(bbox, radius, fill=None):
        x1, y1, x2, y2 = bbox
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        draw.ellipse([x1, y1, x1 + 2 * radius, y1 + 2 * radius], fill=fill)
        draw.ellipse([x2 - 2 * radius, y1, x2, y1 + 2 * radius], fill=fill)
        draw.ellipse([x1, y2 - 2 * radius, x1 + 2 * radius, y2], fill=fill)
        draw.ellipse([x2 - 2 * radius, y2 - 2 * radius, x2, y2], fill=fill)

    # ---- 标题 ----
    cur_y = CARD_PAD
    title_text = "🎭 偷鱼结果"
    tw, th = get_text_size(title_text, title_font)
    draw.text(((width - tw) // 2, cur_y), title_text, font=title_font, fill=primary_dark)
    cur_y += TITLE_H

    # ---- 用户卡片 ----
    draw_rounded_rect((CARD_PAD, cur_y, width - CARD_PAD, cur_y + USER_CARD_H), 10, card_bg)
    cx = CARD_PAD + 20

    thief_name = steal_data.get('thief_name', '未知用户')
    victim_name = steal_data.get('victim_name', '未知用户')
    draw.text((cx, cur_y + 14), f"{thief_name}  →  {victim_name}", font=subtitle_font, fill=primary_medium)

    status_text = "偷鱼成功" if success else "偷鱼失败"
    status_color = success_color if success else error_color
    draw.text((cx, cur_y + 46), status_text, font=small_font, fill=status_color)
    cur_y += USER_CARD_H + 20

    # ---- 鱼卡片列表 ----
    if stolen_fish:
        for i, fish in enumerate(stolen_fish[:8]):
            fy = cur_y
            draw_rounded_rect((CARD_PAD, fy, width - CARD_PAD, fy + FISH_CARD_H), 10, card_bg)

            rarity = fish.get('rarity', 1)
            if rarity >= 7:
                rarity_color = COLOR_REFINE_RED
            elif rarity >= 5:
                rarity_color = COLOR_REFINE_ORANGE
            elif rarity >= 3:
                rarity_color = COLOR_RARE
            else:
                rarity_color = text_secondary

            rarity_label = f"稀有度: {format_rarity_display(rarity)}"
            draw.text((cx, fy + 12), rarity_label, font=small_font, fill=rarity_color)

            info_y = fy + 40

            fish_name = fish.get('name', '未知鱼')[:15]
            quality_level = fish.get('quality_level', 0)
            draw.text((cx, info_y), f"{fish_name}", font=content_font, fill=text_primary)

            detail_y = info_y + 25

            quantity = fish.get('quantity', 1)
            fish_id = fish.get('fish_id', 0)
            value = fish.get('value', 0)
            fcode = f"F{fish_id}H" if quality_level == 1 else f"F{fish_id}"
            quality_text = "高品质" if quality_level == 1 else "普通"
            details = [
                f"数量: {quantity}",
                f"ID: {fcode}",
                f"品质: {quality_text}",
                f"价值: {value} 金币"
            ]
            detail_text = " | ".join(details)
            draw.text((cx, detail_y), detail_text, font=tiny_font, fill=text_secondary)

            cur_y += FISH_CARD_H + FISH_GAP

        if len(stolen_fish) > 8:
            remaining = len(stolen_fish) - 8
            more_text = f"… 还有 {remaining} 种鱼未显示"
            mw, _ = get_text_size(more_text, tiny_font)
            draw.text(((width - mw) // 2, cur_y), more_text, font=tiny_font, fill=text_secondary)
            cur_y += 25

    # ---- 消息卡片（失败时） ----
    if message_lines and not stolen_fish:
        capped = message_lines[:8]
        msg_card_h = len(capped) * LINE_H + 40
        draw_rounded_rect((CARD_PAD, cur_y, width - CARD_PAD, cur_y + msg_card_h), 10, card_bg)

        ty = cur_y + 20
        for line in capped:
            draw.text((cx, ty), line, font=content_font, fill=text_primary)
            ty += LINE_H
        cur_y += msg_card_h + 15

    # ---- 页脚 ----
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    fw, fh = get_text_size(footer_text, tiny_font)
    draw.text(((width - fw) // 2, cur_y), footer_text, font=tiny_font, fill=text_secondary)

    # ---- 四角装饰 ----
    cs = 15
    cc = COLOR_CORNER
    for (px, py) in [(8, 8), (width - 23, 8), (8, height - 23), (width - 23, height - 23)]:
        draw.ellipse([px, py, px + cs, py + cs], fill=cc)

    return image


def _create_steal_fallback_image(steal_data: Dict[str, Any]) -> Image.Image:
    width, height = 600, 350
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    title_font = load_font(28)
    content_font = load_font(18)
    primary_dark = (52, 73, 94)
    draw.text((50, 30), "🎭 偷鱼结果", font=title_font, fill=primary_dark)
    draw.text((50, 100), f"{steal_data.get('thief_name', '?')} → {steal_data.get('victim_name', '?')}", font=content_font, fill=primary_dark)
    draw.text((50, 140), steal_data.get('message', '')[:100], font=content_font, fill=primary_dark)
    return image
