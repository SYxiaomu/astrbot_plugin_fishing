"""
擦弹游戏图片生成模块
用于生成擦弹游戏相关的各种图片消息
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_GOLD,
    COLOR_TEXT_DARK, COLOR_TEXT_WHITE, COLOR_CARD_BG,
    load_font
)


def draw_wipe_bomb_result(
    contribution: int,
    multiplier: float,
    reward: int,
    profit: int,
    remaining_today: int,
    suppression_notice: str = ""
) -> Image.Image:
    """绘制擦弹结果图片"""
    width, height = 800, 400
    
    # 根据结果决定背景色
    if multiplier >= 3:
        # 大成功 - 金色渐变
        bg_top = (255, 223, 150)
        bg_bot = (255, 245, 210)
    elif multiplier >= 1:
        # 普通成功 - 浅蓝色（标准背景）
        bg_top = (174, 214, 241)
        bg_bot = (245, 251, 255)
    else:
        # 亏损 - 浅红色
        bg_top = (255, 190, 180)
        bg_bot = (255, 240, 240)
    
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(20)
    
    # 绘制标题
    if multiplier >= 3:
        title_text = "大成功！"
    elif multiplier >= 1:
        title_text = "擦弹结果"
    else:
        title_text = "擦弹失败"
    
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 40), title_text, fill=COLOR_TEXT_DARK, font=title_font)
    
    # 绘制倍率信息
    if multiplier < 0.01:
        multiplier_formatted = f"{multiplier:.4f}"
    else:
        multiplier_formatted = f"{multiplier:.2f}"
    
    result_text = f"获得 {multiplier_formatted} 倍奖励"
    result_bbox = draw.textbbox((0, 0), result_text, font=subtitle_font)
    result_width = result_bbox[2] - result_bbox[0]
    result_x = (width - result_width) // 2
    draw.text((result_x, 95), result_text, fill=COLOR_GOLD, font=subtitle_font)
    
    # 绘制详细信息
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
    
    y_start = 155
    line_height = 32
    for line in detail_lines:
        if not line.strip():
            y_start += 10
            continue
        line_bbox = draw.textbbox((0, 0), line, font=content_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        draw.text((line_x, y_start), line, fill=COLOR_TEXT_DARK, font=content_font)
        y_start += line_height
    
    return image


def draw_wipe_bomb_history(history: List[Dict[str, Any]]) -> Image.Image:
    """绘制擦弹记录图片"""
    # 根据记录数量动态调整高度
    line_height = 26
    record_height = line_height * 4 + 15  # 每条记录4行 + 间隔
    base_height = 120
    height = base_height + len(history) * record_height
    width = 800
    
    # 使用标准钓鱼插件背景色
    bg_top = (174, 214, 241)
    bg_bot = (245, 251, 255)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    title_font = load_font(32)
    subtitle_font = load_font(20)
    content_font = load_font(18)
    
    # 绘制标题
    title_text = "擦弹记录"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 30), title_text, fill=COLOR_TEXT_DARK, font=title_font)
    
    # 绘制分割线
    draw.line([(60, 80), (width - 60, 80)], fill=(180, 200, 220), width=2)
    
    # 绘制记录
    y_start = 95
    for record in history:
        # 时间
        time_text = f"时间: {record['timestamp']}"
        draw.text((80, y_start), time_text, fill=COLOR_TEXT_DARK, font=content_font)
        y_start += line_height
        
        # 投入和奖励
        amount_text = f"投入: {record['contribution']} 金币  |  奖励: {record['reward']} 金币"
        draw.text((80, y_start), amount_text, fill=COLOR_TEXT_DARK, font=content_font)
        y_start += line_height
        
        # 计算盈亏
        profit = record["reward"] - record["contribution"]
        if profit >= 0:
            profit_text = f"盈利: +{profit}"
        else:
            profit_text = f"亏损: {profit}"
        
        multiplier_val = record["multiplier"]
        rate_text = f"倍率: {multiplier_val}  ({profit_text})"
        
        # 根据盈亏选择颜色
        if profit >= 0:
            profit_color = COLOR_SUCCESS
        else:
            profit_color = COLOR_ERROR
        
        draw.text((80, y_start), rate_text, fill=profit_color, font=content_font)
        y_start += line_height
        
        # 分割线
        draw.line([(80, y_start), (width - 80, y_start)], fill=(210, 220, 230), width=1)
        y_start += 15
    
    return image


def draw_wipe_bomb_error(message: str) -> Image.Image:
    """绘制擦弹错误/提示图片"""
    width, height = 800, 200
    
    bg_top = (255, 190, 180)
    bg_bot = (255, 240, 240)
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    title_font = load_font(28)
    content_font = load_font(20)
    
    # 绘制标题
    title_text = "擦弹失败"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 40), title_text, fill=COLOR_ERROR, font=title_font)
    
    # 绘制错误信息
    msg_bbox = draw.textbbox((0, 0), message, font=content_font)
    msg_width = msg_bbox[2] - msg_bbox[0]
    msg_x = (width - msg_width) // 2
    draw.text((msg_x, 100), message, fill=COLOR_TEXT_DARK, font=content_font)
    
    return image


def save_image_to_temp(image: Image.Image, prefix: str, data_dir: str) -> str:
    """保存图片到临时目录并返回路径"""
    import tempfile
    
    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)
    
    image.save(temp_path, format='PNG')
    
    return temp_path
