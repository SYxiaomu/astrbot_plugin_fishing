"""
命运之轮图片生成模块
用于生成命运之轮游戏相关的各种图片消息
"""

import asyncio
import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_GOLD,
    COLOR_TEXT_DARK, COLOR_TEXT_WHITE, COLOR_CARD_BG,
    load_font
)
from .utils import get_user_avatar, draw_user_card_bg

# 统一左侧边距
LEFT_MARGIN = 20


async def draw_wheel_of_fate_start(entry_fee: int, current_coins: int,
                                    user_id: str = None, nickname: str = None,
                                    data_dir: str = None) -> Image.Image:
    """绘制命运之轮开始图片"""
    width = 400
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(16)
    small_font = load_font(14)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    text_secondary = (120, 144, 156)
    card_bg = (255, 255, 255, 240)

    # 估算高度
    base_h = 360
    image = create_vertical_gradient(width, base_h, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "🎡 命运之轮"
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

    # 入场费信息（居左）
    fee_text = f"入场费: {entry_fee:,} 金币"
    draw.text((LEFT_MARGIN, current_y), fee_text, fill=COLOR_GOLD, font=subtitle_font)
    _, fh = draw.textbbox((0, 0), fee_text, font=subtitle_font)[2:4]
    current_y += fh + 8

    # 当前余额（居左）
    balance_text = f"当前余额: {current_coins:,} 金币"
    draw.text((LEFT_MARGIN, current_y), balance_text, fill=COLOR_TEXT_DARK, font=content_font)
    _, bh = draw.textbbox((0, 0), balance_text, font=content_font)[2:4]
    current_y += bh + 18

    # 提示信息（居左）
    tips = [
        "这是一个挑战勇气与运气的游戏！",
        "你将面临连续的抉择，",
        "幸存得越久，奖励越丰厚，",
        "但失败将让你失去一切。",
        "",
        "游戏共10层，每层都会提示你",
        "当前的奖金和下一层的成功率。",
        "你需要在60秒内回复【继续】或【放弃】",
        "来决定你的命运！"
    ]

    for tip in tips:
        if tip:
            draw.text((LEFT_MARGIN, current_y), tip, fill=COLOR_TEXT_DARK, font=content_font)
        current_y += 20

    return image


async def draw_wheel_of_fate_result(message: str, user_nickname: str,
                                     user_id: str = None, data_dir: str = None) -> Image.Image:
    """绘制命运之轮结果图片（通用）"""
    width = 400
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(16)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    card_bg = (255, 255, 255, 240)

    # 先计算内容高度
    lines = message.split('\n')
    max_lines = 12
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("...")

    content_lines = [l for l in lines if l.strip()]
    estimated_h = 160 + len(content_lines) * 22 + 30
    height = max(300, min(estimated_h, 700))

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "🎡 命运之轮"
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
    if user_id and data_dir and user_nickname:
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 10
    if user_nickname:
        draw.text((col_x, row_y + 4), user_nickname, font=subtitle_font, fill=primary_medium)
    current_y += card_h + 15

    # 绘制消息内容（居左显示）
    line_height = 22
    y_pos = current_y
    for line in lines:
        if not line.strip():
            y_pos += 6
            continue
        wrapped = _wrap_text(line, content_font, width - LEFT_MARGIN * 2)
        for wl in wrapped:
            draw.text((LEFT_MARGIN, y_pos), wl, fill=COLOR_TEXT_DARK, font=content_font)
            y_pos += line_height
            if y_pos > height - 20:
                break

    return image


async def draw_wheel_of_fate_help() -> Image.Image:
    """绘制命运之轮帮助说明图片"""
    width = 400
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(14)

    primary_dark = (52, 73, 94)

    help_content = [
        ("这是一个挑战勇气与运气的游戏！", False),
        ("你将面临连续的抉择，", False),
        ("幸存得越久，奖励越丰厚，", False),
        ("但失败将让你失去一切。", False),
        ("", False),
        ("【玩法】", True),
        ("使用 /命运之轮 <金额> 开始游戏。", False),
        ("(金额最低 100 金币，无上限)", False),
        ("", False),
        ("【规则】", True),
        ("游戏共10层，每层机器人都会提示你", False),
        ("当前的奖金和下一层的成功率。", False),
        ("你需要在 60 秒内回复【继续】或【放弃】", False),
        ("来决定你的命运！", False),
        ("超时将自动放弃并结算当前奖金。", False),
        ("", False),
        ("【概率详情】", True),
        ("前往第 1 层：65% 成功率", False),
        ("前往第 2 层：60% 成功率", False),
        ("前往第 3 层：55% 成功率", False),
        ("前往第 4 层：50% 成功率", False),
        ("前往第 5 层：45% 成功率", False),
        ("前往第 6 层：40% 成功率", False),
        ("前往第 7 层：35% 成功率", False),
        ("前往第 8 层：30% 成功率", False),
        ("前往第 9 层：25% 成功率", False),
        ("前往第10 层：20% 成功率", False),
        ("", False),
        ("祝你好运，挑战者！", False),
    ]

    # 估算高度
    h = 80 + len(help_content) * 18 + 20
    image = create_vertical_gradient(width, h, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "🎡 命运之轮 玩法说明"
    draw.text((LEFT_MARGIN, 15), title_text, fill=primary_dark, font=title_font)
    _, th = draw.textbbox((0, 0), title_text, font=title_font)[2:4]

    # 内容（居左）
    current_y = 15 + th + 12
    for text, is_heading in help_content:
        if not text.strip():
            current_y += 8
            continue
        font = subtitle_font if is_heading else content_font
        fill_color = COLOR_GOLD if is_heading else COLOR_TEXT_DARK
        draw.text((LEFT_MARGIN, current_y), text, fill=fill_color, font=font)
        _, lh = draw.textbbox((0, 0), text, font=font)[2:4]
        current_y += lh + 4

    return image


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    简单的文本换行处理
    按字符数估算换行位置
    """
    if not text:
        return []
    
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [text]


def save_image_to_temp(image: Image.Image, prefix: str, data_dir: str) -> str:
    """保存图片到临时目录并返回路径"""
    import tempfile
    import time
    
    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)
    
    # 保存图片
    image.save(temp_path, format='PNG')
    
    return temp_path
