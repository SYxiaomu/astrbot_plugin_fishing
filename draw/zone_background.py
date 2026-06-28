"""
区域背景图生成器
为每个钓鱼区域生成渐变色背景图，包含区域名称和气候类型信息。
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Optional


# 区域背景配置：渐变色和文字信息
ZONE_BG_CONFIG = {
    1: {
        "name": "热带雨林溪流",
        "climate": "高温多雨 · 物种极其丰富",
        "colors": ("#1a5c1a", "#4caf50"),  # 绿色系渐变
    },
    2: {
        "name": "亚热带河口湿地",
        "climate": "温暖湿润 · 咸淡水交汇",
        "colors": ("#006064", "#4dd0e1"),  # 蓝绿渐变
    },
    3: {
        "name": "温带平原湖泊",
        "climate": "四季分明 · 水域广阔",
        "colors": ("#1565c0", "#64b5f6"),  # 蓝色渐变
    },
    4: {
        "name": "寒带针叶林河流",
        "climate": "寒冷漫长 · 水质清澈",
        "colors": ("#1a237e", "#5c6bc0"),  # 冷蓝渐变
    },
    5: {
        "name": "干旱区内陆盐湖",
        "climate": "干旱少雨 · 高盐碱度",
        "colors": ("#bf8f00", "#ffd54f"),  # 黄褐渐变
    },
    6: {
        "name": "近岸浅湾",
        "climate": "风平浪静 · 阳光充足",
        "colors": ("#0277bd", "#81d4fa"),  # 浅蓝渐变
    },
    7: {
        "name": "大陆架渔场",
        "climate": "营养丰富 · 鱼群密集",
        "colors": ("#0d47a1", "#42a5f5"),  # 深海蓝渐变
    },
    8: {
        "name": "寒带峡湾",
        "climate": "冰川侵蚀 · 深邃宁静",
        "colors": ("#b0bec5", "#eceff1"),  # 冷白渐变
    },
    9: {
        "name": "远洋海岭",
        "climate": "深海孤寂 · 巨型鱼类出没",
        "colors": ("#1a237e", "#283593"),  # 深蓝渐变
    },
    10: {
        "name": "极地冰缘海",
        "climate": "极寒刺骨 · 浮冰遍布",
        "colors": ("#e0e0e0", "#ffffff"),  # 白蓝渐变
    },
}


def hex_to_rgb(hex_color: str) -> tuple:
    """将十六进制颜色转换为RGB元组"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def create_vertical_gradient(width: int, height: int, top_color: tuple, bottom_color: tuple) -> Image.Image:
    """创建垂直渐变图像"""
    image = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    return image


def generate_zone_background(
    zone_id: int,
    output_dir: str,
    width: int = 800,
    height: int = 400,
    font_path: Optional[str] = None,
) -> str:
    """生成指定区域的背景图

    Args:
        zone_id: 区域ID (1-10)
        output_dir: 输出目录
        width: 图片宽度
        height: 图片高度
        font_path: 字体文件路径，为None则使用默认字体

    Returns:
        生成的图片文件路径
    """
    config = ZONE_BG_CONFIG.get(zone_id)
    if not config:
        raise ValueError(f"未知区域ID: {zone_id}")

    os.makedirs(output_dir, exist_ok=True)

    # 创建渐变背景
    top_color = hex_to_rgb(config["colors"][0])
    bottom_color = hex_to_rgb(config["colors"][1])
    image = create_vertical_gradient(width, height, top_color, bottom_color)
    draw = ImageDraw.Draw(image)

    # 加载字体
    title_font_size = 48
    subtitle_font_size = 24
    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, title_font_size)
            subtitle_font = ImageFont.truetype(font_path, subtitle_font_size)
        else:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    # 计算文字颜色（基于背景亮度）
    avg_brightness = (top_color[0] * 0.299 + top_color[1] * 0.587 + top_color[2] * 0.114 +
                      bottom_color[0] * 0.299 + bottom_color[1] * 0.587 + bottom_color[2] * 0.114) / 2
    text_color = (20, 20, 20) if avg_brightness > 128 else (240, 240, 240)

    # 绘制半透明遮罩层增强文字可读性
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 60))
    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    # 绘制区域名称
    zone_name = f"区域{zone_id}：{config['name']}"
    try:
        bbox = draw.textbbox((0, 0), zone_name, font=title_font)
        text_w = bbox[2] - bbox[0]
    except Exception:
        text_w = len(zone_name) * title_font_size
    text_x = (width - text_w) // 2
    text_y = height // 2 - 60
    draw.text((text_x, text_y), zone_name, font=title_font, fill=text_color)

    # 绘制气候信息
    climate = config["climate"]
    try:
        bbox = draw.textbbox((0, 0), climate, font=subtitle_font)
        clim_w = bbox[2] - bbox[0]
    except Exception:
        clim_w = len(climate) * subtitle_font_size
    clim_x = (width - clim_w) // 2
    clim_y = text_y + 80
    draw.text((clim_x, clim_y), climate, font=subtitle_font, fill=text_color)

    # 绘制区域标签
    zone_tag = f"zone_{zone_id}"
    try:
        bbox = draw.textbbox((0, 0), zone_tag, font=subtitle_font)
        tag_w = bbox[2] - bbox[0]
    except Exception:
        tag_w = len(zone_tag) * subtitle_font_size
    tag_x = (width - tag_w) // 2
    tag_y = clim_y + 50
    draw.text((tag_x, tag_y), zone_tag, font=subtitle_font, fill=text_color)

    # 保存图片
    output_path = os.path.join(output_dir, f"zone_{zone_id}.png")
    image.save(output_path, "PNG")
    return output_path


def generate_all_zone_backgrounds(
    output_dir: str,
    width: int = 800,
    height: int = 400,
    font_path: Optional[str] = None,
) -> dict:
    """生成所有10个区域的背景图

    Args:
        output_dir: 输出目录
        width: 图片宽度
        height: 图片高度
        font_path: 字体文件路径

    Returns:
        区域ID到图片路径的映射字典
    """
    result = {}
    for zone_id in range(1, 11):
        try:
            path = generate_zone_background(zone_id, output_dir, width, height, font_path)
            result[zone_id] = path
            print(f"✅ 区域 {zone_id} 背景图已生成: {path}")
        except Exception as e:
            print(f"❌ 区域 {zone_id} 背景图生成失败: {e}")
    return result
