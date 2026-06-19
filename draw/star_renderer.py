"""
星级渲染器 - 解决★和emoji同时渲染的问题
"""
import os
from PIL import Image, ImageDraw, ImageFont

# 星星图片路径
STAR_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "resource", "star.png")

# 缓存加载的星星图片
_star_image_cache = None

def get_star_image(size=32):
    """获取星星图片（带缓存和缩放）"""
    global _star_image_cache
    if _star_image_cache is None:
        if os.path.exists(STAR_IMAGE_PATH):
            _star_image_cache = Image.open(STAR_IMAGE_PATH)
        else:
            return None
    
    # 缩放图片
    if _star_image_cache.size[0] != size:
        return _star_image_cache.resize((size, size), Image.Resampling.LANCZOS)
    return _star_image_cache

def draw_text_with_stars(img, draw, xy, text, font, star_count=0, fill=(0, 0, 0), star_size=32):
    """
    绘制文本，其中★用图片渲染，其他文字正常渲染
    
    Args:
        img: Image对象（用于paste操作）
        draw: ImageDraw对象
        xy: 起始坐标 (x, y)
        text: 文本内容
        font: 字体
        star_count: 星星数量（如果text包含★字符，则自动计算）
        fill: 颜色
        star_size: 星星图片大小
    """
    x, y = xy
    
    # 计算星星数量
    if star_count == 0 and '★' in text:
        star_count = text.count('★')
    
    # 分割文本和星星
    parts = text.split('★')
    
    star_img = get_star_image(star_size)
    
    for i, part in enumerate(parts):
        # 绘制文本部分
        if part:
            draw.text((x, y), part, font=font, fill=fill)
            x += draw.textlength(part, font=font)
        
        # 绘制星星（除了最后一个部分后）
        if i < len(parts) - 1 and star_img:
            # 计算垂直对齐 - 使用基线对齐，稍微向下调整
            try:
                # 获取文本的bbox来计算基线位置
                bbox = draw.textbbox((0, 0), "A", font=font)
                text_height = bbox[3] - bbox[1]
                text_ascent = abs(bbox[1])  # 上升高度
                # 将星星底部与文本底部对齐
                y_offset = text_ascent - star_size
            except:
                # 回退方案：使用字体大小估算
                y_offset = font.size - star_size
            
            # 调整星星位置（往下移）
            y_offset += 15
            
            # 粘贴星星图片（支持RGBA）
            if star_img.mode == 'RGBA':
                img.paste(star_img, (int(x), int(y + y_offset)), star_img)
            else:
                img.paste(star_img, (int(x), int(y + y_offset)))
            
            x += star_size

def format_rarity_with_image(rarity: int, star_size=32) -> str:
    """
    返回稀有度文本（包含特殊标记）
    注意：这个函数返回的是纯文本，实际渲染需要用 draw_text_with_stars
    """
    if rarity <= 10:
        return '★' * rarity
    else:
        return '★' * 10 + '+'