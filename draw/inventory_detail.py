"""
分类背包详情图片生成 - 鱼竿、饰品、道具的单独图片输出
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from PIL import Image, ImageDraw
from .styles import (
    COLOR_GOLD, COLOR_RARE, COLOR_REFINE_RED, COLOR_REFINE_ORANGE,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_LOCK,
    COLOR_CORNER, load_font
)
from .star_renderer import draw_text_with_stars
from .utils import get_user_avatar, draw_user_card_bg


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
        return f"{value * 100:.2f}%"
    else:
        return f"{(value - 1) * 100:.2f}%"


def _create_base_image(width: int, height: int):
    """创建基础渐变背景图像"""
    from .gradient_utils import create_vertical_gradient
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    return image, bg_top, bg_bot


def _setup_fonts():
    """设置字体"""
    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(18)
    small_font = load_font(16)
    tiny_font = load_font(14)
    return title_font, subtitle_font, content_font, small_font, tiny_font


def _setup_colors():
    """设置颜色"""
    return {
        'primary_dark': (52, 73, 94),
        'primary_medium': (74, 105, 134),
        'primary_light': (108, 142, 191),
        'text_primary': (55, 71, 79),
        'text_secondary': (120, 144, 156),
        'text_muted': (176, 190, 197),
        'success_color': COLOR_SUCCESS,
        'warning_color': COLOR_WARNING,
        'error_color': COLOR_ERROR,
        'lock_color': COLOR_LOCK,
        'gold_color': COLOR_GOLD,
        'rare_color': COLOR_RARE,
        'card_bg': (255, 255, 255, 240),
    }


def draw_rounded_rectangle(draw, bbox, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill, outline=outline, width=width)


def _draw_corner_decorations(draw, width, height):
    """绘制四角装饰"""
    corner_size = 15
    corner_color = COLOR_CORNER
    draw.ellipse([8, 8, 8 + corner_size, 8 + corner_size], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, 8, width - 8, 8 + corner_size], fill=corner_color)
    draw.ellipse([8, height - 8 - corner_size, 8 + corner_size, height - 8], fill=corner_color)
    draw.ellipse([width - 8 - corner_size, height - 8 - corner_size, width - 8, height - 8], fill=corner_color)


def _draw_footer(draw, current_y, width, small_font, text_secondary):
    """绘制底部信息"""
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer_w, footer_h = draw.textbbox((0, 0), footer_text, font=small_font)[2:4]
    footer_x = (width - footer_w) // 2
    draw.text((footer_x, current_y), footer_text, font=small_font, fill=text_secondary)
    current_y += footer_h + 15
    return current_y


def _ensure_height(image, draw, height, needed_height, width, bg_top, bg_bot):
    """动态扩展画布高度"""
    if needed_height <= height:
        return image, draw, height
    new_h = needed_height
    new_image = Image.new('RGB', (width, new_h), (255, 255, 255))
    from .gradient_utils import create_vertical_gradient
    bg = create_vertical_gradient(width, new_h, bg_top, bg_bot)
    new_image.paste(bg, (0, 0))
    new_image.paste(image, (0, 0))
    new_image_draw = ImageDraw.Draw(new_image)
    return new_image, new_image_draw, new_h


# ========== 鱼竿图片 ==========

def _calc_rods_height(rods: List[Dict[str, Any]]) -> int:
    """计算鱼竿区域高度"""
    base_height = 200
    rod_count = len(rods)
    if rod_count > 0:
        rows = (rod_count + 1) // 2
        avg_height = 200
        rod_height = 35 + rows * avg_height + (rows - 1) * 15
    else:
        rod_height = 35 + 50
    return base_height + rod_height + 80


async def draw_rods_image(rods: List[Dict[str, Any]], user_id: str,
                           nickname: str, is_filtered: bool,
                           total_count: int, displayed_count: int,
                           data_dir: str = None) -> Image.Image:
    """绘制鱼竿详情图片"""
    try:
        return await asyncio.wait_for(
            _draw_rods_impl(rods, user_id, nickname, is_filtered, total_count, displayed_count, data_dir),
            timeout=20.0
        )
    except asyncio.TimeoutError:
        return _create_fallback_image("鱼竿", total_count)


async def _draw_rods_impl(rods, user_id, nickname, is_filtered, total_count, displayed_count, data_dir):
    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache

    width = 800
    height = _calc_rods_height(rods)
    image, bg_top, bg_bot = _create_base_image(width, height)
    draw = ImageDraw.Draw(image)
    title_font, subtitle_font, content_font, small_font, tiny_font = _setup_fonts()
    colors = _setup_colors()

    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    def wrap_text_by_width(text, font, max_width):
        return wrap_text_by_width_optimized(text, font, max_width, text_cache)

    def ensure_height(needed):
        nonlocal image, draw, height
        image, draw, height = _ensure_height(image, draw, height, needed, width, bg_top, bg_bot)

    # 标题
    if is_filtered:
        title_text = f"🎣 鱼竿 (共{total_count}根，显示{displayed_count}根)"
    else:
        title_text = f"🎣 鱼竿 (共{total_count}根)"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, font=title_font, fill=colors['primary_dark'])
    current_y += title_h + 15

    # 用户信息卡片（带头像）
    card_height = 105
    user_card_margin = 30
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (user_card_margin, current_y, width - user_card_margin, current_y + card_height),
                            10, fallback_fill=colors['card_bg'])

    col1_x = user_card_margin + 20
    avatar_size = 50
    row1_y = current_y + 15

    if user_id and data_dir:
        if avatar_image := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar_image, (col1_x, row1_y), avatar_image)
            col1_x += avatar_size + 15

    draw.text((col1_x, row1_y), nickname, font=subtitle_font, fill=colors['primary_medium'])
    current_y += card_height + 15

    if is_filtered:
        hint_text = "💡 数量过多，仅显示5星以上鱼竿"
        draw.text((30, current_y), hint_text, font=small_font, fill=colors['warning_color'])
        current_y += 22

    if not rods:
        draw.text((30, current_y), "🎣 您还没有鱼竿，快去商店购买或抽奖获得吧！", font=content_font, fill=colors['text_muted'])
        current_y += 50
        image, draw, height = _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, colors['text_secondary'], _ROD_HINTS)
        return image

    # 鱼竿卡片
    card_width = (width - 90) // 2
    card_margin = 15
    row_start_y = current_y
    next_row_start_y = current_y

    for i, rod in enumerate(rods):
        row = i // 2
        col = i % 2
        x = 30 + col * (card_width + card_margin)

        if col == 0:
            row_start_y = next_row_start_y
            left_h = _measure_rod_card_height(rod, card_width, tiny_font, wrap_text_by_width, get_text_size)
            right_index = i + 1
            right_h = _measure_rod_card_height(rods[right_index], card_width, tiny_font, wrap_text_by_width, get_text_size) if right_index < len(rods) else 0
            row_h = max(left_h, right_h)
            y = row_start_y
            next_row_start_y = row_start_y + row_h + card_margin
            card_h = row_h
        else:
            y = row_start_y
            card_h = row_h
        ensure_height(y + card_h + 40)

        draw_rounded_rectangle(draw, (x, y, x + card_width, y + card_h), 8, fill=colors['card_bg'])

        # 名称和ID
        rod_name = rod['name'][:15] + "..." if len(rod['name']) > 15 else rod['name']
        display_code = rod.get('display_code', f"ID{rod.get('instance_id', 'N/A')}")
        name_w, _ = get_text_size(rod_name, content_font)
        draw.text((x + 15, y + 15), rod_name, font=content_font, fill=colors['text_primary'])
        id_w, id_h = get_text_size("ID: 000000", tiny_font)
        draw.text((x + 15 + name_w + 10, y + 15 + (get_text_size(rod_name, content_font)[1] - id_h)),
                  f"ID: {display_code}", font=tiny_font, fill=colors['primary_light'])

        # 锁定状态
        if rod.get('is_locked', False):
            label_text = "🔒 锁定保护中"
            lw, lh = get_text_size(label_text, tiny_font)
            draw.text((x + card_width - 15 - lw, y + 12), label_text, font=tiny_font, fill=colors['lock_color'])

        # 稀有度和精炼等级
        rarity = rod.get('rarity', 1)
        refine_level = rod.get('refine_level', 1)
        if refine_level >= 10:
            star_color = COLOR_REFINE_RED
        elif refine_level >= 6:
            star_color = COLOR_REFINE_ORANGE
        elif rarity > 4 and refine_level > 4:
            star_color = colors['rare_color']
        elif rarity > 3:
            star_color = colors['warning_color']
        else:
            star_color = colors['text_secondary']
        rarity_refine_text = f"{format_rarity_display(rarity)} Lv.{refine_level}"
        draw_text_with_stars(image, draw, (x + 15, y + 40), rarity_refine_text,
                             font=small_font, fill=star_color, star_size=18)

        # 装备状态和耐久度
        is_equipped = rod.get('is_equipped', False)
        current_dur = rod.get('current_durability')
        max_dur = rod.get('max_durability')

        if is_equipped:
            draw.text((x + 15, y + 60), "已装备", font=small_font, fill=colors['success_color'])
        else:
            draw.text((x + 15, y + 60), "未装备", font=small_font, fill=colors['text_muted'])

        if max_dur is not None and current_dur is not None:
            durability_text = f"耐久: {current_dur}/{max_dur}"
            durability_ratio = current_dur / max_dur if max_dur > 0 else 0
            if durability_ratio > 0.6:
                dur_color = colors['success_color']
            elif durability_ratio > 0.3:
                dur_color = colors['warning_color']
            else:
                dur_color = colors['error_color']
            draw.text((x + 15, y + 80), durability_text, font=tiny_font, fill=dur_color)
            bonus_y = y + 105
        elif current_dur is None:
            draw.text((x + 15, y + 80), "耐久: ∞", font=tiny_font, fill=colors['primary_light'])
            bonus_y = y + 105
        else:
            bonus_y = y + 85

        # 属性加成
        if rod.get('bonus_fish_quality_modifier', 1.0) != 1.0 and rod.get('bonus_fish_quality_modifier', 1) != 1 and rod.get('bonus_fish_quality_modifier', 1) > 0:
            draw.text((x + 15, bonus_y), f"鱼类品质加成: {to_percentage(rod['bonus_fish_quality_modifier'])}", font=tiny_font, fill=colors['primary_light'])
            bonus_y += 18
        if rod.get('bonus_fish_quantity_modifier', 1.0) != 1.0 and rod.get('bonus_fish_quantity_modifier', 1) != 1 and rod.get('bonus_fish_quantity_modifier', 1) > 0:
            draw.text((x + 15, bonus_y), f"鱼类数量加成: {to_percentage(rod['bonus_fish_quantity_modifier'])}", font=tiny_font, fill=colors['primary_light'])
            bonus_y += 18
        if rod.get('bonus_rare_fish_chance', 1.0) != 1.0 and rod.get('bonus_rare_fish_chance', 1) != 1 and rod.get('bonus_rare_fish_chance', 1) > 0:
            draw.text((x + 15, bonus_y), f"钓鱼几率加成: {to_percentage(rod['bonus_rare_fish_chance'])}", font=tiny_font, fill=colors['primary_light'])
            bonus_y += 18

        # 描述
        if rod.get('description'):
            available_width = card_width - 30
            lines = wrap_text_by_width(rod['description'], tiny_font, available_width)
            line_h = get_text_size("测", tiny_font)[1] + 2
            max_lines = max((y + card_h - 20) - bonus_y, 0) // line_h
            if max_lines > 0:
                for li, line in enumerate(lines[:max_lines]):
                    draw.text((x + 15, bonus_y + li * line_h), line, font=tiny_font, fill=colors['text_secondary'])

    current_y = next_row_start_y + 15

    # 过滤提示
    if is_filtered:
        clean_text = "🧹 建议清理低品质鱼竿：/出售所有鱼竿"
        draw.text((30, current_y), clean_text, font=small_font, fill=colors['text_secondary'])
        current_y += 25

    image, draw, height = _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, colors['text_secondary'], _ROD_HINTS)
    return image


def _measure_rod_card_height(rod, card_width, tiny_font, wrap_fn, get_text_size_fn):
    """测量鱼竿卡片高度"""
    line_h = get_text_size_fn("测", tiny_font)[1] + 2
    attr_lines = 0
    if rod.get('bonus_fish_quality_modifier', 1.0) not in (1.0, 1) and rod.get('bonus_fish_quality_modifier', 0) > 0:
        attr_lines += 1
    if rod.get('bonus_fish_quantity_modifier', 1.0) not in (1.0, 1) and rod.get('bonus_fish_quantity_modifier', 0) > 0:
        attr_lines += 1
    if rod.get('bonus_rare_fish_chance', 1.0) not in (1.0, 1) and rod.get('bonus_rare_fish_chance', 0) > 0:
        attr_lines += 1
    desc_lines = 0
    if rod.get('description'):
        desc_lines = len(wrap_fn(rod['description'], tiny_font, card_width - 30))
    durability_height = 20 if (rod.get('max_durability') is not None or rod.get('current_durability') is None) else 0
    header_height = 85 + durability_height
    bottom_pad = 20
    return max(header_height + attr_lines * 18 + desc_lines * line_h + bottom_pad, 160)


# ========== 饰品图片 ==========

def _calc_accessories_height(accessories: List[Dict[str, Any]]) -> int:
    """计算饰品区域高度"""
    base_height = 200
    acc_count = len(accessories)
    if acc_count > 0:
        rows = (acc_count + 1) // 2
        avg_height = 200
        acc_height = 35 + rows * avg_height + (rows - 1) * 15
    else:
        acc_height = 35 + 50
    return base_height + acc_height + 80


async def draw_accessories_image(accessories: List[Dict[str, Any]], user_id: str,
                                  nickname: str, is_filtered: bool,
                                  total_count: int, displayed_count: int,
                                  data_dir: str = None) -> Image.Image:
    """绘制饰品详情图片"""
    try:
        return await asyncio.wait_for(
            _draw_accessories_impl(accessories, user_id, nickname, is_filtered, total_count, displayed_count, data_dir),
            timeout=20.0
        )
    except asyncio.TimeoutError:
        return _create_fallback_image("饰品", total_count)


async def _draw_accessories_impl(accessories, user_id, nickname, is_filtered, total_count, displayed_count, data_dir):
    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache

    width = 800
    height = _calc_accessories_height(accessories)
    image, bg_top, bg_bot = _create_base_image(width, height)
    draw = ImageDraw.Draw(image)
    title_font, subtitle_font, content_font, small_font, tiny_font = _setup_fonts()
    colors = _setup_colors()

    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    def wrap_text_by_width(text, font, max_width):
        return wrap_text_by_width_optimized(text, font, max_width, text_cache)

    def ensure_height(needed):
        nonlocal image, draw, height
        image, draw, height = _ensure_height(image, draw, height, needed, width, bg_top, bg_bot)

    # 标题
    if is_filtered:
        title_text = f"💍 饰品 (共{total_count}个，显示{displayed_count}个)"
    else:
        title_text = f"💍 饰品 (共{total_count}个)"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, font=title_font, fill=colors['primary_dark'])
    current_y += title_h + 15

    # 用户信息卡片（带头像）
    card_height = 105
    user_card_margin = 30
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (user_card_margin, current_y, width - user_card_margin, current_y + card_height),
                            10, fallback_fill=colors['card_bg'])

    col1_x = user_card_margin + 20
    avatar_size = 50
    row1_y = current_y + 15

    if user_id and data_dir:
        if avatar_image := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar_image, (col1_x, row1_y), avatar_image)
            col1_x += avatar_size + 15

    draw.text((col1_x, row1_y), nickname, font=subtitle_font, fill=colors['primary_medium'])
    current_y += card_height + 15

    if is_filtered:
        hint_text = "💡 数量过多，仅显示5星以上饰品"
        draw.text((30, current_y), hint_text, font=small_font, fill=colors['warning_color'])
        current_y += 22

    if not accessories:
        draw.text((30, current_y), "💍 您还没有饰品，快去商店购买或抽奖获得吧！", font=content_font, fill=colors['text_muted'])
        current_y += 50
        image, draw, height = _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, colors['text_secondary'], _ACCESSORY_HINTS)
        return image

    # 饰品卡片
    card_width = (width - 90) // 2
    card_margin = 15
    row_start_y = current_y
    next_row_start_y = current_y

    for i, accessory in enumerate(accessories):
        row = i // 2
        col = i % 2
        x = 30 + col * (card_width + card_margin)

        if col == 0:
            row_start_y = next_row_start_y
            left_h = _measure_accessory_card_height(accessory, card_width, tiny_font, wrap_text_by_width, get_text_size)
            right_index = i + 1
            right_h = _measure_accessory_card_height(accessories[right_index], card_width, tiny_font, wrap_text_by_width, get_text_size) if right_index < len(accessories) else 0
            row_h = max(left_h, right_h)
            y = row_start_y
            next_row_start_y = row_start_y + row_h + card_margin
            card_h = row_h
        else:
            y = row_start_y
            card_h = row_h
        ensure_height(y + card_h + 40)

        draw_rounded_rectangle(draw, (x, y, x + card_width, y + card_h), 8, fill=colors['card_bg'])

        # 名称和ID
        acc_name = accessory['name'][:15] + "..." if len(accessory['name']) > 15 else accessory['name']
        display_code = accessory.get('display_code', f"ID{accessory.get('instance_id', 'N/A')}")
        name_w, _ = get_text_size(acc_name, content_font)
        draw.text((x + 15, y + 15), acc_name, font=content_font, fill=colors['text_primary'])
        id_w, id_h = get_text_size("ID: 000000", tiny_font)
        draw.text((x + 15 + name_w + 10, y + 15 + (get_text_size(acc_name, content_font)[1] - id_h)),
                  f"ID: {display_code}", font=tiny_font, fill=colors['primary_light'])

        # 锁定状态
        if accessory.get('is_locked', False):
            label_text = "🔒 锁定"
            lw, lh = get_text_size(label_text, tiny_font)
            draw.text((x + card_width - 15 - lw, y + 12), label_text, font=tiny_font, fill=colors['lock_color'])

        # 稀有度和精炼等级
        rarity = accessory.get('rarity', 1)
        refine_level = accessory.get('refine_level', 1)
        if refine_level >= 10:
            star_color = COLOR_REFINE_RED
        elif refine_level >= 6:
            star_color = COLOR_REFINE_ORANGE
        elif rarity > 4 and refine_level > 4:
            star_color = colors['rare_color']
        elif rarity > 3:
            star_color = colors['warning_color']
        else:
            star_color = colors['text_secondary']
        accessory_rarity_text = f"{format_rarity_display(rarity)} Lv.{refine_level}"
        draw_text_with_stars(image, draw, (x + 15, y + 40), accessory_rarity_text,
                             font=small_font, fill=star_color, star_size=18)

        # 装备状态
        is_equipped = accessory.get('is_equipped', False)
        if is_equipped:
            draw.text((x + 15, y + 60), "已装备", font=small_font, fill=colors['success_color'])
        else:
            draw.text((x + 15, y + 60), "未装备", font=small_font, fill=colors['text_muted'])

        # 属性加成
        bonus_y = y + 85
        if accessory.get('bonus_fish_quality_modifier', 1.0) != 1.0 and accessory.get('bonus_fish_quality_modifier', 1) != 1 and accessory.get('bonus_fish_quality_modifier', 1) > 0:
            draw.text((x + 15, bonus_y), f"鱼类品质加成: {to_percentage(accessory['bonus_fish_quality_modifier'])}", font=tiny_font, fill=colors['primary_light'])
            bonus_y += 18
        if accessory.get('bonus_fish_quantity_modifier', 1.0) != 1.0 and accessory.get('bonus_fish_quantity_modifier', 1) != 1 and accessory.get('bonus_fish_quantity_modifier', 1) > 0:
            draw.text((x + 15, bonus_y), f"鱼类数量加成: {to_percentage(accessory['bonus_fish_quantity_modifier'])}", font=tiny_font, fill=colors['primary_light'])
            bonus_y += 18
        if accessory.get('bonus_rare_fish_chance', 1.0) != 1.0 and accessory.get('bonus_rare_fish_chance', 1) != 1 and accessory.get('bonus_rare_fish_chance', 1) > 0:
            draw.text((x + 15, bonus_y), f"钓鱼几率加成: {to_percentage(accessory['bonus_rare_fish_chance'])}", font=tiny_font, fill=colors['primary_light'])
            bonus_y += 18
        if accessory.get('bonus_coin_modifier', 1.0) != 1.0 and accessory.get('bonus_coin_modifier', 1) != 1 and accessory.get('bonus_coin_modifier', 1) > 0:
            draw.text((x + 15, bonus_y), f"金币加成: {to_percentage(accessory['bonus_coin_modifier'])}", font=tiny_font, fill=colors['gold_color'])
            bonus_y += 18

        # 描述
        if accessory.get('description'):
            available_width = card_width - 30
            lines = wrap_text_by_width(accessory['description'], tiny_font, available_width)
            line_h = get_text_size("测", tiny_font)[1] + 2
            max_lines = max((y + card_h - 20) - bonus_y, 0) // line_h
            if max_lines > 0:
                for li, line in enumerate(lines[:max_lines]):
                    draw.text((x + 15, bonus_y + li * line_h), line, font=tiny_font, fill=colors['text_secondary'])

    current_y = next_row_start_y + 15

    if is_filtered:
        clean_text = "🧹 建议清理低品质饰品：/出售所有饰品"
        draw.text((30, current_y), clean_text, font=small_font, fill=colors['text_secondary'])
        current_y += 25

    image, draw, height = _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, colors['text_secondary'], _ACCESSORY_HINTS)
    return image


def _measure_accessory_card_height(acc, card_width, tiny_font, wrap_fn, get_text_size_fn):
    """测量饰品卡片高度"""
    line_h = get_text_size_fn("测", tiny_font)[1] + 2
    attr_lines = 0
    if acc.get('bonus_fish_quality_modifier', 1.0) not in (1.0, 1) and acc.get('bonus_fish_quality_modifier', 0) > 0:
        attr_lines += 1
    if acc.get('bonus_fish_quantity_modifier', 1.0) not in (1.0, 1) and acc.get('bonus_fish_quantity_modifier', 0) > 0:
        attr_lines += 1
    if acc.get('bonus_rare_fish_chance', 1.0) not in (1.0, 1) and acc.get('bonus_rare_fish_chance', 0) > 0:
        attr_lines += 1
    if acc.get('bonus_coin_modifier', 1.0) not in (1.0, 1) and acc.get('bonus_coin_modifier', 0) > 0:
        attr_lines += 1
    desc_lines = 0
    if acc.get('description'):
        desc_lines = len(wrap_fn(acc['description'], tiny_font, card_width - 30))
    header_height = 85
    bottom_pad = 20
    return max(header_height + attr_lines * 18 + desc_lines * line_h + bottom_pad, 160)


# ========== 道具图片 ==========

def _calc_items_height(items: List[Dict[str, Any]]) -> int:
    """计算道具区域高度"""
    base_height = 200
    item_count = len(items)
    if item_count > 0:
        rows = (item_count + 1) // 2
        avg_height = 130
        item_height = 35 + rows * avg_height + (rows - 1) * 15
    else:
        item_height = 35 + 50
    return base_height + item_height + 80


async def draw_items_image(items: List[Dict[str, Any]], user_id: str,
                            nickname: str, data_dir: str = None) -> Image.Image:
    """绘制道具详情图片"""
    try:
        return await asyncio.wait_for(
            _draw_items_impl(items, user_id, nickname, data_dir),
            timeout=20.0
        )
    except asyncio.TimeoutError:
        return _create_fallback_image("道具", len(items))


async def _draw_items_impl(items, user_id, nickname, data_dir):
    from .text_utils import get_text_size_cached, wrap_text_by_width_optimized, create_text_cache

    width = 800
    height = _calc_items_height(items)
    image, bg_top, bg_bot = _create_base_image(width, height)
    draw = ImageDraw.Draw(image)
    title_font, subtitle_font, content_font, small_font, tiny_font = _setup_fonts()
    colors = _setup_colors()

    text_cache = create_text_cache()

    def get_text_size(text, font):
        return get_text_size_cached(text, font, text_cache)

    def wrap_text_by_width(text, font, max_width):
        return wrap_text_by_width_optimized(text, font, max_width, text_cache)

    def ensure_height(needed):
        nonlocal image, draw, height
        image, draw, height = _ensure_height(image, draw, height, needed, width, bg_top, bg_bot)

    # 标题
    title_text = f"📦 道具 (共{len(items)}个)"
    title_w, title_h = get_text_size(title_text, title_font)
    title_x = (width - title_w) // 2
    current_y = 20
    draw.text((title_x, current_y), title_text, font=title_font, fill=colors['primary_dark'])
    current_y += title_h + 15

    # 用户信息卡片（带头像）
    card_height = 105
    user_card_margin = 30
    await draw_user_card_bg(image, draw, user_id, data_dir,
                            (user_card_margin, current_y, width - user_card_margin, current_y + card_height),
                            10, fallback_fill=colors['card_bg'])

    col1_x = user_card_margin + 20
    avatar_size = 50
    row1_y = current_y + 15

    if user_id and data_dir:
        if avatar_image := await get_user_avatar(user_id, data_dir, avatar_size):
            image.paste(avatar_image, (col1_x, row1_y), avatar_image)
            col1_x += avatar_size + 15

    draw.text((col1_x, row1_y), nickname, font=subtitle_font, fill=colors['primary_medium'])
    current_y += card_height + 15

    if not items:
        draw.text((30, current_y), "📦 您还没有道具。", font=content_font, fill=colors['text_muted'])
        current_y += 50
        image, draw, height = _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, colors['text_secondary'], _ITEM_HINTS)
        return image

    # 道具卡片
    card_width = (width - 90) // 2
    card_margin = 15
    row_start_y = current_y
    next_row_start_y = current_y

    for i, item in enumerate(items):
        row = i // 2
        col = i % 2
        x = 30 + col * (card_width + card_margin)

        if col == 0:
            row_start_y = next_row_start_y
            left_h = _measure_item_card_height(item, card_width, tiny_font, wrap_text_by_width, get_text_size)
            right_index = i + 1
            right_h = _measure_item_card_height(items[right_index], card_width, tiny_font, wrap_text_by_width, get_text_size) if right_index < len(items) else 0
            row_h = max(left_h, right_h)
            y = row_start_y
            next_row_start_y = row_start_y + row_h + card_margin
            card_h = row_h
        else:
            y = row_start_y
            card_h = row_h
        ensure_height(y + card_h + 40)

        draw_rounded_rectangle(draw, (x, y, x + card_width, y + card_h), 6, fill=colors['card_bg'])

        # 名称和ID
        item_name = item['name'][:12] + "..." if len(item['name']) > 12 else item['name']
        name_w, _ = get_text_size(item_name, small_font)
        draw.text((x + 15, y + 10), item_name, font=small_font, fill=colors['text_primary'])
        item_id = int(item.get('item_id', 0) or 0)
        dcode = f"D{item_id}" if item_id else "D0"
        draw.text((x + 15 + name_w + 10, y + 12), f"ID: {dcode}", font=tiny_font, fill=colors['primary_light'])

        # 消耗品标识
        label_text = "消耗" if item.get('is_consumable') else "非消耗"
        lw, lh = get_text_size(label_text, tiny_font)
        draw.text((x + card_width - 15 - lw, y + 12), label_text, font=tiny_font,
                  fill=colors['success_color'] if item.get('is_consumable') else colors['text_muted'])

        # 稀有度
        rarity = item.get('rarity', 1)
        star_color = colors['rare_color'] if rarity > 4 else colors['warning_color'] if rarity >= 3 else colors['text_secondary']
        draw_text_with_stars(image, draw, (x + 15, y + 30), format_rarity_display(rarity),
                             font=tiny_font, fill=star_color, star_size=16)

        # 数量
        quantity = item.get('quantity', 0)
        draw.text((x + 15, y + 50), f"数量: {quantity}", font=tiny_font, fill=colors['text_secondary'])

        # 效果描述
        next_y = y + 70
        if effect_desc := item.get('effect_description'):
            available_width = card_width - 30
            lines = wrap_text_by_width(f"效果: {effect_desc}", tiny_font, available_width)
            line_h = get_text_size("测", tiny_font)[1] + 2
            max_lines = max((y + card_h - 15) - next_y, 0) // line_h
            if max_lines > 0:
                for li, line in enumerate(lines[:max_lines]):
                    draw.text((x + 15, next_y + li * line_h), line, font=tiny_font, fill=colors['text_secondary'])

    current_y = next_row_start_y + 15

    image, draw, height = _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, colors['text_secondary'], _ITEM_HINTS)
    return image


def _measure_item_card_height(item, card_width, tiny_font, wrap_fn, get_text_size_fn):
    """测量道具卡片高度"""
    line_h = get_text_size_fn("测", tiny_font)[1] + 2
    desc_lines = 0
    if item.get('effect_description'):
        desc_lines = len(wrap_fn(f"效果: {item['effect_description']}", tiny_font, card_width - 30))
    header_height = 70
    bottom_pad = 15 if desc_lines > 0 else 10
    return header_height + desc_lines * line_h + bottom_pad


# ========== 指令提示 ==========

_ROD_HINTS = [
    "💡 装备：/使用+ID（如 /使用 R2N9C）",
    "💡 出售：/出售+ID  |  /出售所有鱼竿",
    "💡 精炼：/精炼鱼竿+ID",
]

_ACCESSORY_HINTS = [
    "💡 装备：/使用+ID（如 /使用 A7K3Q）",
    "💡 出售：/出售+ID  |  /出售所有饰品",
    "💡 精炼：/精炼饰品+ID",
]

_ITEM_HINTS = [
    "💡 使用：/使用+ID（支持数量，如 /使用 D1 5）",
    "💡 出售：/出售+ID [数量]",
]


# ========== 公共工具 ==========

def _finalize_image(image, draw, height, current_y, width, bg_top, bg_bot, small_font, text_secondary, hints=None):
    """完成图片：绘制指令提示、底部信息和装饰"""
    from .gradient_utils import create_vertical_gradient

    # 绘制指令提示（参考商店底部）
    if hints:
        for hint_line in hints:
            hw, hh = draw.textbbox((0, 0), hint_line, font=small_font)[2:4]
            hx = (width - hw) // 2
            draw.text((hx, current_y), hint_line, font=small_font, fill=text_secondary)
            current_y += hh + 4
        current_y += 6

    # 生成时间
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer_w, footer_h = draw.textbbox((0, 0), footer_text, font=small_font)[2:4]
    footer_x = (width - footer_w) // 2
    needed_height = current_y + footer_h + 30
    if needed_height > height:
        new_image = Image.new('RGB', (width, needed_height), (255, 255, 255))
        bg = create_vertical_gradient(width, needed_height, bg_top, bg_bot)
        new_image.paste(bg, (0, 0))
        new_image.paste(image, (0, 0))
        image = new_image
        draw = ImageDraw.Draw(image)
        height = needed_height
    draw.text((footer_x, current_y), footer_text, font=small_font, fill=text_secondary)
    _draw_corner_decorations(draw, width, height)
    return image, draw, height


def _create_fallback_image(category: str, total_count: int) -> Image.Image:
    """创建简化的回退图像"""
    width, height = 800, 400
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    title_font = load_font(28)
    content_font = load_font(18)
    small_font = load_font(16)
    primary_dark = (52, 73, 94)
    text_secondary = (120, 144, 156)
    warning_orange = (255, 165, 0)

    draw.text((50, 30), f"{category}列表", font=title_font, fill=primary_dark)
    draw.text((50, 100), f"共 {total_count} 个{category}", font=content_font, fill=primary_dark)
    draw.text((50, 150), "⚠️ 图片生成超时！", font=content_font, fill=warning_orange)
    draw.text((50, 200), "💡 建议稍后再试或使用背包命令查看", font=small_font, fill=text_secondary)
    footer_text = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((50, height - 50), footer_text, font=small_font, fill=text_secondary)
    return image
