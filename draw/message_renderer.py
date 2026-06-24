"""
通用消息图片渲染模块
用于将所有文本输出统一渲染为图片消息，包含用户信息卡片
"""

import os
import tempfile
from datetime import datetime
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_TEXT_DARK, COLOR_TEXT_GRAY, COLOR_CARD_BG,
    COLOR_CORNER, COLOR_GOLD, COLOR_RARE,
    COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    load_font, _is_emoji_char, _get_emoji_font
)
from .utils import get_user_avatar, draw_user_card_bg


# 统一边距
LEFT_MARGIN = 25
RIGHT_MARGIN = 25


def _measure_mixed_text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    """逐字符测量含 emoji 混排文本的真实渲染宽度"""
    emoji_font = _get_emoji_font(font.size)
    if emoji_font is None:
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


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """文本自动换行（支持 emoji）"""
    if not text:
        return []

    lines = []
    current_line = ""

    for char in text:
        if char == '\n':
            if current_line:
                lines.append(current_line)
                current_line = ""
            continue
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


def _get_title_color(status_type: str) -> Tuple[int, int, int]:
    """根据状态类型获取标题颜色"""
    if status_type == "success":
        return (46, 125, 50)       # 绿色
    elif status_type == "error":
        return (198, 40, 40)       # 红色
    elif status_type == "warning":
        return (255, 160, 0)       # 橙色
    else:
        return (30, 80, 162)       # 蓝色（info）


def _get_bg_colors(status_type: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """根据状态类型获取渐变背景色"""
    colors = {
        "success": ((200, 235, 200), (245, 255, 245)),
        "error": ((255, 200, 190), (255, 245, 240)),
        "warning": ((255, 230, 190), (255, 250, 240)),
        "info": ((174, 214, 241), (245, 251, 255)),
    }
    return colors.get(status_type, colors["info"])


async def draw_message_image(
    message: str,
    title_text: str = "📋 消息",
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None,
    status_type: str = "info",
    width: int = 500,
) -> Image.Image:
    """
    通用消息图片渲染器

    将文本消息渲染为包含用户信息卡片的图片输出。

    Args:
        message: 消息内容（支持多行，用 \\n 分隔）
        title_text: 标题文本
        user_id: 用户ID（提供时显示用户卡片）
        nickname: 用户昵称
        data_dir: 插件数据目录（用于加载头像和卡片背景）
        status_type: 状态类型：success/info/error/warning
        width: 图片宽度（默认500）

    Returns:
        PIL.Image.Image: 生成的图片
    """
    import asyncio

    try:
        return await asyncio.wait_for(
            _draw_message_image_impl(message, title_text, user_id, nickname, data_dir, status_type, width),
            timeout=10.0
        )
    except asyncio.TimeoutError:
        return _create_fallback_image(message, title_text)


async def _draw_message_image_impl(
    message: str,
    title_text: str,
    user_id: Optional[str],
    nickname: Optional[str],
    data_dir: Optional[str],
    status_type: str,
    width: int,
) -> Image.Image:
    """实际渲染实现"""
    content_font = load_font(16)
    small_font = load_font(14)
    title_font = load_font(24)

    # 预估高度
    lines = message.split('\n')
    content_lines = [l for l in lines if l.strip()]
    user_card_h = 83 if user_id and data_dir else 0
    user_card_margin = 15
    line_height = 22
    estimated_h = (
        30 +                        # 顶部边距
        40 +                        # 标题
        10 +                        # 标题-分割线间距
        2 +                         # 分割线
        12 +                        # 分割线-用户卡片间距
        user_card_h +
        (user_card_margin if user_card_h > 0 else 0) +
        len(content_lines) * line_height +
        30 +                        # 底部边距
        40                          # 页脚
    )
    height = max(200, min(estimated_h, 800))

    bg_top, bg_bot = _get_bg_colors(status_type)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    primary_dark = (52, 73, 94)
    text_secondary = (120, 144, 156)
    title_color = _get_title_color(status_type)

    current_y = 15

    # ---- 标题 ----
    tw, th = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
    title_x = (width - tw) // 2
    draw.text((title_x, current_y), title_text, fill=title_color, font=title_font)
    current_y += th + 10

    # ---- 分割线 ----
    draw.line([(LEFT_MARGIN, current_y), (width - RIGHT_MARGIN, current_y)],
              fill=(180, 200, 220), width=1)
    current_y += 12

    # ---- 用户卡片 ----
    if user_id and data_dir and nickname:
        card_h = 83
        margin = 15
        await draw_user_card_bg(image, draw, user_id, data_dir,
                                (margin, current_y, width - margin, current_y + card_h),
                                8, fallback_fill=COLOR_CARD_BG)
        col_x = margin + 12
        avatar_size = 40
        row_y = current_y + 12
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 10
        draw.text((col_x, row_y + 4), nickname, font=small_font, fill=primary_dark)
        current_y += card_h + 12

    # ---- 消息内容 ----
    max_text_width = width - LEFT_MARGIN - RIGHT_MARGIN
    for line in lines:
        if not line.strip():
            current_y += 6
            continue

        wrapped = _wrap_text(line, content_font, max_text_width)
        for wl in wrapped:
            color = _get_line_color(wl, status_type)
            draw.text((LEFT_MARGIN, current_y), wl, fill=color, font=content_font)
            current_y += line_height
            if current_y > height - 25:
                break

    # ---- 页脚时间戳 ----
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    fw, fh = draw.textbbox((0, 0), footer_text, font=small_font)[2:4]
    footer_x = (width - fw) // 2
    footer_y = height - 30
    draw.text((footer_x, footer_y), footer_text, fill=text_secondary, font=small_font)

    # ---- 四角装饰 ----
    corner_size = 12
    corner_color = COLOR_CORNER
    for (px, py) in [(8, 8), (width - 8 - corner_size, 8),
                     (8, height - 8 - corner_size), (width - 8 - corner_size, height - 8 - corner_size)]:
        draw.ellipse([px, py, px + corner_size, py + corner_size], fill=corner_color)

    return image


def _get_line_color(line: str, status_type: str) -> Tuple[int, int, int]:
    """根据行内容和状态类型获取文本颜色"""
    if any(kw in line for kw in ["✅", "成功", "获得", "金币", "💰"]):
        return (46, 125, 50) if "❌" not in line else (198, 40, 40)
    if any(kw in line for kw in ["❌", "失败", "错误"]):
        return (198, 40, 40)
    return COLOR_TEXT_DARK


def _create_fallback_image(message: str, title_text: str) -> Image.Image:
    """超时回退：简单白底图片"""
    width, height = 500, 300
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    title_font = load_font(22)
    content_font = load_font(16)
    primary_dark = (52, 73, 94)

    draw.text((20, 15), title_text, font=title_font, fill=primary_dark)
    lines = message.split('\n')
    y = 60
    for line in lines[:10]:
        if line.strip():
            draw.text((20, y), line[:50], font=content_font, fill=primary_dark)
            y += 24
    return image


def save_message_image(image: Image.Image, prefix: str, data_dir: str = None) -> str:
    """保存消息图片到临时目录并返回路径"""
    if data_dir:
        tmp_dir = os.path.join(data_dir, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        import time
        path = os.path.join(tmp_dir, f"{prefix}_{int(time.time())}.png")
        image.save(path, format='PNG')
        return path
    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)
    image.save(temp_path, format='PNG')
    return temp_path
