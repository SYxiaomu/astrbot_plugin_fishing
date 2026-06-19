"""
成就列表图片生成模块
用于生成用户成就列表的图片消息，包含用户信息展示
参考排行榜的显示比例（800px宽、居中标题、大用户卡片）
"""

from PIL import Image, ImageDraw
from typing import List, Dict, Any
from datetime import datetime
from .gradient_utils import create_vertical_gradient
from .styles import (
    IMG_WIDTH, PADDING, CORNER_RADIUS,
    COLOR_SUCCESS, COLOR_TEXT_DARK, COLOR_GOLD, COLOR_CARD_BG,
    COLOR_CARD_BORDER, COLOR_ACCENT,
    load_font
)
from .utils import get_user_avatar, draw_user_card_bg


def _draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = bbox
    draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill, outline=fill)
    draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill, outline=fill)
    draw.ellipse((x1, y1, x1 + 2 * radius, y1 + 2 * radius), fill=fill, outline=fill)
    draw.ellipse((x2 - 2 * radius, y1, x2, y1 + 2 * radius), fill=fill, outline=fill)
    draw.ellipse((x1, y2 - 2 * radius, x1 + 2 * radius, y2), fill=fill, outline=fill)
    draw.ellipse((x2 - 2 * radius, y2 - 2 * radius, x2, y2), fill=fill, outline=fill)
    if outline:
        draw.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
        draw.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
        draw.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)
        draw.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)
        draw.line((x1 + radius, y1, x2 - radius, y1), fill=outline, width=width)
        draw.line((x1 + radius, y2, x2 - radius, y2), fill=outline, width=width)
        draw.line((x1, y1 + radius, x1, y2 - radius), fill=outline, width=width)
        draw.line((x2, y1 + radius, x2, y2 - radius), fill=outline, width=width)


def _get_text_size(text, font, draw):
    """获取文本宽高"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


async def draw_achievements(
    achievements: List[Dict[str, Any]],
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None,
    safe_datetime_handler=None
) -> Image.Image:
    """
    绘制用户成就列表图片（参考排行榜比例）

    Args:
        achievements: 成就列表，每个成就包含 id, name, description, progress, target, completed_at
        user_id: 用户ID（用于获取头像和自定义背景）
        nickname: 用户昵称
        data_dir: 数据目录
        safe_datetime_handler: 安全的日期时间格式化函数

    Returns:
        PIL.Image.Image: 生成的成就列表图片
    """
    width = IMG_WIDTH  # 800px，与排行榜一致

    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(36)
    subtitle_font = load_font(22)
    content_font = load_font(18)
    small_font = load_font(16)
    tiny_font = load_font(14)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    text_secondary = (120, 144, 156)
    card_bg = (255, 255, 255, 240)
    progress_bar_bg = (220, 230, 240)
    progress_bar_fill_incomplete = (100, 149, 237)

    # 统计完成数
    completed_count = sum(1 for ach in achievements if ach.get("completed_at"))
    total_count = len(achievements)

    # 估算高度
    ach_item_height = 90  # 每个成就项的高度（留足空间）
    estimated_h = (
        80            # 标题区
        + 120 + 20    # 用户卡片 + 间距
        + 60          # 统计区
        + total_count * ach_item_height
        + PADDING * 2  # 底部间距
    )
    height = max(500, estimated_h + 30)

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # ---- 标题（居中，参考排行榜）----
    title_text = "🏆成就列表"
    title_w, title_h = _get_text_size(title_text, title_font, draw)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, fill=primary_dark, font=title_font)
    current_y += title_h + 15

    # ---- 用户信息卡片（参考排行榜/背包比例）----
    card_h = 120
    card_margin = PADDING  # 30
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (card_margin, current_y, width - card_margin, current_y + card_h),
                            10, fallback_fill=card_bg)
    _draw_rounded_rect(draw,
                       (card_margin, current_y, width - card_margin, current_y + card_h),
                       10, outline=COLOR_CARD_BORDER, width=2)

    col_x = card_margin + 20
    avatar_size = 60
    row_y = current_y + 18

    if user_id and data_dir and nickname:
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 20

    if nickname:
        draw.text((col_x, row_y + 8), nickname, font=subtitle_font, fill=primary_dark)

    # 右侧显示完成统计
    stat_text = f"{completed_count}/{total_count} 已完成"
    stat_w, stat_h = _get_text_size(stat_text, subtitle_font, draw)
    draw.text((width - card_margin - stat_w - 20, row_y + 8), stat_text,
              fill=COLOR_GOLD, font=subtitle_font)

    # 用户卡片下方显示进度条
    bar_y = current_y + 75
    bar_x = card_margin + 20
    bar_w = width - card_margin * 2 - 40
    bar_h = 10
    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                           radius=5, fill=progress_bar_bg)
    if total_count > 0:
        fill_w = int(bar_w * completed_count / total_count)
        if fill_w > 0:
            draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h),
                                   radius=5, fill=COLOR_GOLD)
    pct = int(completed_count / total_count * 100) if total_count > 0 else 0
    pct_text = f"完成进度: {pct}%"
    draw.text((bar_x, bar_y + bar_h + 4), pct_text, fill=text_secondary, font=tiny_font)

    current_y += card_h + 15

    # ---- 分割线 ----
    draw.line([(PADDING, current_y), (width - PADDING, current_y)],
              fill=(180, 200, 220), width=2)
    current_y += 15

    # ---- 绘制每个成就（卡片式）----
    for ach in achievements:
        ach_name = ach.get("name", "未知成就")
        ach_desc = ach.get("description", "")
        ach_progress = ach.get("progress", 0)
        ach_target = ach.get("target", 1)
        completed_at = ach.get("completed_at")

        is_completed = completed_at is not None

        # 状态图标和颜色
        if is_completed:
            status_icon = "✅"
            name_color = COLOR_SUCCESS
        else:
            status_icon = "⬜"
            name_color = COLOR_TEXT_DARK

        # 成就卡片背景
        item_x = PADDING
        item_w = width - PADDING * 2
        item_h = 68
        _draw_rounded_rect(draw,
                           (item_x, current_y, item_x + item_w, current_y + item_h),
                           8, fill=card_bg, outline=COLOR_CARD_BORDER, width=1)

        # 成就名称行
        name_text = f"{status_icon} {ach_name}"
        text_x = item_x + 15
        draw.text((text_x, current_y + 10), name_text, fill=name_color, font=content_font)

        # 成就描述行
        desc_y = current_y + 10 + 22
        if ach_desc:
            draw.text((text_x + 24, desc_y), ach_desc, fill=text_secondary, font=small_font)
            desc_y += 20

        # 进度行
        if is_completed:
            if safe_datetime_handler and completed_at:
                time_str = safe_datetime_handler(completed_at)
                progress_text = f"已完成 - {time_str}"
            else:
                progress_text = "已完成"
            draw.text((text_x + 24, desc_y), progress_text,
                      fill=COLOR_SUCCESS, font=tiny_font)
        else:
            # 进度条
            p_bar_x = text_x + 24
            p_bar_w = item_w - 200
            p_bar_h = 8
            draw.rounded_rectangle((p_bar_x, desc_y + 2, p_bar_x + p_bar_w, desc_y + 2 + p_bar_h),
                                   radius=4, fill=progress_bar_bg)
            fill_ratio = min(ach_progress / max(ach_target, 1), 1.0)
            fill_w = int(p_bar_w * fill_ratio)
            if fill_w > 0:
                draw.rounded_rectangle((p_bar_x, desc_y + 2, p_bar_x + fill_w, desc_y + 2 + p_bar_h),
                                       radius=4, fill=progress_bar_fill_incomplete)
            # 进度文本（右侧）
            progress_text = f"{ach_progress}/{ach_target}"
            draw.text((p_bar_x + p_bar_w + 10, desc_y), progress_text,
                      fill=text_secondary, font=tiny_font)

        current_y += item_h + 10

    return image


async def draw_no_achievements_message(
    message: str,
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None
) -> Image.Image:
    """
    绘制无成就时的提示图片（参考排行榜比例）

    Args:
        message: 提示消息
        user_id: 用户ID
        nickname: 用户昵称
        data_dir: 数据目录

    Returns:
        PIL.Image.Image: 生成的图片
    """
    width = IMG_WIDTH  # 800px
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)

    title_font = load_font(36)
    subtitle_font = load_font(22)
    content_font = load_font(18)

    primary_dark = (52, 73, 94)
    primary_medium = (74, 105, 134)
    card_bg = (255, 255, 255, 240)

    height = 380

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居中）
    title_text = "🏆成就"
    title_w, title_h = _get_text_size(title_text, title_font, draw)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, fill=primary_dark, font=title_font)
    current_y += title_h + 15

    # 用户信息卡片（参考排行榜比例）
    card_h = 120
    card_margin = PADDING
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (card_margin, current_y, width - card_margin, current_y + card_h),
                            10, fallback_fill=card_bg)
    _draw_rounded_rect(draw,
                       (card_margin, current_y, width - card_margin, current_y + card_h),
                       10, outline=COLOR_CARD_BORDER, width=2)

    col_x = card_margin + 20
    avatar_size = 60
    row_y = current_y + 18

    if user_id and data_dir and nickname:
        if avatar := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar, (col_x, row_y), avatar)
            col_x += avatar_size + 20
    if nickname:
        draw.text((col_x, row_y + 8), nickname, font=subtitle_font, fill=primary_dark)
    current_y += card_h + 20

    # 提示信息（居中）
    msg_w, msg_h = _get_text_size(message, content_font, draw)
    msg_x = (width - msg_w) // 2
    draw.text((msg_x, current_y), message, fill=COLOR_TEXT_DARK, font=content_font)

    return image


def save_image_to_temp(image: Image.Image, prefix: str, data_dir: str) -> str:
    """保存图片到临时目录并返回路径"""
    import tempfile
    import os

    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)

    image.save(temp_path, format='PNG')

    return temp_path
