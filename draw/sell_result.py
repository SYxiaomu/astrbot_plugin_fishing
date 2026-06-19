"""
出售结果和金币余额图片生成模块
用于生成出售操作结果和金币余额查询相关的图片消息
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_SUCCESS, COLOR_GOLD, COLOR_TEXT_DARK, COLOR_CARD_BG,
    load_font, _is_emoji_char, _get_emoji_font
)
from .utils import get_user_avatar, draw_user_card_bg

# 统一左侧边距
LEFT_MARGIN = 20


async def draw_sell_result(message: str,
                           user_id: str = None,
                           nickname: str = None,
                           data_dir: str = None) -> Image.Image:
    """
    绘制品出售结果图片（通用）

    适用：全部出售、出售保留、砸锅卖铁、按稀有度出售、出售鱼竿、出售饰品

    Args:
        message: 出售结果消息文本
        user_id: 用户ID（用于获取头像）
        nickname: 用户昵称
        data_dir: 数据目录

    Returns:
        PIL.Image.Image: 生成的出售结果图像
    """
    width = 400
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(16)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    card_bg = (255, 255, 255, 240)

    # 预处理内容行
    lines = message.split('\n')
    max_lines = 20
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("...")

    content_lines = [l for l in lines if l.strip()]
    estimated_h = 160 + len(content_lines) * 24 + 30
    height = max(280, min(estimated_h, 700))

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "💰 出售结果"
    draw.text((LEFT_MARGIN, 15), title_text, fill=primary_dark, font=title_font)
    _, th = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
    current_y = 15 + th + 10

    # 用户卡片（带头像）
    card_h = 83
    margin = 15
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (margin, current_y, width - margin, current_y + card_h),
                            8, fallback_fill=card_bg)
    col_x = margin + 12
    avatar_size = 40
    row_y = current_y + 12
    if user_id and data_dir and nickname:
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 10
    if nickname:
        draw.text((col_x, row_y + 4), nickname, font=subtitle_font, fill=primary_medium)
    current_y += card_h + 15

    # 绘制消息内容（居左显示）
    line_height = 22
    for line in lines:
        if not line.strip():
            current_y += 6
            continue
        wrapped = _wrap_text(line, content_font, width - LEFT_MARGIN * 2)
        for wl in wrapped:
            # 金币数值用金色高亮
            color = COLOR_GOLD if _is_coin_value_line(wl) else COLOR_TEXT_DARK
            draw.text((LEFT_MARGIN, current_y), wl, fill=color, font=content_font)
            current_y += line_height
            if current_y > height - 20:
                break

    return image


async def draw_coins_balance(coins: int,
                             premium_currency: int = 0,
                             user_id: str = None,
                             nickname: str = None,
                             data_dir: str = None) -> Image.Image:
    """
    绘制货币余额查询图片（双列布局：左金币 / 右高级货币）

    Args:
        coins: 用户当前金币数量
        premium_currency: 用户当前高级货币数量
        user_id: 用户ID（用于获取头像）
        nickname: 用户昵称
        data_dir: 数据目录

    Returns:
        PIL.Image.Image: 生成的货币余额图像
    """
    width = 400
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(16)
    big_num_font = load_font(28)
    small_font = load_font(14)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    text_secondary = (120, 144, 156)
    card_bg = (255, 255, 255, 240)
    premium_color = (100, 149, 237)  # 矢车菊蓝，区分高级货币

    height = 260
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "💰 资产概览"
    draw.text((LEFT_MARGIN, 15), title_text, fill=primary_dark, font=title_font)
    _, th = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
    current_y = 15 + th + 10

    # 用户卡片（带头像）
    card_h = 83
    margin = 15
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (margin, current_y, width - margin, current_y + card_h),
                            8, fallback_fill=card_bg)
    col_x = margin + 12
    avatar_size = 40
    row_y = current_y + 12
    if user_id and data_dir and nickname:
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 10
    if nickname:
        draw.text((col_x, row_y + 4), nickname, font=subtitle_font, fill=primary_medium)
    current_y += card_h + 15

    # 双列货币卡片
    gap = 10  # 两列间距
    col_w = (width - margin * 2 - gap) // 2
    col_left_x = margin
    col_right_x = margin + col_w + gap
    col_card_h = 80

    # 左列：金币
    draw.rounded_rectangle((col_left_x, current_y, col_left_x + col_w, current_y + col_card_h),
                           radius=8, fill=card_bg)
    # 标签
    draw.text((col_left_x + 10, current_y + 8), "💰 金币", fill=text_secondary, font=small_font)
    # 数值
    coins_text = f"{coins:,}"
    draw.text((col_left_x + 10, current_y + 30), coins_text, fill=COLOR_GOLD, font=big_num_font)

    # 右列：高级货币
    draw.rounded_rectangle((col_right_x, current_y, col_right_x + col_w, current_y + col_card_h),
                           radius=8, fill=card_bg)
    # 标签
    draw.text((col_right_x + 10, current_y + 8), "💎 高级货币", fill=text_secondary, font=small_font)
    # 数值
    premium_text = f"{premium_currency:,}"
    draw.text((col_right_x + 10, current_y + 30), premium_text, fill=premium_color, font=big_num_font)

    return image


def _measure_mixed_text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    """
    逐字符测量含 emoji 混排文本的真实渲染宽度。
    与 styles.py 中的 _emoji_aware_draw_text 逻辑一致：
    - emoji 字符用 Segoe UI Emoji 测量
    - ★☆ 字符用 Segoe UI Symbol 测量
    - 其他字符用主字体测量
    """
    emoji_font = _get_emoji_font(font.size)
    if emoji_font is None:
        # 没有 emoji 字体，退回到整体测量
        temp_img = Image.new('RGB', (1, 1), (255, 255, 255))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    temp_img = Image.new('RGB', (1, 1), (255, 255, 255))
    temp_draw = ImageDraw.Draw(temp_img)
    total_w = 0
    for char in text:
        if _is_emoji_char(char):
            if ord(char) in (0x2605, 0x2606):
                char_font = _get_emoji_font(font.size, for_star=True) or emoji_font
            else:
                char_font = emoji_font
        else:
            char_font = font
        try:
            char_bbox = temp_draw.textbbox((0, 0), char, font=char_font)
            total_w += char_bbox[2] - char_bbox[0]
        except:
            total_w += font.size
    return total_w


def _is_coin_value_line(line: str) -> bool:
    """判断一行文本是否包含金币数值（用于高亮）"""
    return any(kw in line for kw in ["金币", "获得", "价值", "总价值"])


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """简单的文本换行处理（考虑 emoji 字符宽度）"""
    if not text:
        return []

    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        line_width = _measure_mixed_text_width(test_line, font)

        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]
