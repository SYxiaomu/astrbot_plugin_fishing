"""
称号列表图片生成模块
用于生成用户称号列表的图片消息，包含用户信息展示
参考排行榜的显示比例（800px宽、居中标题、大用户卡片）
"""

from PIL import Image, ImageDraw
from typing import List, Dict, Any
from .gradient_utils import create_vertical_gradient
from .styles import (
    IMG_WIDTH, PADDING,
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


async def draw_titles(
    titles: List[Dict[str, Any]],
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None,
    current_title_id: int = None
) -> Image.Image:
    """
    绘制用户称号列表图片（参考排行榜比例）

    Args:
        titles: 称号列表，每个称号包含 title_id, name, description, is_current
        user_id: 用户ID（用于获取头像和自定义背景）
        nickname: 用户昵称
        data_dir: 数据目录
        current_title_id: 当前装备的称号ID

    Returns:
        PIL.Image.Image: 生成的称号列表图片
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
    equipped_bg = (230, 255, 230, 240)  # 当前装备称号的卡片背景（淡绿）
    equipped_border = COLOR_SUCCESS

    # 统计当前装备称号
    equipped_name = None
    for t in titles:
        if t.get("is_current"):
            equipped_name = t.get("name")
            break

    # 估算高度
    title_item_height = 72  # 每个称号项的高度
    estimated_h = (
        80              # 标题区
        + 120 + 20      # 用户卡片 + 间距
        + 50            # 当前称号提示区
        + len(titles) * title_item_height
        + PADDING * 2   # 底部间距
    )
    height = max(450, estimated_h + 30)

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # ---- 标题（居中，参考排行榜）----
    title_text = "🏅 称号列表"
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

    # 右侧显示称号总数
    stat_text = f"共 {len(titles)} 个称号"
    stat_w, stat_h = _get_text_size(stat_text, subtitle_font, draw)
    draw.text((width - card_margin - stat_w - 20, row_y + 8), stat_text,
              fill=COLOR_GOLD, font=subtitle_font)

    # 当前装备称号显示
    if equipped_name:
        equip_info_text = f"当前装备: {equipped_name}"
        draw.text((card_margin + 20, current_y + 78), equip_info_text,
                  fill=equipped_border, font=small_font)
    else:
        draw.text((card_margin + 20, current_y + 78), "未装备称号",
                  fill=text_secondary, font=small_font)

    current_y += card_h + 20

    # ---- 分割线 ----
    draw.line([(PADDING, current_y), (width - PADDING, current_y)],
              fill=(180, 200, 220), width=2)
    current_y += 18

    # ---- 绘制每个称号（卡片式）----
    for t in titles:
        t_name = t.get("name", "未知称号")
        t_desc = t.get("description", "")
        t_id = t.get("title_id", 0)
        is_current = t.get("is_current", False)

        # 称号卡片背景
        item_x = PADDING
        item_w = width - PADDING * 2
        item_h = 62
        item_fill = equipped_bg if is_current else card_bg
        item_outline = equipped_border if is_current else COLOR_CARD_BORDER
        _draw_rounded_rect(draw,
                           (item_x, current_y, item_x + item_w, current_y + item_h),
                           8, fill=item_fill, outline=item_outline, width=1)

        # 称号名称行
        text_x = item_x + 15
        name_display = f"🏅 {t_name}"
        name_color = COLOR_SUCCESS if is_current else COLOR_TEXT_DARK
        draw.text((text_x, current_y + 10), name_display, fill=name_color, font=content_font)

        # 状态标签（右侧）
        if is_current:
            tag_text = "当前装备"
            tag_w, tag_h = _get_text_size(tag_text, tiny_font, draw)
            tag_x = item_x + item_w - tag_w - 15
            tag_y = current_y + 10
            # 绘制标签背景
            _draw_rounded_rect(draw,
                               (tag_x - 6, tag_y - 2, tag_x + tag_w + 6, tag_y + tag_h + 2),
                               4, fill=COLOR_SUCCESS)
            draw.text((tag_x, tag_y), tag_text, fill=(255, 255, 255), font=tiny_font)

        # 描述行
        desc_y = current_y + 10 + 24
        if t_desc:
            desc_text = t_desc
            draw.text((text_x + 20, desc_y), desc_text, fill=text_secondary, font=small_font)

        # ID 显示（右下角）
        id_text = f"ID: {t_id}"
        id_w, id_h = _get_text_size(id_text, tiny_font, draw)
        draw.text((item_x + item_w - id_w - 15, current_y + item_h - id_h - 6),
                  id_text, fill=text_secondary, font=tiny_font)

        current_y += item_h + 10

    return image


async def draw_no_titles_message(
    message: str,
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None
) -> Image.Image:
    """
    绘制无称号时的提示图片（参考排行榜比例）

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
    card_bg = (255, 255, 255, 240)

    height = 380

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居中）
    title_text = "🏅 称号"
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
