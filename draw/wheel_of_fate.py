"""
命运之轮图片生成模块
用于生成命运之轮游戏相关的各种图片消息
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_GOLD,
    COLOR_TEXT_DARK, COLOR_TEXT_WHITE, COLOR_CARD_BG,
    load_font
)


def draw_wheel_of_fate_start(entry_fee: int, current_coins: int) -> Image.Image:
    """绘制命运之轮开始图片"""
    width, height = 800, 450
    
    # 使用钓鱼插件的标准背景色
    bg_top = (174, 214, 241)  # 浅蓝色
    bg_bot = (245, 251, 255)  # 更浅的蓝色
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    title_font = load_font(36)
    subtitle_font = load_font(24)
    content_font = load_font(20)
    
    # 绘制标题
    title_text = "命运之轮"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 50), title_text, fill=COLOR_TEXT_DARK, font=title_font)
    
    # 绘制入场费信息
    fee_text = f"入场费: {entry_fee:,} 金币"
    fee_bbox = draw.textbbox((0, 0), fee_text, font=subtitle_font)
    fee_width = fee_bbox[2] - fee_bbox[0]
    fee_x = (width - fee_width) // 2
    draw.text((fee_x, 120), fee_text, fill=COLOR_GOLD, font=subtitle_font)
    
    # 绘制当前余额
    balance_text = f"当前余额: {current_coins:,} 金币"
    balance_bbox = draw.textbbox((0, 0), balance_text, font=content_font)
    balance_width = balance_bbox[2] - balance_bbox[0]
    balance_x = (width - balance_width) // 2
    draw.text((balance_x, 170), balance_text, fill=COLOR_TEXT_DARK, font=content_font)
    
    # 绘制提示信息
    tips = [
        "这是一个挑战勇气与运气的游戏！",
        "你将面临连续的抉择，",
        "幸存得越久，奖励越丰厚，",
        "但失败将让你失去一切。",
        "",
        "游戏共10层，每层都会提示你",
        "当前的奖金和下一层的成功率。",
        "你需要在60秒内回复【继续】或【放弃】",
        "来决定你的命运！"
    ]
    
    tip_y = 230
    for tip in tips:
        if tip:  # 跳过空行
            tip_bbox = draw.textbbox((0, 0), tip, font=content_font)
            tip_width = tip_bbox[2] - tip_bbox[0]
            tip_x = (width - tip_width) // 2
            draw.text((tip_x, tip_y), tip, fill=COLOR_TEXT_DARK, font=content_font)
        tip_y += 25
    
    return image


def draw_wheel_of_fate_result(message: str, user_nickname: str) -> Image.Image:
    """绘制命运之轮结果图片（通用）"""
    width, height = 800, 500
    
    # 根据消息内容判断是成功还是失败
    is_success = "成功" in message or "恭喜" in message or "获得" in message
    is_failure = "失败" in message or "遗憾" in message or "失去" in message
    
    # 创建渐变背景（使用钓鱼插件标准背景）
    bg_top = (174, 214, 241)  # 浅蓝色
    bg_bot = (245, 251, 255)  # 更浅的蓝色
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(20)
    
    # 绘制用户昵称
    user_text = f"@{user_nickname}"
    user_bbox = draw.textbbox((0, 0), user_text, font=subtitle_font)
    user_width = user_bbox[2] - user_bbox[0]
    user_x = (width - user_width) // 2
    draw.text((user_x, 40), user_text, fill=COLOR_GOLD, font=subtitle_font)
    
    # 绘制消息内容（支持多行）
    lines = message.split('\n')
    line_height = 28
    max_lines = 12  # 最多显示12行
    
    # 如果行数太多，截取前面的
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("...")
    
    y_start = 100
    for i, line in enumerate(lines):
        if not line.strip():  # 跳过空行
            continue
        
        # 自动换行处理
        wrapped_lines = _wrap_text(line, content_font, width - 60)
        
        for wrapped_line in wrapped_lines:
            line_bbox = draw.textbbox((0, 0), wrapped_line, font=content_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            draw.text((line_x, y_start), wrapped_line, fill=COLOR_TEXT_DARK, font=content_font)
            y_start += line_height
            
            # 防止超出图片高度
            if y_start > height - 50:
                break
    
    return image


def draw_wheel_of_fate_help() -> Image.Image:
    """绘制命运之轮帮助说明图片"""
    width, height = 800, 550
    
    # 使用钓鱼插件的标准背景色
    bg_top = (174, 214, 241)  # 浅蓝色
    bg_bot = (245, 251, 255)  # 更浅的蓝色
    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)
    
    # 加载字体
    title_font = load_font(32)
    subtitle_font = load_font(24)
    content_font = load_font(18)
    
    # 绘制标题
    title_text = "命运之轮 玩法说明"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 40), title_text, fill=COLOR_TEXT_DARK, font=title_font)
    
    # 绘制说明内容
    help_content = [
        "这是一个挑战勇气与运气的游戏！",
        "你将面临连续的抉择，",
        "幸存得越久，奖励越丰厚，",
        "但失败将让你失去一切。",
        "",
        "【玩法】",
        "使用 /命运之轮 <金额> 开始游戏。",
        "(金额需在 500 - 50000 之间)",
        "",
        "【规则】",
        "游戏共10层，每层机器人都会提示你",
        "当前的奖金和下一层的成功率。",
        "你需要在 60 秒内回复【继续】或【放弃】",
        "来决定你的命运！",
        "超时将自动放弃并结算当前奖金。",
        "",
        "【概率详情】",
        "前往第 1 层：100% 成功率",
        "前往第 2 层：90% 成功率",
        "前往第 3 层：80% 成功率",
        "前往第 4 层：70% 成功率",
        "前往第 5 层：60% 成功率",
        "前往第 6 层：50% 成功率",
        "前往第 7 层：40% 成功率",
        "前往第 8 层：30% 成功率",
        "前往第 9 层：20% 成功率",
        "前往第10 层：10% 成功率",
        "",
        "祝你好运，挑战者！"
    ]
    
    y_start = 100
    for line in help_content:
        if not line.strip():  # 空行增加间距
            y_start += 10
            continue
        
        # 检查是否是标题
        if line.startswith("【"):
            line_bbox = draw.textbbox((0, 0), line, font=subtitle_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            draw.text((line_x, y_start), line, fill=COLOR_GOLD, font=subtitle_font)
        else:
            line_bbox = draw.textbbox((0, 0), line, font=content_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (width - line_width) // 2
            draw.text((line_x, y_start), line, fill=COLOR_TEXT_DARK, font=content_font)
        
        y_start += 22
    
    return image


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    简单的文本换行处理
    按字符数估算换行位置
    """
    if not text:
        return []
    
    # 估算每个字符的宽度（中文字符约20px，英文字符约10px）
    avg_char_width = 18
    chars_per_line = max_width // avg_char_width
    
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        line_width = bbox[2] - bbox[0]
        
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [text]


def save_image_to_temp(image: Image.Image, prefix: str, data_dir: str) -> str:
    """保存图片到临时目录并返回路径"""
    import tempfile
    import time
    
    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)
    
    # 保存图片
    image.save(temp_path, format='PNG')
    
    return temp_path
