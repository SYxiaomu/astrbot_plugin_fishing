"""
擦弹游戏图片生成模块
用于生成擦弹游戏相关的各种图片消息
"""

import asyncio
import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_GOLD,
    COLOR_TEXT_DARK, COLOR_TEXT_WHITE, COLOR_CARD_BG,
    load_font
)
from .utils import get_user_avatar, draw_user_card_bg

# 统一左侧边距
LEFT_MARGIN = 20


async def draw_wipe_bomb_result(
    contribution: int,
    multiplier: float,
    reward: int,
    profit: int,
    remaining_today: int,
    suppression_notice: str = "",
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None
) -> Image.Image:
    """绘制擦弹结果图片"""
    width = 400

    # 根据结果决定背景色
    if multiplier >= 3:
        bg_top = (255, 223, 150)
        bg_bot = (255, 245, 210)
    elif multiplier >= 1:
        bg_top = (174, 214, 241)
        bg_bot = (245, 251, 255)
    else:
        bg_top = (255, 190, 180)
        bg_bot = (255, 240, 240)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(16)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    card_bg = (255, 255, 255, 240)

    # 估算高度
    detail_count = 4 + (1 if suppression_notice else 0)
    estimated_h = 160 + detail_count * 26 + 40
    height = max(300, min(estimated_h, 600))

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    if multiplier >= 3:
        title_text = "💣 大成功！"
    elif multiplier >= 1:
        title_text = "💣 擦弹结果"
    else:
        title_text = "💣 擦弹失败"

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

    # 倍率信息（居左）
    if multiplier < 0.01:
        multiplier_formatted = f"{multiplier:.4f}"
    else:
        multiplier_formatted = f"{multiplier:.2f}"

    result_text = f"获得 {multiplier_formatted} 倍奖励"
    draw.text((LEFT_MARGIN, current_y), result_text, fill=COLOR_GOLD, font=subtitle_font)
    _, rh = draw.textbbox((0, 0), result_text, font=subtitle_font)[2:4]
    current_y += rh + 12

    # 详细信息（居左）
    detail_lines = [
        f"投入: {contribution} 金币",
        f"奖励金额: {reward} 金币",
    ]
    if profit >= 0:
        detail_lines.append(f"盈利: +{profit} 金币")
    else:
        detail_lines.append(f"亏损: -{abs(profit)} 金币")
    detail_lines.append(f"剩余擦弹次数: {remaining_today} 次")
    if suppression_notice:
        detail_lines.append("")
        detail_lines.append(suppression_notice)

    line_height = 24
    for line in detail_lines:
        if not line.strip():
            current_y += 8
            continue
        draw.text((LEFT_MARGIN, current_y), line, fill=COLOR_TEXT_DARK, font=content_font)
        current_y += line_height

    return image


async def draw_wipe_bomb_history(history: List[Dict[str, Any]],
                                  user_id: str = None, nickname: str = None,
                                  data_dir: str = None) -> Image.Image:
    """绘制擦弹记录图片"""
    width = 400
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(14)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    card_bg = (255, 255, 255, 240)

    # 估算高度
    line_height = 20
    record_height = line_height * 4 + 12
    base_height = 140 + len(history) * record_height
    height = max(250, base_height)

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "📜 擦弹记录"
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

    # 分割线
    draw.line([(LEFT_MARGIN, current_y), (width - LEFT_MARGIN, current_y)], fill=(180, 200, 220), width=2)
    current_y += 10

    # 绘制记录（居左）
    for record in history:
        # 时间
        time_text = f"时间: {record['timestamp']}"
        draw.text((LEFT_MARGIN, current_y), time_text, fill=COLOR_TEXT_DARK, font=content_font)
        current_y += line_height

        # 投入和奖励
        amount_text = f"投入: {record['contribution']} 金币  |  奖励: {record['reward']} 金币"
        draw.text((LEFT_MARGIN, current_y), amount_text, fill=COLOR_TEXT_DARK, font=content_font)
        current_y += line_height

        # 计算盈亏
        profit = record["reward"] - record["contribution"]
        if profit >= 0:
            profit_text = f"盈利: +{profit}"
        else:
            profit_text = f"亏损: {profit}"

        multiplier_val = record["multiplier"]
        rate_text = f"倍率: {multiplier_val}  ({profit_text})"
        profit_color = COLOR_SUCCESS if profit >= 0 else COLOR_ERROR
        draw.text((LEFT_MARGIN, current_y), rate_text, fill=profit_color, font=content_font)
        current_y += line_height

        # 分割线
        draw.line([(LEFT_MARGIN, current_y), (width - LEFT_MARGIN, current_y)], fill=(210, 220, 230), width=1)
        current_y += 10

    return image


async def draw_wipe_bomb_error(message: str,
                                user_id: str = None, nickname: str = None,
                                data_dir: str = None) -> Image.Image:
    """绘制擦弹错误/提示图片"""
    width = 400
    bg_top = (255, 190, 180)
    bg_bot = (255, 240, 240)

    title_font = load_font(24)
    subtitle_font = load_font(18)
    content_font = load_font(16)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    card_bg = (255, 255, 255, 240)

    # 估算高度
    estimated_h = 200
    if user_id and data_dir and nickname:
        estimated_h += 75

    image = create_vertical_gradient(width, estimated_h, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居左）
    title_text = "💣 擦弹"
    draw.text((LEFT_MARGIN, 15), title_text, fill=primary_dark, font=title_font)
    _, th = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
    current_y = 15 + th + 10

    # 用户卡片（可选）
    if user_id and data_dir and nickname:
        card_h = 83
        margin = 15
        await draw_user_card_bg(image, draw, user_id, data_dir,
                                (margin, current_y, width - margin, current_y + card_h),
                                8, fallback_fill=card_bg)
        col_x = margin + 12
        avatar_size = 40
        row_y = current_y + 12
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 10
        draw.text((col_x, row_y + 4), nickname, font=subtitle_font, fill=primary_medium)
        current_y += card_h + 15

    # 错误信息（居左）
    draw.text((LEFT_MARGIN, current_y + 5), message, fill=COLOR_TEXT_DARK, font=content_font)

    return image


def save_image_to_temp(image: Image.Image, prefix: str, data_dir: str) -> str:
    """保存图片到临时目录并返回路径"""
    import tempfile
    
    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)
    
    image.save(temp_path, format='PNG')
    
    return temp_path
