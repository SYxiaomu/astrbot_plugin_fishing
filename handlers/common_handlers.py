import os
from astrbot.api.event import filter, AstrMessageEvent
from ..draw.help import draw_help_image
from ..draw.state import draw_state_image, get_user_state_data
from ..draw.card_setting import draw_card_setting_message, save_image_to_temp as save_card_image
from ..core.utils import get_now
from ..utils import safe_datetime_handler, parse_target_user_id, parse_amount
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import FishingPlugin


async def register_user(self: "FishingPlugin", event: AstrMessageEvent):
    """注册用户命令"""
    user_id = self._get_effective_user_id(event)
    nickname = event.get_sender_name() if event.get_sender_name() is not None else user_id
    if result := self.user_service.register(user_id, nickname):
        yield event.plain_result(result["message"])
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")

async def sign_in(self: "FishingPlugin", event: AstrMessageEvent):
    """签到"""
    user_id = self._get_effective_user_id(event)
    result = self.user_service.daily_sign_in(user_id)
    if result["success"]:
        yield event.plain_result(result["message"])

async def state(self: "FishingPlugin", event: AstrMessageEvent):
    """查看用户状态"""
    user_id = self._get_effective_user_id(event)

    # 调用新的数据获取函数
    user_data = get_user_state_data(
        self.user_repo,
        self.inventory_repo,
        self.item_template_repo,
        self.log_repo,
        self.buff_repo,
        self.game_config,
        user_id,
    )
    
    if not user_data:
        yield event.plain_result('❌ 用户不存在，请先发送"注册"来开始游戏')
        return
    # 生成状态图像
    image = await draw_state_image(user_data, self.data_dir)
    # 保存图像到临时文件
    image_path = os.path.join(self.tmp_dir, "user_status.png")
    image.save(image_path)
    yield event.image_result(image_path)

async def fishing_log(self: "FishingPlugin", event: AstrMessageEvent):
    """查看钓鱼记录"""
    user_id = self._get_effective_user_id(event)
    if result := self.fishing_service.get_user_fish_log(user_id):
        if result["success"]:
            records = result["records"]
            if not records:
                yield event.plain_result("❌ 您还没有钓鱼记录。")
                return
            message = "【📜 钓鱼记录】：\n"
            for record in records:
                message += (f" - {record['fish_name']} ({'★' * record['fish_rarity']})\n"
                            f" - ⚖️重量: {record['fish_weight']} 克 - 💰价值: {record['fish_value']} 金币\n"
                            f" - 🔧装备： {record['accessory']} & {record['rod']} | 🎣鱼饵: {record['bait']}\n"
                            f" - 钓鱼时间: {safe_datetime_handler(record['timestamp'])}\n")
            yield event.plain_result(message)
        else:
            yield event.plain_result(f"❌ 获取钓鱼记录失败：{result['message']}")
    else:
        yield event.plain_result("❌ 出错啦！请稍后再试。")

async def fishing_help(self: "FishingPlugin", event: AstrMessageEvent):
    """显示钓鱼插件帮助信息"""
    image = draw_help_image()
    output_path = os.path.join(self.tmp_dir, "fishing_help.png")
    image.save(output_path)
    yield event.image_result(output_path)

async def transfer_coins(self: "FishingPlugin", event: AstrMessageEvent):
    """转账金币"""
    args = event.message_str.split(" ")
    
    # 解析目标用户ID（支持@和用户ID两种方式）
    target_user_id, error_msg = parse_target_user_id(event, args, 1)
    if error_msg:
        yield event.plain_result(error_msg)
        return
    
    # 检查转账金额参数
    if len(args) < 3:
        yield event.plain_result(
            "❌ 请指定转账金额，例如：/转账 @用户 1000 或 /转账 @用户 1万 或 /转账 @用户 一千"
        )
        return
    
    amount_str = args[2]
    
    # 使用通用解析器，支持中文与混写
    try:
        amount = parse_amount(amount_str)
    except Exception as e:
        yield event.plain_result(f"❌ 无法解析转账金额：{str(e)}。示例：/转账 @用户 1000 或 /转账 @用户 1万 或 /转账 @用户 一千")
        return
    
    from_user_id = self._get_effective_user_id(event)
    
    # 调用转账服务
    result = self.user_service.transfer_coins(from_user_id, target_user_id, amount)
    yield event.plain_result(result["message"])


async def update_nickname(self: "FishingPlugin", event: AstrMessageEvent):
    """更新用户昵称"""
    args = event.message_str.split(" ")
    
    # 检查是否提供了新昵称
    if len(args) < 2:
        yield event.plain_result(
            "❌ 请提供新昵称，例如：/更新昵称 新的昵称\n"
            "💡 昵称要求：\n"
            "  - 不能为空\n"
            "  - 长度不超过32个字符\n"
            "  - 支持中文、英文、数字和常用符号"
        )
        return
    
    # 提取新昵称（支持包含空格的昵称）
    new_nickname = " ".join(args[1:])
    
    user_id = self._get_effective_user_id(event)
    
    # 调用用户服务更新昵称
    result = self.user_service.update_nickname(user_id, new_nickname)
    yield event.plain_result(result["message"])


async def set_card_bg(self: "FishingPlugin", event: AstrMessageEvent):
    """设置用户自定义卡片背景图"""
    from astrbot.api import logger
    user_id = self._get_effective_user_id(event)

    # 检查用户是否已注册
    user = self.user_repo.get_by_id(user_id)
    if not user:
        yield event.plain_result("❌ 您还没有注册，请先使用 /注册 命令注册。")
        return

    args = event.message_str.strip().split()

    # 获取用户昵称（用于图片展示）
    nickname = user.nickname if user and user.nickname else user_id

    # 子命令：重置
    if len(args) >= 2 and args[1] in ("重置", "reset", "清除", "删除"):
        from ..draw.utils import remove_user_card_bg
        removed = remove_user_card_bg(user_id, self.data_dir)
        # 清除数据库记录
        user.card_bg_path = None
        self.user_repo.update(user)
        if removed:
            image = await draw_card_setting_message(
                "✅ 卡片背景已重置为默认白色样式。",
                title_text="🎨 卡片背景",
                status_type="success",
                user_id=user_id, nickname=nickname, data_dir=self.data_dir
            )
            image_path = save_card_image(image, "card_bg_reset", self.data_dir)
            yield event.image_result(image_path)
        else:
            image = await draw_card_setting_message(
                "ℹ️ 您当前没有设置自定义卡片背景。",
                title_text="🎨 卡片背景",
                status_type="info",
                user_id=user_id, nickname=nickname, data_dir=self.data_dir
            )
            image_path = save_card_image(image, "card_bg_no_bg", self.data_dir)
            yield event.image_result(image_path)
        return

    # 子命令：查看
    if len(args) >= 2 and args[1] in ("查看", "view", "预览"):
        from ..draw.utils import get_card_bg_path
        bg_path = get_card_bg_path(user_id, self.data_dir)
        if bg_path:
            yield event.image_result(bg_path)
        else:
            image = await draw_card_setting_message(
                "ℹ️ 您当前没有设置自定义卡片背景，使用默认白色样式。\n💡 发送 /卡片背景 + 图片 即可设置自定义背景。",
                title_text="🎨 卡片背景",
                status_type="info",
                user_id=user_id, nickname=nickname, data_dir=self.data_dir
            )
            image_path = save_card_image(image, "card_bg_view", self.data_dir)
            yield event.image_result(image_path)
        return

    # 上传模式：查找消息中的图片组件
    image_url = None
    message_chain = event.message_obj.message
    for component in message_chain:
        # AstrBot Image 组件的 type 是 ComponentType.Image (值为 'Image')
        comp_type = getattr(component, 'type', None)
        is_image = False
        if comp_type is not None:
            # 支持枚举比较和字符串比较
            if hasattr(comp_type, 'value'):
                is_image = comp_type.value == 'Image'
            else:
                is_image = str(comp_type).lower() == 'image'
        # 回退：检查类名
        if not is_image:
            is_image = type(component).__name__ == 'Image'

        if is_image:
            # 尝试获取图片 URL
            if hasattr(component, 'url') and component.url:
                image_url = component.url
                break
            elif hasattr(component, 'file') and component.file and component.file.startswith('http'):
                image_url = component.file
                break

    if not image_url:
        help_message = (
            "💡 卡片背景设置说明：\n"
            "━━━━━━━━━━━━━\n"
            "📷 设置背景：/卡片背景 + 发送一张图片\n"
            "🔄 重置背景：/卡片背景 重置\n"
            "👀 查看当前：/卡片背景 查看\n"
            "━━━━━━━━━━━━━\n"
            "📝 图片要求：\n"
            "  - 格式：PNG 或 JPG\n"
            "  - 推荐尺寸：800 x 150 px\n"
            "  - 最小尺寸：400 x 90 px\n"
            "  - 最大文件：10MB\n"
            "  - PNG 支持半透明效果"
        )
        image = await draw_card_setting_message(
            help_message,
            title_text="🎨 卡片背景",
            status_type="info",
            user_id=user_id, nickname=nickname, data_dir=self.data_dir
        )
        image_path = save_card_image(image, "card_bg_help", self.data_dir)
        yield event.image_result(image_path)
        return

    # 下载图片
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                else:
                    yield event.plain_result(f"❌ 下载图片失败，HTTP 状态码: {response.status}")
                    return
    except Exception as e:
        logger.error(f"下载卡片背景图片失败: {e}")
        yield event.plain_result(f"❌ 下载图片失败：{e}")
        return

    # 保存并更新
    try:
        from ..draw.utils import save_user_card_bg
        bg_path = await save_user_card_bg(user_id, self.data_dir, image_data)
        # 更新数据库
        user.card_bg_path = bg_path
        self.user_repo.update(user)
        success_message = (
            "✅ 卡片背景设置成功！\n"
            "📝 您的信息卡片将在以下场景中使用自定义背景：\n"
            "  - 排行榜、背包、状态、鱼塘、水族箱\n"
            "  - 钓鱼结果、擦弹、命运之轮、偷鱼等\n"
            "💡 发送 /卡片背景 重置 可恢复默认样式"
        )
        image = await draw_card_setting_message(
            success_message,
            title_text="🎨 卡片背景",
            status_type="success",
            user_id=user_id, nickname=nickname, data_dir=self.data_dir
        )
        image_path = save_card_image(image, "card_bg_set", self.data_dir)
        yield event.image_result(image_path)
    except ValueError as e:
        yield event.plain_result(f"❌ {e}")
    except Exception as e:
        logger.error(f"保存卡片背景失败: {e}")
        yield event.plain_result(f"❌ 保存卡片背景失败：{e}")