import os
import re
import hashlib
from typing import Optional, Tuple
from PIL import Image, ImageDraw
from astrbot.api import logger


def draw_rounded_rectangle(draw, bbox, radius, fill=None, outline=None, width=1):
    """绘制圆角矩形（通用工具函数）"""
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y1, x1 + 2 * radius, y1 + 2 * radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - 2 * radius, y1, x2, y1 + 2 * radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y2 - 2 * radius, x1 + 2 * radius, y2], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - 2 * radius, y2 - 2 * radius, x2, y2], fill=fill, outline=outline, width=width)


def _safe_user_id(user_id: str) -> str:
    """将 user_id 安全化为文件名"""
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', user_id)
    safe = re.sub(r'_+', '_', safe).strip('_') or 'unknown'
    return safe


def get_card_bg_path(user_id: str, data_dir: str) -> Optional[str]:
    """获取用户自定义卡片背景图的文件路径，不存在则返回 None"""
    safe_uid = _safe_user_id(user_id)
    bg_dir = os.path.join(data_dir, "card_bg")
    bg_path = os.path.join(bg_dir, f"{safe_uid}.png")
    if os.path.exists(bg_path):
        return bg_path
    return None


async def get_user_card_bg(user_id: str, data_dir: str, card_width: int, card_height: int, radius: int = 10) -> Optional[Image.Image]:
    """
    获取用户自定义卡片背景图并处理为目标尺寸圆角矩形。

    Args:
        user_id: 用户ID
        data_dir: 插件数据目录
        card_width: 目标卡片宽度
        card_height: 目标卡片高度
        radius: 圆角半径

    Returns:
        处理后的 PIL.Image (RGBA)，或者 None（无自定义背景时）
    """
    bg_path = get_card_bg_path(user_id, data_dir)
    if not bg_path:
        return None

    try:
        bg_image = Image.open(bg_path).convert('RGBA')

        # 智能缩放并居中裁剪到目标尺寸
        src_w, src_h = bg_image.size
        scale = max(card_width / src_w, card_height / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        bg_image = bg_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 居中裁剪
        left = (new_w - card_width) // 2
        top = (new_h - card_height) // 2
        bg_image = bg_image.crop((left, top, left + card_width, top + card_height))

        # 处理为圆角矩形（抗锯齿）
        scale_factor = 4
        large_w = card_width * scale_factor
        large_h = card_height * scale_factor
        large_radius = radius * scale_factor

        large_mask = Image.new('L', (large_w, large_h), 0)
        large_draw = ImageDraw.Draw(large_mask)
        large_draw.rounded_rectangle([0, 0, large_w, large_h], radius=large_radius, fill=255)
        mask = large_mask.resize((card_width, card_height), Image.Resampling.LANCZOS)
        bg_image.putalpha(mask)

        return bg_image
    except Exception as e:
        logger.warning(f"加载用户 {user_id} 的自定义卡片背景失败: {e}")
        return None


async def draw_user_card_bg(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    user_id: str,
    data_dir: str,
    bbox: Tuple[int, int, int, int],
    radius: int = 10,
    fallback_fill=(255, 255, 255, 240)
):
    """
    绘制用户卡片背景 - 优先使用自定义背景图，否则使用默认填充色。

    Args:
        image: 主图像 (RGBA)
        draw: ImageDraw 对象
        user_id: 用户ID
        data_dir: 插件数据目录
        bbox: 卡片边界框 (x1, y1, x2, y2)
        radius: 圆角半径
        fallback_fill: 默认填充色（当无自定义背景时使用）
    """
    x1, y1, x2, y2 = bbox
    card_w = x2 - x1
    card_h = y2 - y1

    custom_bg = await get_user_card_bg(user_id, data_dir, card_w, card_h, radius)
    if custom_bg:
        # 确保主图像是 RGBA 模式以支持透明粘贴
        if image.mode != 'RGBA':
            # 无法直接转换，使用 paste 的 mask 参数
            image.paste(custom_bg, (x1, y1), custom_bg)
        else:
            image.paste(custom_bg, (x1, y1), custom_bg)
    else:
        # 回退到默认白色圆角矩形
        draw_rounded_rectangle(draw, bbox, radius, fill=fallback_fill)


async def save_user_card_bg(user_id: str, data_dir: str, image_data: bytes) -> str:
    """
    保存用户上传的卡片背景图。

    Args:
        user_id: 用户ID
        data_dir: 插件数据目录
        image_data: 图片二进制数据

    Returns:
        保存后的文件路径

    Raises:
        ValueError: 图片格式不支持或文件过大
    """
    from io import BytesIO

    # 检查文件大小（最大 10MB）
    if len(image_data) > 10 * 1024 * 1024:
        raise ValueError("图片文件大小超过 10MB 限制")

    # 打开并验证图片
    try:
        img = Image.open(BytesIO(image_data))
        if img.format and img.format.upper() not in ('PNG', 'JPEG', 'JPG'):
            raise ValueError(f"不支持的图片格式: {img.format}，请使用 PNG 或 JPG")
    except Exception as e:
        raise ValueError(f"无法解析图片: {e}")

    # 创建存储目录
    bg_dir = os.path.join(data_dir, "card_bg")
    os.makedirs(bg_dir, exist_ok=True)

    # 保存为 PNG
    safe_uid = _safe_user_id(user_id)
    bg_path = os.path.join(bg_dir, f"{safe_uid}.png")

    # 转换为 RGBA 并保存
    img = img.convert('RGBA')
    img.save(bg_path, 'PNG')

    return bg_path


def remove_user_card_bg(user_id: str, data_dir: str) -> bool:
    """删除用户的自定义卡片背景图"""
    bg_path = get_card_bg_path(user_id, data_dir)
    if bg_path and os.path.exists(bg_path):
        try:
            os.remove(bg_path)
            return True
        except Exception as e:
            logger.warning(f"删除用户 {user_id} 的卡片背景图失败: {e}")
    return False


async def get_user_avatar(user_id: str, data_dir: str, avatar_size: int = 50) -> Optional[Image.Image]:
    """
    获取用户头像并处理为圆形
    
    Args:
        user_id: 用户ID
        data_dir: 插件的数据目录
        avatar_size: 头像尺寸
    
    Returns:
        处理后的头像图像，如果失败返回None
    """
    try:
        import aiohttp
        from io import BytesIO
        import time
        
        # 创建头像缓存目录
        cache_dir = os.path.join(data_dir, "avatar_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # 安全化user_id用于文件名
        import re
        safe_user_id = re.sub(r'[^a-zA-Z0-9._-]', '_', user_id)
        safe_user_id = re.sub(r'_+', '_', safe_user_id).strip('_') or 'unknown'
        avatar_cache_path = os.path.join(cache_dir, f"{safe_user_id}_avatar.png")
        
        # 检查是否有缓存的头像（24小时刷新）
        avatar_image = None
        if os.path.exists(avatar_cache_path):
            try:
                file_age = time.time() - os.path.getmtime(avatar_cache_path)
                if file_age < 86400:  # 24小时
                    avatar_image = Image.open(avatar_cache_path).convert('RGBA')
            except:
                pass
        
        # 如果没有缓存或缓存过期，重新下载
        if avatar_image is None:
            avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
            try:
                # 增加超时时间并添加重试机制
                timeout = aiohttp.ClientTimeout(total=10, connect=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(avatar_url) as response:
                        if response.status == 200:
                            content = await response.read()
                            avatar_image = Image.open(BytesIO(content)).convert('RGBA')
                            # 保存到缓存
                            avatar_image.save(avatar_cache_path, 'PNG')
            except Exception as e:
                # 如果下载失败，记录日志但不抛出异常
                logger.warning(f"头像下载失败: {e}")
                return None
        
        if avatar_image:
            return avatar_postprocess(avatar_image, avatar_size)
        
    except Exception as e:
        pass
    
    return None

def avatar_postprocess(avatar_image: Image.Image, size: int) -> Image.Image:
    """
    将头像处理为指定大小的圆角头像
    """
    # 调整头像大小
    avatar_image = avatar_image.resize((size, size), Image.Resampling.LANCZOS)
    
    # 使用更合适的圆角半径
    corner_radius = size // 8  # 稍微减小圆角，看起来更自然
    
    # 抗锯齿处理
    scale_factor = 4
    large_size = size * scale_factor
    large_radius = corner_radius * scale_factor
    
    # 创建高质量遮罩
    large_mask = Image.new('L', (large_size, large_size), 0)
    large_draw = ImageDraw.Draw(large_mask)
    
    # 绘制圆角矩形
    large_draw.rounded_rectangle(
        [0, 0, large_size, large_size], 
        radius=large_radius, 
        fill=255
    )
    
    # 高质量缩放
    mask = large_mask.resize((size, size), Image.Resampling.LANCZOS)
    avatar_image.putalpha(mask)
    
    return avatar_image

async def get_fish_icon(icon_url: str, data_dir: str, icon_size: int = 60) -> Optional[Image.Image]:
    """
    下载并处理鱼类图标
    
    Args:
        icon_url: 图标URL
        data_dir: 插件的数据目录
        icon_size: 图标尺寸
    
    Returns:
        处理后的图标图像，如果失败返回None
    """
    if not icon_url or not icon_url.strip():
        return None
    
    try:
        import aiohttp
        from io import BytesIO
        import time
        
        # 创建图标缓存目录
        cache_dir = os.path.join(data_dir, "fish_icon_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # 使用URL的hash作为缓存文件名
        url_hash = hashlib.md5(icon_url.encode()).hexdigest()
        icon_cache_path = os.path.join(cache_dir, f"{url_hash}.png")
        
        # 检查是否有缓存的图标（7天刷新）
        icon_image = None
        if os.path.exists(icon_cache_path):
            try:
                file_age = time.time() - os.path.getmtime(icon_cache_path)
                if file_age < 604800:  # 7天
                    icon_image = Image.open(icon_cache_path).convert('RGBA')
            except:
                pass
        
        # 如果没有缓存或缓存过期，重新下载
        if icon_image is None:
            try:
                timeout = aiohttp.ClientTimeout(total=10, connect=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(icon_url.strip()) as response:
                        if response.status == 200:
                            content = await response.read()
                            # 限制文件大小（最大5MB）
                            if len(content) > 5 * 1024 * 1024:
                                logger.warning(f"图标文件过大，跳过: {icon_url}")
                                return None
                            icon_image = Image.open(BytesIO(content)).convert('RGBA')
                            # 保存到缓存
                            icon_image.save(icon_cache_path, 'PNG')
                        else:
                            logger.warning(f"下载图标失败，HTTP状态码: {response.status}, URL: {icon_url}")
                            return None
            except Exception as e:
                # 如果下载失败，记录日志但不抛出异常
                logger.warning(f"图标下载失败: {e}, URL: {icon_url}")
                return None
        
        if icon_image:
            # 调整图标大小并保持宽高比
            icon_image.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
            return icon_image
        
    except Exception as e:
        logger.warning(f"处理图标时发生错误: {e}, URL: {icon_url}")
    
    return None
