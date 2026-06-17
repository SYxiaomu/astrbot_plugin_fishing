"""
文本处理工具函数
优化文本测量、换行和渲染性能
"""
import os
import platform
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Optional


def get_text_size_cached(text: str, font: ImageFont.FreeTypeFont, cache: dict = None) -> Tuple[int, int]:
    """
    带缓存的文本尺寸测量，避免重复计算
    
    Args:
        text: 要测量的文本
        font: 字体对象
        cache: 可选的缓存字典
    
    Returns:
        (width, height): 文本尺寸
    """
    if cache is None:
        # 如果没有提供缓存，直接测量
        return _measure_text_size(text, font)
    
    # 使用缓存
    cache_key = f"{text}_{font.size}"
    if cache_key not in cache:
        cache[cache_key] = _measure_text_size(text, font)
    
    return cache[cache_key]


def _measure_text_size(text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    """
    测量文本尺寸的内部函数
    """
    # 创建临时图像进行测量
    temp_img = Image.new('RGB', (1, 1), (255, 255, 255))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text_by_width_optimized(text: str, font: ImageFont.FreeTypeFont, max_width: int, cache: dict = None) -> List[str]:
    """
    优化的文本按宽度换行函数
    
    Args:
        text: 要换行的文本
        font: 字体对象
        max_width: 最大宽度
        cache: 可选的缓存字典
    
    Returns:
        List[str]: 换行后的文本行列表
    """
    if not text:
        return []
    
    # 如果文本很短，直接返回
    text_width, _ = get_text_size_cached(text, font, cache)
    if text_width <= max_width:
        return [text]
    
    lines = []
    current_line = ""
    
    # 按字符分割，但优化测量频率
    for char in text:
        test_line = current_line + char
        test_width, _ = get_text_size_cached(test_line, font, cache)
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    
    if current_line:
        lines.append(current_line)
    
    return lines


def wrap_text_by_width_with_hyphenation(text: str, font: ImageFont.FreeTypeFont, max_width: int, cache: dict = None) -> List[str]:
    """
    带连字符的文本换行，适用于英文文本
    
    Args:
        text: 要换行的文本
        font: 字体对象
        max_width: 最大宽度
        cache: 可选的缓存字典
    
    Returns:
        List[str]: 换行后的文本行列表
    """
    if not text:
        return []
    
    # 先尝试简单换行
    lines = wrap_text_by_width_optimized(text, font, max_width, cache)
    
    # 如果只有一行，直接返回
    if len(lines) <= 1:
        return lines
    
    # 对每行进行连字符优化
    optimized_lines = []
    for line in lines:
        if len(line) > 10 and ' ' in line:  # 只对较长的行进行连字符处理
            words = line.split(' ')
            if len(words) > 1:
                # 尝试在单词边界换行
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    test_width, _ = get_text_size_cached(test_line, font, cache)
                    
                    if test_width <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            optimized_lines.append(current_line)
                        current_line = word
                
                if current_line:
                    optimized_lines.append(current_line)
            else:
                optimized_lines.append(line)
        else:
            optimized_lines.append(line)
    
    return optimized_lines


def create_text_cache() -> dict:
    """
    创建文本测量缓存
    
    Returns:
        dict: 空的缓存字典
    """
    return {}


def clear_text_cache(cache: dict) -> None:
    """
    清空文本测量缓存
    
    Args:
        cache: 要清空的缓存字典
    """
    cache.clear()


def get_text_metrics_batch(texts: List[str], font: ImageFont.FreeTypeFont, cache: dict = None) -> List[Tuple[int, int]]:
    """
    批量测量文本尺寸，提高效率
    
    Args:
        texts: 文本列表
        font: 字体对象
        cache: 可选的缓存字典
    
    Returns:
        List[Tuple[int, int]]: 每个文本的尺寸列表
    """
    if cache is None:
        return [_measure_text_size(text, font) for text in texts]
    
    results = []
    for text in texts:
        results.append(get_text_size_cached(text, font, cache))
    
    return results


def _find_cjk_font() -> Optional[str]:
    """
    查找CJK字体路径（支持繁体中文字符）
    
    Returns:
        字体文件路径，如果找不到则返回None
    """
    resource_dir = os.path.join(os.path.dirname(__file__), "resource")
    
    # 使用项目资源目录中的字体（按优先级排序）
    cjk_fonts = [
        "NotoSansTC-Bold.ttf",  # Noto Sans 繁体中文（优先）
        "NotoSansJP-Bold.ttf",  # Noto Sans 日文（后备）
    ]
    
    for font_name in cjk_fonts:
        font_path = os.path.join(resource_dir, font_name)
        if os.path.exists(font_path):
            return font_path
    
    return None


class FontWithFallback:
    """
    带自动回退的字体包装类
    当主字体不支持某个字符时，自动使用系统CJK字体或emoji字体
    
    策略：
    - 中文字符 → 优先使用 DouyinSansBold
    - Emoji 符号 → 优先使用 Segoe UI Emoji
    - 其他字符 → 主字体
    """
    def __init__(self, primary_font: ImageFont.FreeTypeFont, fallback_font: Optional[ImageFont.FreeTypeFont] = None, emoji_font: Optional[ImageFont.FreeTypeFont] = None):
        self.primary_font = primary_font
        self.fallback_font = fallback_font
        self.emoji_font = emoji_font
        self._char_cache = {}  # 缓存字符到字体的映射
    
    def _is_cjk_char(self, char: str) -> bool:
        """判断是否为CJK字符（中文、日文、韩文）"""
        if not char:
            return False
        code = ord(char)
        # CJK统一汉字、CJK扩展A/B/C/D/E、CJK兼容汉字、日文平假名/片假名、韩文等
        return (
            0x4E00 <= code <= 0x9FFF or  # CJK统一汉字
            0x3400 <= code <= 0x4DBF or  # CJK扩展A
            0x20000 <= code <= 0x2A6DF or  # CJK扩展B
            0x2A700 <= code <= 0x2B73F or  # CJK扩展C
            0x2B740 <= code <= 0x2B81F or  # CJK扩展D
            0x2B820 <= code <= 0x2CEAF or  # CJK扩展E
            0xF900 <= code <= 0xFAFF or  # CJK兼容汉字
            0x3040 <= code <= 0x309F or  # 日文平假名
            0x30A0 <= code <= 0x30FF or  # 日文片假名
            0xAC00 <= code <= 0xD7AF     # 韩文音节
        )
    
    def _is_emoji_char(self, char: str) -> bool:
        """判断是否为 emoji 字符"""
        if not char:
            return False
        code = ord(char)
        # 常见的 emoji Unicode 范围
        return (
            0x1F300 <= code <= 0x1F9FF or  # Miscellaneous Symbols and Pictographs, Emoticons, etc.
            0x2600 <= code <= 0x26FF or    # Miscellaneous Symbols
            0x2700 <= code <= 0x27BF or    # Dingbats
            0xFE0F == code                 # Variation Selector-16 (emoji presentation)
        )
    
    def _get_font_for_char(self, char: str) -> ImageFont.FreeTypeFont:
        """
        选择字符的渲染字体
        
        策略：
        1. Emoji → 使用 emoji_font（如果有）
        2. CJK → 使用 fallback_font（如果有）或 primary_font
        3. 其他 → 优先使用 primary_font，不支持则回退
        """
        if char in self._char_cache:
            return self._char_cache[char]
        
        # 1. 检查是否为 emoji
        if self._is_emoji_char(char):
            if self.emoji_font:
                try:
                    mask = self.emoji_font.getmask(char)
                    if mask.size[0] > 0 and mask.size[1] > 0:
                        self._char_cache[char] = self.emoji_font
                        return self.emoji_font
                except Exception:
                    pass
        
        # 2. 检查是否为 CJK 字符
        if self._is_cjk_char(char):
            # CJK 字符优先使用主字体（DouyinSansBold）
            try:
                mask = self.primary_font.getmask(char)
                if mask.size[0] > 0 and mask.size[1] > 0:
                    bbox = mask.getbbox()
                    if bbox is None or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                        raise ValueError("Invalid bbox")
                    self._char_cache[char] = self.primary_font
                    return self.primary_font
            except Exception:
                pass
            
            # 主字体不支持，尝试回退字体
            if self.fallback_font:
                try:
                    mask = self.fallback_font.getmask(char)
                    if mask.size[0] > 0 and mask.size[1] > 0:
                        self._char_cache[char] = self.fallback_font
                        return self.fallback_font
                except Exception:
                    pass
        
        # 3. 其他字符，优先使用主字体
        try:
            mask = self.primary_font.getmask(char)
            if mask.size[0] > 0 and mask.size[1] > 0:
                self._char_cache[char] = self.primary_font
                return self.primary_font
        except Exception:
            pass
        
        # 4. 最后回退到 fallback_font
        if self.fallback_font:
            try:
                mask = self.fallback_font.getmask(char)
                if mask.size[0] > 0 and mask.size[1] > 0:
                    self._char_cache[char] = self.fallback_font
                    return self.fallback_font
            except Exception:
                pass
        
        # 5. 实在不行就用主字体（可能会显示方框）
        self._char_cache[char] = self.primary_font
        return self.primary_font
    
    def getmask(self, text, mode="", *args, **kwargs):
        """
        获取文本的mask，自动处理回退
        
        对于包含多种字符类型的文本，使用主字体作为基础
        PIL 会自动处理每个字符的渲染
        """
        # 如果有 emoji_font，且文本中包含 emoji，尝试使用 emoji_font
        if self.emoji_font and any(self._is_emoji_char(c) for c in text):
            try:
                return self.emoji_font.getmask(text, mode, *args, **kwargs)
            except Exception:
                pass
        
        # 默认使用主字体
        try:
            return self.primary_font.getmask(text, mode, *args, **kwargs)
        except Exception:
            if self.fallback_font:
                try:
                    return self.fallback_font.getmask(text, mode, *args, **kwargs)
                except Exception:
                    pass
            raise
    
    def getbbox(self, text, *args, **kwargs):
        """获取文本边界框"""
        return self.primary_font.getbbox(text, *args, **kwargs)
    
    def __getattr__(self, name):
        """代理其他属性到主字体"""
        return getattr(self.primary_font, name)


def load_font_with_cjk_fallback(font_path: str, size: int) -> FontWithFallback:
    """
    加载字体，自动添加CJK回退支持
    
    Args:
        font_path: 主字体文件路径
        size: 字体大小
    
    Returns:
        FontWithFallback: 带回退的字体对象
    """
    # 加载主字体
    try:
        primary_font = ImageFont.truetype(font_path, size)
    except Exception:
        primary_font = ImageFont.load_default()
    
    # 加载CJK字体作为回退（仅使用项目资源中的字体，不查询系统）
    fallback_font = None
    cjk_font_path = _find_cjk_font()
    if cjk_font_path:
        try:
            fallback_font = ImageFont.truetype(cjk_font_path, size)
        except Exception as e:
            # 如果加载失败，记录错误但不抛出异常
            pass
    
    return FontWithFallback(primary_font, fallback_font)


def draw_text_smart(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int] = (0, 0, 0)
) -> None:
    """
    智能文本绘制函数，自动处理字体回退
    
    如果传入的font是FontWithFallback类型，会自动使用回退字体处理缺失字符
    否则直接使用普通绘制
    
    Args:
        draw: ImageDraw对象
        position: 文本位置 (x, y)
        text: 要绘制的文本
        font: 字体对象（可以是FontWithFallback或普通字体）
        fill: 文本颜色
    """
    # 如果是FontWithFallback类型，需要特殊处理
    if isinstance(font, FontWithFallback):
        if not font.fallback_font:
            # 没有回退字体，直接绘制
            draw.text(position, text, font=font.primary_font, fill=fill)
            return
        
        # 检查是否所有字符都能用主字体渲染
        need_fallback = False
        for char in text:
            char_font = font._get_font_for_char(char)
            if char_font != font.primary_font:
                need_fallback = True
                break
        
        # 如果所有字符都能用主字体，直接一次性绘制（保持原始间距）
        if not need_fallback:
            draw.text(position, text, font=font.primary_font, fill=fill)
            return
        
        # 需要回退字体，逐个字符检查并绘制
        x, y = position
        current_x = x
        
        # 创建临时图像用于测量（复用以提高效率）
        temp_img = Image.new('RGB', (200, 100), (255, 255, 255))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 计算中线对齐：使用主字体的标准字符的垂直中心作为参考
        # 这确保无论使用哪个字体渲染，字符都在同一水平视觉中心线上
        # 使用"A"作为参考字符（标准拉丁字母大写，所有字体都支持）
        reference_bbox = temp_draw.textbbox((0, 0), "A", font=font.primary_font)
        reference_center_y = (reference_bbox[1] + reference_bbox[3]) / 2  # 垂直中心
        
        for i, char in enumerate(text):
            # 获取适合该字符的字体
            char_font = font._get_font_for_char(char)
            
            # 获取当前字符的bbox
            char_bbox = temp_draw.textbbox((0, 0), char, font=char_font)
            char_center_y = (char_bbox[1] + char_bbox[3]) / 2  # 当前字符的垂直中心
            
            # 计算y坐标：让所有字符的垂直中心对齐到参考中心
            # 基本思路：字符中心 = y + reference_center_y
            # 所以：char_y = y + (reference_center_y - char_center_y)
            char_y = y + (reference_center_y - char_center_y)
            
            # 测量字符宽度
            # 为了保持字符间距一致，统一使用主字体来测量宽度
            try:
                # 使用主字体测量宽度（保持一致的间距）
                if hasattr(font.primary_font, 'getlength'):
                    char_width = int(font.primary_font.getlength(char))
                else:
                    bbox = temp_draw.textbbox((0, 0), char, font=font.primary_font)
                    char_width = bbox[2] - bbox[0]
                    
                    # 如果主字体无法测量（宽度为0），使用实际字符字体测量
                    if char_width <= 0:
                        if hasattr(char_font, 'getlength'):
                            char_width = int(char_font.getlength(char))
                        else:
                            bbox = temp_draw.textbbox((0, 0), char, font=char_font)
                            char_width = bbox[2] - bbox[0]
                            if char_width <= 0:
                                char_width = font.primary_font.size
            except Exception:
                # 如果测量失败，使用字体大小估算
                char_width = font.primary_font.size
            
            # 绘制字符（使用调整后的y坐标，确保基线对齐）
            draw.text((current_x, char_y), char, font=char_font, fill=fill)
            current_x += char_width
    else:
        # 普通字体，直接绘制
        draw.text(position, text, font=font, fill=fill)
