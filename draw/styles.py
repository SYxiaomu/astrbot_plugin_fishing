# draw/styles.py
import os
from PIL import Image, ImageFont, ImageDraw

# --- 基础配置 ---
IMG_WIDTH = 800
PADDING = 30
CORNER_RADIUS = 15

# --- 布局定义 ---
HEADER_HEIGHT = 100
USER_CARD_HEIGHT = 135
USER_CARD_MARGIN = 12

# --- 颜色定义 ---
# 基础颜色
COLOR_BACKGROUND = (245, 245, 245)
COLOR_HEADER_BG = (51, 153, 255)
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_DARK = (50, 50, 50)
COLOR_TEXT_GRAY = (120, 120, 140)
COLOR_CARD_BG = (255, 255, 255)
COLOR_CARD_BORDER = (230, 230, 230)
COLOR_ACCENT = (0, 180, 255)

# 状态颜色
COLOR_SUCCESS = (76, 175, 80)      # 温和绿 - 成功/积极状态
COLOR_WARNING = (255, 183, 77)     # 柔和橙 - 警告/中性
COLOR_ERROR = (229, 115, 115)      # 温和红 - 错误/消极状态
COLOR_LOCK = (54, 162, 235)        # 安全蓝 - 锁定保护状态

# 特殊颜色
COLOR_GOLD = (240, 173, 78)        # 温和金色 - 金币
COLOR_RARE = (149, 117, 205)       # 柔和紫色 - 稀有物品

# 排行榜颜色
COLOR_TEXT_GOLD = (255, 215, 0)    # 金色（用于第一名）
COLOR_TEXT_SILVER = (192, 192, 192)  # 银色（用于第二名）
COLOR_TEXT_BRONZE = (205, 127, 50)   # 铜色（用于第三名）
COLOR_FISH_COUNT = (46, 139, 87)     # 鱼数量颜色
COLOR_COINS = (218, 165, 32)         # 金币颜色

# 精炼等级颜色
COLOR_REFINE_RED = (255, 0, 0)     # 红色 - 10级
COLOR_REFINE_ORANGE = (244, 50, 156)  # 粉色 - 6-9级

# 稀有度颜色映射
COLOR_RARITY_MAP = {
    1: (176, 196, 222),  # 1星 钢蓝色
    2: (100, 149, 237),  # 2星 矢车菊蓝
    3: (147, 112, 219),  # 3星 中紫罗兰红
    4: (218, 112, 214),  # 4星 兰花紫
    5: (255, 165, 0),    # 5星 橙色
    6: (255, 69, 0),     # 6星 红橙色
    7: (220, 20, 60),    # 7星 深红色
    8: (178, 34, 34),    # 8星 火砖红
    9: (139, 0, 0),      # 9星 暗红色
    10: (128, 0, 0),     # 10星 栗色
}

# 帮助页面颜色
COLOR_TITLE = (30, 80, 162)        # 标题颜色
COLOR_CMD = (40, 40, 40)           # 命令颜色
COLOR_LINE = (200, 200, 200)       # 分割线颜色
COLOR_SHADOW = (0, 0, 0, 80)       # 阴影颜色

# 装饰颜色
COLOR_CORNER = (255, 255, 255, 80) # 四角装饰颜色

# --- 字体路径 ---
FONT_PATH_BOLD = os.path.join(os.path.dirname(__file__), "resource", "DouyinSansBold.otf")
# Emoji 回退字体（Windows 系统）
EMOJI_FONT_PATH = "C:/Windows/Fonts/seguiemj.ttf"
# ★☆ 专用回退字体（Segoe UI Emoji 不包含 ★☆，用 Segoe UI Symbol）
STAR_FONT_PATH = "C:/Windows/Fonts/seguisym.ttf"

# --- emoji 回退字体缓存 ---
_emoji_font_cache = {}
_star_font_cache = {}

def _get_emoji_font(size: int, for_star: bool = False):
    """获取对应大小的 emoji 字体（带缓存）
    
    Args:
        size: 字体大小
        for_star: 是否为 ★☆ 字符（Segoe UI Emoji 不包含，需要用 Segoe UI Symbol）
    """
    if for_star:
        # ★☆ 专用缓存（独立字典，不与 emoji 缓存冲突）
        if size not in _star_font_cache:
            try:
                _star_font_cache[size] = ImageFont.truetype(STAR_FONT_PATH, size)
            except Exception:
                _star_font_cache[size] = None
        return _star_font_cache[size]
    
    if size not in _emoji_font_cache:
        try:
            _emoji_font_cache[size] = ImageFont.truetype(EMOJI_FONT_PATH, size)
        except Exception:
            _emoji_font_cache[size] = None
    return _emoji_font_cache[size]

# --- 字体加载 ---
def load_font(size):
    """加载主字体"""
    try:
        return ImageFont.truetype(FONT_PATH_BOLD, size)
    except IOError:
        return ImageFont.load_default()


def load_font_with_emoji_fallback(size):
    """加载字体（带 emoji 回退支持）
    
    由于 styles.py 已全局替换 ImageDraw.text 为 _emoji_aware_draw_text，
    emoji 回退由绘图层自动处理，此函数等价于 load_font()。
    提供此函数仅为保持语义清晰的 API 接口。
    """
    return load_font(size)

FONT_HEADER = load_font(36)    # 标题字体
FONT_SUBHEADER = load_font(24) # 收集进度字体
FONT_FISH_NAME = load_font(24) # 鱼名字体
FONT_REGULAR = load_font(14)   # 常规字体
FONT_SMALL = load_font(12)     # 小字体

# --- 通用稀有度显示字符串 ---
# 使用图片渲染 ★，保证显示成功率
# 注意：此处不导入，避免循环依赖，在需要的地方直接使用

def format_rarity_display(rarity: int) -> str:
    """
    格式化稀有度显示（返回包含★的文本）
    注意：在绘图时需要使用 draw_text_with_stars() 来正确渲染
    """
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★' * 10 + "+"

# ============================================================
# 全局 emoji 渲染修复
# ============================================================
# 问题：DouyinSansBold 字体不包含 emoji 字形，导致 🎣💰🐟 等 emoji 显示为空白/方框。
# 解决方法：替换 ImageDraw.Draw.text 方法，使所有绘图模块自动使用字符级渲染，
# 中文用 DouyinSansBold，emoji 用 Segoe UI Emoji。
# 此修改全局生效，无需改动任何绘图模块。

# 保存原始 draw.text 方法
_original_draw_text = ImageDraw.ImageDraw.text

def _is_emoji_char(char: str) -> bool:
    """判断字符是否需要用 emoji 字体回退"""
    code = ord(char)
    # 完整 emoji 范围
    if 0x1F300 <= code <= 0x1F9FF or 0xFE00 <= code <= 0xFE0F:
        return True
    # ★☆ (U+2605/U+2606) DouyinSansBold 不包含，需要回退到 emoji 字体
    if code in (0x2605, 0x2606):
        return True
    # ⭐ (U+2B50) 白五星，DouyinSansBold 不包含
    if code == 0x2B50:
        return True
    # ✨ (U+2728) DouyinSansBold 不包含，需要回退到 emoji 字体
    if code == 0x2728:
        return True
    # ◆ (U+25C6) ◇ (U+25C7) ◈ (U+25C8) DouyinSansBold 不包含，需要回退到 emoji 字体
    if code in (0x25C6, 0x25C7, 0x25C8):
        return True
    return False

def _has_emoji(text: str) -> bool:
    """检查文本中是否包含 emoji 字符"""
    if not text:
        return False
    for char in text:
        if _is_emoji_char(char):
            return True
    return False

def _emoji_aware_draw_text(self, xy, text, fill=None, font=None, *args, **kwargs):
    """
    智能文本绘制，自动处理 emoji 回退。
    
    如果文本包含 emoji 且有 emoji 字体可用，会逐字符渲染
    （中文用 DouyinSansBold，emoji 用 Segoe UI Emoji）；
    否则使用原始 draw.text() 方法。
    """
    if font is None or not _has_emoji(text):
        _original_draw_text(self, xy, text, fill=fill, font=font, *args, **kwargs)
        return

    # 获取对应大小的 emoji 字体（★☆ 需要特殊处理）
    emoji_font = _get_emoji_font(font.size)
    if emoji_font is None:
        _original_draw_text(self, xy, text, fill=fill, font=font, *args, **kwargs)
        return

    # 检查是否全是 emoji
    has_non_emoji = False
    for char in text:
        if not _is_emoji_char(char):
            has_non_emoji = True
            break

    if not has_non_emoji:
        _original_draw_text(self, xy, text, fill=fill, font=emoji_font, *args, **kwargs)
        return

    # 混合文本（中文+emoji），需要逐字符渲染
    x, y = xy
    current_x = x

    temp_img = Image.new('RGB', (1, 1), (255, 255, 255))
    temp_draw = ImageDraw.Draw(temp_img)

    try:
        ref_bbox = temp_draw.textbbox((0, 0), "A", font=font)
    except:
        ref_bbox = (0, 0, font.size, font.size)
    ref_center_y = (ref_bbox[1] + ref_bbox[3]) / 2

    for char in text:
        is_emoji = _is_emoji_char(char)
        # ★☆ 使用专用字体
        if is_emoji and ord(char) in (0x2605, 0x2606):
            char_font = _get_emoji_font(font.size, for_star=True)
            if char_font is None:
                char_font = emoji_font
        else:
            char_font = emoji_font if is_emoji else font

        try:
            char_bbox = temp_draw.textbbox((0, 0), char, font=char_font)
            char_w = char_bbox[2] - char_bbox[0]
            char_center_y = (char_bbox[1] + char_bbox[3]) / 2
        except:
            char_w = font.size
            char_center_y = font.size / 2

        char_y = y + (ref_center_y - char_center_y)

        try:
            _original_draw_text(self, (current_x, char_y), char, fill=fill, font=char_font)
        except:
            pass

        current_x += char_w

# 全局替换：所有 ImageDraw.Draw.text 调用都会自动处理 emoji
ImageDraw.ImageDraw.text = _emoji_aware_draw_text