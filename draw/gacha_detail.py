"""
抽卡/十连结果图片生成模块
用于生成单抽、十连、多次十连结果的图片消息，包含用户信息展示
参考排行榜的显示比例（800px宽、居中标题、大用户卡片）
"""

from PIL import Image, ImageDraw
from typing import List, Dict, Any, Optional
from .gradient_utils import create_vertical_gradient
from .styles import (
    IMG_WIDTH, PADDING,
    COLOR_SUCCESS, COLOR_TEXT_DARK, COLOR_GOLD, COLOR_CARD_BG,
    COLOR_CARD_BORDER, COLOR_ACCENT,
    load_font
)
from .utils import get_user_avatar, draw_user_card_bg
from .star_renderer import draw_text_with_stars


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


def _get_rarity_color(rarity: int):
    """根据稀有度返回颜色"""
    if rarity >= 8:
        return (255, 69, 0)      # 橙红 - 传说
    elif rarity >= 6:
        return (148, 0, 211)     # 紫色 - 史诗
    elif rarity >= 4:
        return (0, 100, 200)     # 蓝色 - 稀有
    elif rarity >= 2:
        return (0, 150, 80)      # 绿色 - 精良
    return COLOR_TEXT_DARK        # 白色/默认


def _format_stars(rarity: int) -> str:
    """格式化星星显示（使用★字符，由 draw_text_with_stars 替换为 star.png）"""
    if rarity <= 10:
        return '★' * rarity
    return '★' * 10 + '+'


async def draw_gacha_result(
    items: List[Dict[str, Any]],
    title_text: str,
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None,
    pool_name: str = None,
    extra_info: str = None
) -> Image.Image:
    """
    绘制单抽/单次十连结果图片

    Args:
        items: 抽到的物品列表
        title_text: 标题文字
        user_id: 用户ID
        nickname: 用户昵称
        data_dir: 数据目录
        pool_name: 卡池名称
        extra_info: 额外信息（底部）

    Returns:
        PIL.Image.Image
    """
    width = IMG_WIDTH
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

    # 估算高度
    item_h = 50        # 每个物品卡片高度
    item_gap = 8       # 卡片间距
    extra_h = 8 + (16 if extra_info else 0)
    estimated_h = (
        80              # 标题区
        + 120 + 20      # 用户卡片 + 间距
        + 15            # 分割线
        + len(items) * (item_h + item_gap) + 15
        + extra_h
        + PADDING * 2
    )
    height = max(400, estimated_h + 30)

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # ---- 标题（居中）----
    title_w, title_h = _get_text_size(title_text, title_font, draw)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, fill=primary_dark, font=title_font)
    current_y += title_h + 15

    # ---- 用户信息卡片（参考排行榜比例）----
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

    # 右侧显示获得物品数
    stat_text = f"获得 {len(items)} 件物品"
    stat_w, stat_h = _get_text_size(stat_text, subtitle_font, draw)
    draw.text((width - card_margin - stat_w - 20, row_y + 8), stat_text,
              fill=COLOR_GOLD, font=subtitle_font)

    # 卡池名称
    if pool_name:
        draw.text((card_margin + 20, current_y + 78), f"卡池：{pool_name}",
                  fill=primary_medium, font=small_font)

    current_y += card_h + 20

    # ---- 分割线 ----
    draw.line([(PADDING, current_y), (width - PADDING, current_y)],
              fill=(180, 200, 220), width=2)
    current_y += 15

    # ---- 物品列表（白色卡片背景，参考鱼塘）----
    for item in items:
        item_type = item.get("type", "")
        item_name = item.get("name", "未知")
        item_rarity = item.get("rarity", 1)
        item_qty = item.get("quantity", 1)

        if item_type == "coins":
            line_text = f"💰 {item_qty} 金币"
            clr = COLOR_GOLD
        else:
            stars = _format_stars(item_rarity)
            line_text = f"{stars} {item_name}"
            if item_qty > 1:
                line_text += f" × {item_qty}"
            clr = _get_rarity_color(item_rarity)

        # 白色卡片背景（参考鱼塘每条鱼的卡片样式）
        card_x = PADDING
        card_w = width - PADDING * 2
        _draw_rounded_rect(draw,
                           (card_x, current_y, card_x + card_w, current_y + item_h),
                           6, fill=card_bg, outline=COLOR_CARD_BORDER, width=1)

        draw_text_with_stars(image, draw, (card_x + 12, current_y + (item_h - 18) // 2 - 1), line_text,
                             font=content_font, fill=clr, star_size=24)
        current_y += item_h + item_gap

    # 额外信息
    if extra_info:
        current_y += 8
        draw.text((PADDING + 15, current_y), extra_info, fill=text_secondary, font=tiny_font)

    return image


async def draw_multi_ten_gacha_result(
    times: int,
    total_items: int,
    total_cost: str,
    cost_type: str,
    rarity_counts: Dict[int, int],
    item_counts: Dict[str, int],
    coin_total: int,
    pool_name: str,
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None
) -> Image.Image:
    """
    绘制多次十连合并统计结果图片

    Args:
        times: 十连次数
        total_items: 总物品数
        total_cost: 总消耗金额（字符串）
        cost_type: 消耗类型
        rarity_counts: 稀有度统计 {rarity: count}
        item_counts: 物品名 -> 数量
        coin_total: 金币总数
        pool_name: 卡池名称
        user_id: 用户ID
        nickname: 用户昵称
        data_dir: 数据目录

    Returns:
        PIL.Image.Image
    """
    width = IMG_WIDTH
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

    # 估算高度
    rarity_order = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    rarity_lines = sum(1 for r in rarity_order if rarity_counts.get(r, 0) > 0)
    item_lines = len(item_counts)

    estimated_h = (
        80              # 标题区
        + 120 + 20      # 用户卡片 + 间距
        + 15            # 分割线
        + 26 + 24       # 消耗统计标题 + 内容
        + 26            # 稀有度统计标题
        + rarity_lines * 28       # 稀有度行
        + (28 if coin_total > 0 else 0)
        + 15            # 间距
        + (26 + item_lines * 24 + 15 if item_lines > 0 else 0)
        + PADDING * 2
    )
    height = max(450, estimated_h + 40)

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # ---- 标题 ----
    title_text = f"🎰 {times}次十连结果"
    title_w, title_h = _get_text_size(title_text, title_font, draw)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, fill=primary_dark, font=title_font)
    current_y += title_h + 15

    # ---- 用户信息卡片 ----
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

    # 右侧显示总物品数
    stat_text = f"共 {total_items} 件物品"
    stat_w, stat_h = _get_text_size(stat_text, subtitle_font, draw)
    draw.text((width - card_margin - stat_w - 20, row_y + 8), stat_text,
              fill=COLOR_GOLD, font=subtitle_font)

    # 卡池名称
    if pool_name:
        draw.text((card_margin + 20, current_y + 78), f"卡池：{pool_name}",
                  fill=primary_medium, font=small_font)

    current_y += card_h + 20

    # ---- 分割线 ----
    draw.line([(PADDING, current_y), (width - PADDING, current_y)],
              fill=(180, 200, 220), width=2)
    current_y += 15

    # ---- 消耗统计 ----
    consume_title = "💰 消耗统计"
    draw.text((PADDING + 15, current_y), consume_title, fill=primary_dark, font=content_font)
    current_y += 26
    draw.text((PADDING + 30, current_y), f"消耗{cost_type}：{total_cost}", fill=COLOR_TEXT_DARK, font=small_font)
    current_y += 24

    # ---- 稀有度统计 ----
    rarity_title = "📊 稀有度统计"
    draw.text((PADDING + 15, current_y), rarity_title, fill=primary_dark, font=content_font)
    current_y += 26

    for rarity in rarity_order:
        count = rarity_counts.get(rarity, 0)
        if count > 0:
            stars_display = _format_stars(rarity)
            line = f"{stars_display} {count} 件"
            clr = _get_rarity_color(rarity)
            draw_text_with_stars(image, draw, (PADDING + 30, current_y), line,
                                 font=content_font, fill=clr, star_size=24)
            current_y += 28

    if coin_total > 0:
        draw.text((PADDING + 30, current_y), f"💰 金币总计：{coin_total:,}", fill=COLOR_GOLD, font=content_font)
        current_y += 28

    current_y += 5

    # ---- 物品详情 ----
    if item_counts:
        detail_title = "🎁 物品详情"
        draw.text((PADDING + 15, current_y), detail_title, fill=primary_dark, font=content_font)
        current_y += 26

        sorted_items = sorted(item_counts.items())
        for item_name, count in sorted_items:
            line = f"{item_name} × {count}"
            draw.text((PADDING + 30, current_y), line, fill=COLOR_TEXT_DARK, font=small_font)
            current_y += 24

    return image


def save_image_to_temp(image: Image.Image, prefix: str, data_dir: str) -> str:
    """保存图片到临时目录并返回路径"""
    import tempfile
    import os

    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)

    image.save(temp_path, format='PNG')

    return temp_path
