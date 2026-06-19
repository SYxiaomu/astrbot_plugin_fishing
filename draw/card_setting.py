"""
卡片设置图片生成模块
用于生成卡片背景设置相关的图片消息（设置成功、重置、帮助说明等）
"""

from PIL import Image, ImageDraw
from typing import List
from .gradient_utils import create_vertical_gradient
from .styles import (
    COLOR_SUCCESS, COLOR_TEXT_DARK,
    load_font
)

# 统一左侧边距
LEFT_MARGIN = 20


async def draw_card_setting_message(
    message: str,
    title_text: str = "🎨 卡片背景",
    status_type: str = "info",
    user_id: str = None,
    nickname: str = None,
    data_dir: str = None
) -> Image.Image:
    """
    绘制卡片设置结果图片（通用，不显示用户信息模块）

    Args:
        message: 消息文本（支持多行，用 \\n 分隔）
        title_text: 标题文本
        status_type: 状态类型 ("success" / "info" / "error")
        user_id: 用户ID（保留参数，不使用）
        nickname: 用户昵称（保留参数，不使用）
        data_dir: 数据目录（保留参数，不使用）

    Returns:
        PIL.Image.Image: 生成的图片
    """
    width = 400

    # 根据状态类型选择背景色
    if status_type == "success":
        bg_top = (180, 230, 180)
        bg_bot = (240, 255, 240)
    elif status_type == "error":
        bg_top = (255, 190, 180)
        bg_bot = (255, 240, 240)
    else:  # info
        bg_top = (174, 214, 241)
        bg_bot = (245, 251, 255)

    title_font = load_font(24)
    content_font = load_font(16)

    primary_dark = (52, 73, 94)

    # 预处理内容行
    lines = message.split('\n')
    content_lines = [l for l in lines if l.strip()]
    estimated_h = 60 + len(content_lines) * 24 + 30
    height = max(200, min(estimated_h, 500))

    image = create_vertical_gradient(width, height, bg_top, bg_bot)
    draw = ImageDraw.Draw(image)

    # 标题（居中）
    title_w, th = draw.textbbox((0, 0), title_text, font=title_font)[2:4]
    title_x = (width - title_w) // 2
    draw.text((title_x, 15), title_text, fill=primary_dark, font=title_font)
    current_y = 15 + th + 15

    # 分割线
    draw.line([(LEFT_MARGIN, current_y), (width - LEFT_MARGIN, current_y)],
              fill=(180, 200, 220), width=1)
    current_y += 12

    # 绘制消息内容（居左显示）
    line_height = 22
    # 根据状态类型设置文本颜色
    if status_type == "success":
        text_color = COLOR_SUCCESS
    elif status_type == "error":
        text_color = (200, 80, 80)
    else:
        text_color = COLOR_TEXT_DARK

    for line in lines:
        if not line.strip():
            current_y += 6
            continue
        wrapped = _wrap_text(line, content_font, width - LEFT_MARGIN * 2)
        for wl in wrapped:
            draw.text((LEFT_MARGIN, current_y), wl, fill=text_color, font=content_font)
            current_y += line_height
            if current_y > height - 20:
                break

    return image


def _wrap_text(text: str, font, max_width: int) -> List[str]:
    """简单的文本换行处理"""
    if not text:
        return []

    lines = []
    current_line = ""

    # 使用 textbbox 测量宽度
    temp_img = Image.new('RGB', (1, 1), (255, 255, 255))
    temp_draw = ImageDraw.Draw(temp_img)

    for char in text:
        test_line = current_line + char
        try:
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
        except Exception:
            line_width = len(test_line) * font.size

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
    import os

    fd, temp_path = tempfile.mkstemp(suffix='.png', prefix=f"{prefix}_")
    os.close(fd)

    image.save(temp_path, format='PNG')

    return temp_path
