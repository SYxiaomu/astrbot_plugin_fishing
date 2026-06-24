import requests
import random
import json
from typing import Dict, Any, Optional, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor
from astrbot.api import logger

# 导入仓储接口和领域模型
from ..repositories.abstract_repository import (
    AbstractUserRepository,
    AbstractLogRepository,
    AbstractInventoryRepository,
    AbstractItemTemplateRepository,
    AbstractUserBuffRepository,
)
from ..domain.models import WipeBombLog, User
from ...core.utils import get_now, get_today

if TYPE_CHECKING:
    from ..repositories.sqlite_user_repo import SqliteUserRepository

def weighted_random_choice(choices: list[tuple[any, any, float]]) -> tuple[any, any, float]:
    """
    带权重的随机选择。
    :param choices: 一个列表，每个元素是一个元组 (min_val, max_val, weight)。
    :return: 选中的元组。
    """
    total_weight = sum(w for _, _, w in choices)
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")
    rand_val = random.uniform(0, total_weight)
    
    current_weight = 0
    for choice in choices:
        current_weight += choice[2] # weight is the 3rd element
        if rand_val <= current_weight:
            return choice
    
    # Fallback in case of floating point inaccuracies
    return choices[-1]

class GameMechanicsService:
    """封装特殊或独立的游戏机制"""


    def __init__(
        self,
        user_repo: AbstractUserRepository,
        log_repo: AbstractLogRepository,
        inventory_repo: AbstractInventoryRepository,
        item_template_repo: AbstractItemTemplateRepository,
        buff_repo: AbstractUserBuffRepository,
        config: Dict[str, Any]
    ):
        self.user_repo = user_repo
        self.log_repo = log_repo
        self.inventory_repo = inventory_repo
        self.item_template_repo = item_template_repo
        self.buff_repo = buff_repo
        self.config = config
        # 服务器级别的抑制状态
        self._server_suppressed = False
        self._last_suppression_date = None
        self.thread_pool = ThreadPoolExecutor(max_workers=5)

    def _check_server_suppression(self) -> bool:
        """检查服务器级别的抑制状态，如果需要则重置"""
        today = get_today()
        
        # 如果是新的一天，重置抑制状态
        if self._last_suppression_date is None or self._last_suppression_date < today:
            self._server_suppressed = False
            self._last_suppression_date = today
        
        return self._server_suppressed
    
    def _trigger_server_suppression(self):
        """触发服务器级别的抑制状态"""
        self._server_suppressed = True
        self._last_suppression_date = get_today()

    def _get_fortune_tier_for_multiplier(self, multiplier: float) -> str:
        if multiplier >= 200.0: return "kyokudaikichi"    # 極大吉 (200-1500倍)
        if multiplier >= 50.0: return "chodaikichi"       # 超大吉 (50-200倍)
        if multiplier >= 15.0: return "daikichi"          # 大吉 (15-50倍)
        if multiplier >= 6.0: return "chukichi"           # 中吉 (6-15倍)
        if multiplier >= 3.0: return "kichi"              # 吉 (3-6倍)
        if multiplier >= 2.0: return "shokichi"           # 小吉 (2-3倍)
        if multiplier >= 1.0: return "suekichi"           # 末吉 (1.0-2倍)
        return "kyo"                                       # 凶 (0-1倍)
    

    def steal_fish(self, thief_id: str, victim_id: str) -> Dict[str, Any]:
        """
        处理"偷鱼"的逻辑。
        """
        if thief_id == victim_id:
            return {"success": False, "message": "不能偷自己的鱼！"}

        thief = self.user_repo.get_by_id(thief_id)
        if not thief:
            return {"success": False, "message": "偷窃者用户不存在"}

        victim = self.user_repo.get_by_id(victim_id)
        if not victim:
            return {"success": False, "message": "目标用户不存在"}

        # 0. 首先检查偷窃CD
        cooldown_seconds = self.config.get("steal", {}).get("cooldown_seconds", 14400) # 默认4小时
        now = get_now()

        # 修复时区问题
        last_steal_time = thief.last_steal_time
        if last_steal_time and last_steal_time.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        elif last_steal_time and last_steal_time.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=last_steal_time.tzinfo)

        if last_steal_time and (now - last_steal_time).total_seconds() < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_steal_time).total_seconds())
            return {"success": False, "message": f"偷鱼冷却中，请等待 {remaining // 60} 分钟后再试"}

        # 1. 检查受害者是否受保护，以及偷窃者是否有反制能力
        protection_buff = self.buff_repo.get_active_by_user_and_type(
            victim_id, "STEAL_PROTECTION_BUFF"
        )
        
        penetration_buff = self.buff_repo.get_active_by_user_and_type(
            thief_id, "STEAL_PENETRATION_BUFF"
        )
        shadow_cloak_buff = self.buff_repo.get_active_by_user_and_type(
            thief_id, "SHADOW_CLOAK_BUFF"
        )
        
        if protection_buff:
            if not penetration_buff and not shadow_cloak_buff:
                return {"success": False, "message": f"❌ 无法偷窃，【{victim.nickname}】的鱼塘似乎被神秘力量守护着！"}
            else:
                if shadow_cloak_buff:
                    self.buff_repo.delete(shadow_cloak_buff.id)

        # 2. 检查受害者是否有鱼可偷
        victim_inventory = self.inventory_repo.get_fish_inventory(victim_id)
        if not victim_inventory:
            return {"success": False, "message": f"目标用户【{victim.nickname}】的鱼塘是空的！"}

        # 3. 随机选择一条鱼偷取
        stolen_fish_item = random.choice(victim_inventory)
        stolen_fish_template = self.item_template_repo.get_fish_by_id(stolen_fish_item.fish_id)

        if not stolen_fish_template:
            return {"success": False, "message": "发生内部错误，无法识别被偷的鱼"}

        # 4. 执行偷窃事务（保持品质属性）
        self.inventory_repo.update_fish_quantity(victim_id, stolen_fish_item.fish_id, delta=-1, quality_level=stolen_fish_item.quality_level)
        self.inventory_repo.add_fish_to_inventory(thief_id, stolen_fish_item.fish_id, quantity=1, quality_level=stolen_fish_item.quality_level)

        # 5. 更新偷窃者的CD时间
        thief.last_steal_time = now
        self.user_repo.update(thief)

        # 6. 生成成功消息
        counter_message = ""
        if protection_buff:
            if penetration_buff:
                counter_message = "破灵符的力量穿透了海灵守护！"
            elif shadow_cloak_buff:
                counter_message = "🌑 暗影斗篷让你在阴影中行动！"

        # 构建品质信息
        quality_info = ""
        actual_value = stolen_fish_template.base_value
        if stolen_fish_item.quality_level == 1:
            quality_info = "（✨高品质）"
            actual_value = stolen_fish_template.base_value * 2
        
        stolen_fish_list = [{
            'name': stolen_fish_template.name,
            'fish_id': stolen_fish_template.fish_id,
            'rarity': stolen_fish_template.rarity,
            'value': actual_value,
            'quantity': 1,
            'quality_level': stolen_fish_item.quality_level
        }]

        return {
            "success": True,
            "message": f"{counter_message}✅ 成功从【{victim.nickname}】的鱼塘里偷到了一条{stolen_fish_template.rarity}★【{stolen_fish_template.name}】{quality_info}！价值 {actual_value} 金币",
            "stolen_fish": stolen_fish_list,
        }

    # ============================================================
    # ==================== 新增功能：电鱼 开始 ====================
    # ============================================================
    def electric_fish(self, thief_id: str, victim_id: str) -> Dict[str, Any]:
        """
        处理"电鱼"的逻辑。
        - 基础成功率，受多种因素影响
        - 失败会扣除金币作为设备损坏费
        - 成功有三个档次：大成功、普通成功、小成功
        - 对鱼塘内鱼数>=100的目标随机偷取
        - 其中最多只能包含一条5星及以上的鱼
        """
        if thief_id == victim_id:
            return {"success": False, "message": "不能电自己的鱼！"}
    
        thief = self.user_repo.get_by_id(thief_id)
        if not thief:
            return {"success": False, "message": "使用者用户不存在"}
    
        victim = self.user_repo.get_by_id(victim_id)
        if not victim:
            return {"success": False, "message": "目标用户不存在"}
    
        # 0. 检查电鱼CD
        cooldown_seconds = self.config.get("electric_fish", {}).get("cooldown_seconds", 10800) # 默认3小时
        now = get_now()
    
        last_electric_fish_time = thief.last_electric_fish_time
        if last_electric_fish_time and last_electric_fish_time.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        elif last_electric_fish_time and last_electric_fish_time.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=last_electric_fish_time.tzinfo)
    
        if last_electric_fish_time and (now - last_electric_fish_time).total_seconds() < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_electric_fish_time).total_seconds())
            return {"success": False, "message": f"电鱼冷却中，请等待 {remaining // 60} 分钟后再试"}
    
        # 1. 检查受害者是否受保护，逻辑同偷鱼
        protection_buff = self.buff_repo.get_active_by_user_and_type(
            victim_id, "STEAL_PROTECTION_BUFF"
        )
        
        penetration_buff = self.buff_repo.get_active_by_user_and_type(
            thief_id, "STEAL_PENETRATION_BUFF"
        )
        shadow_cloak_buff = self.buff_repo.get_active_by_user_and_type(
            thief_id, "SHADOW_CLOAK_BUFF"
        )
        
        if protection_buff:
            if not penetration_buff and not shadow_cloak_buff:
                return {"success": False, "message": f"❌ 无法电鱼，【{victim.nickname}】的鱼塘似乎被神秘力量守护着！"}
            else:
                if shadow_cloak_buff:
                    self.buff_repo.delete(shadow_cloak_buff.id)
    
        # 2. 检查受害者鱼塘数量是否达标
        victim_inventory = self.inventory_repo.get_fish_inventory(victim_id)
        if not victim_inventory:
            return {"success": False, "message": f"目标用户【{victim.nickname}】的鱼塘是空的！"}
        
        total_fish_count = sum(item.quantity for item in victim_inventory)
        if total_fish_count < 100:
            return {"success": False, "message": f"目标用户【{victim.nickname}】的鱼塘里鱼太少了（{total_fish_count}/100），电不到什么好东西，还是放过他吧。"}
        
        # 3. 计算成功率并进行判定
        # 所有目标用户的成功率相同，只使用基础成功率
        final_success_rate = self.config.get("electric_fish", {}).get("base_success_rate", 0.6)
        
        # 进行随机判定
        roll = random.random()
        
        # 失败处理
        if roll > final_success_rate:
            # 使用正态分布计算天罚百分比（0-max_rate之间）
            max_penalty_rate = self.config.get("electric_fish", {}).get("failure_penalty_max_rate", 0.5)
            
            # 正态分布，均值在中间（max_rate/2），标准差使得95%的值在0到max_rate之间
            mean = max_penalty_rate / 2
            std_dev = max_penalty_rate / 4  # 约95%的值在[0, max_rate]之间
            
            # 使用random.gauss生成正态分布的惩罚比例，并限制在[0, max_rate]范围内
            penalty_rate = random.gauss(mean, std_dev)
            penalty_rate = max(0.0, min(max_penalty_rate, penalty_rate))
            
            # 计算实际扣除的金币
            penalty_coins = int(thief.coins * penalty_rate)
            
            thief.coins -= penalty_coins
            thief.last_electric_fish_time = now  # 失败也要更新CD
            self.user_repo.update(thief)
            
            # 根据惩罚程度显示不同的消息（动态基于配置的最大天罚）
            # 轻微: 0-20%的max, 中度: 20-50%的max, 严重: 50-80%的max, 毁灭性: 80-100%的max
            relative_penalty = penalty_rate / max_penalty_rate if max_penalty_rate > 0 else 0
            if relative_penalty < 0.2:
                severity = "轻微天罚"
            elif relative_penalty < 0.5:
                severity = "中度天罚"
            elif relative_penalty < 0.8:
                severity = "严重天罚"
            else:
                severity = "毁灭性天罚"
                        
            return {
                "success": False,
                "message": f"电鱼失败！\n{severity}降临，雷电击中了你，损失了 {penalty_coins} 金币（{penalty_rate*100:.1f}%）！"
            }

        # 4. 成功了！根据成功度（roll值）决定收益档次
        # roll越接近0表示越幸运，获得的收益越高
        success_quality = roll / final_success_rate  # 归一化到0-1之间
        
        # 分段式收益：
        # - 大成功（0-0.3）：15%-20%的鱼
        # - 普通成功（0.3-0.7）：10%-15%的鱼
        # - 小成功（0.7-1.0）：5%-10%的鱼
        success_type = ""
        multiplier_range = (0, 0)
        
        if success_quality <= 0.3:
            success_type = "⭐大成功"
            multiplier_range = (0.15, 0.20)
        elif success_quality <= 0.7:
            success_type = "✅普通成功"
            multiplier_range = (0.10, 0.15)
        else:
            success_type = "🔹小成功"
            multiplier_range = (0.05, 0.10)

        # 5. 准备数据：获取鱼模板并将鱼塘扁平化
        fish_templates = {
            item.fish_id: self.item_template_repo.get_fish_by_id(item.fish_id)
            for item in victim_inventory
        }
        # 构建品质映射：(fish_id, quality_level) -> count
        quality_map = {}
        for item in victim_inventory:
            key = (item.fish_id, item.quality_level)
            quality_map[key] = quality_map.get(key, 0) + item.quantity

        # 扁平化鱼塘，保留品质信息
        all_fish_in_pond = []
        for item in victim_inventory:
            all_fish_in_pond.extend([(item.fish_id, item.quality_level)] * item.quantity)

        # 6. 决定偷取数量并进行初次完全随机抽样
        num_to_steal = 0
        if total_fish_count > 400:
            # 如果鱼数大于400，按成功档次的百分比计算
            lower_bound = max(1, int(total_fish_count * multiplier_range[0]))
            upper_bound = max(lower_bound, int(total_fish_count * multiplier_range[1]))
            num_to_steal = random.randint(lower_bound, upper_bound)
        else:
            # 鱼数较少时，使用固定数量区间
            if success_quality <= 0.3:
                num_to_steal = random.randint(20, 30)  # 大成功
            elif success_quality <= 0.7:
                num_to_steal = random.randint(10, 20)  # 普通成功
            else:
                num_to_steal = random.randint(5, 10)   # 小成功

        actual_num_to_steal = min(num_to_steal, len(all_fish_in_pond))
        initial_catch = random.sample(all_fish_in_pond, actual_num_to_steal)

        # 7. 检查并修正高星鱼数量
        high_rarity_caught = []
        low_rarity_caught = []
        for fish_entry in initial_catch:
            template = fish_templates.get(fish_entry[0])
            if template and template.rarity >= 5:
                high_rarity_caught.append(fish_entry)
            else:
                low_rarity_caught.append(fish_entry)

        final_stolen_fish = []
        if len(high_rarity_caught) <= 1:
            final_stolen_fish = initial_catch
        else:
            random.shuffle(high_rarity_caught)
            final_stolen_fish.append(high_rarity_caught.pop(0))
            final_stolen_fish.extend(low_rarity_caught)

            num_to_replace = len(high_rarity_caught)

            from collections import Counter
            pond_counts = Counter(all_fish_in_pond)
            initial_catch_counts = Counter(initial_catch)
            pond_counts.subtract(initial_catch_counts)

            replacement_pool = []
            for fish_entry, count in pond_counts.items():
                if count > 0:
                    template = fish_templates.get(fish_entry[0])
                    if template and template.rarity < 5:
                        replacement_pool.extend([fish_entry] * count)

            if replacement_pool:
                num_can_replace = min(num_to_replace, len(replacement_pool))
                replacements = random.sample(replacement_pool, num_can_replace)
                final_stolen_fish.extend(replacements)

        # 8. 统计最终偷到的鱼（按 fish_id + quality_level 分组）
        stolen_fish_counts = {}
        for fish_id, quality_level in final_stolen_fish:
            key = (fish_id, quality_level)
            stolen_fish_counts[key] = stolen_fish_counts.get(key, 0) + 1

        # 9. 执行电鱼事务并计算总价值（保留原品质）
        stolen_summary = []
        stolen_fish_details = []
        total_value_stolen = 0

        for (fish_id, quality_level), count in stolen_fish_counts.items():
            self.inventory_repo.update_fish_quantity(victim_id, fish_id, delta=-count, quality_level=quality_level)
            self.inventory_repo.add_fish_to_inventory(thief_id, fish_id, quantity=count, quality_level=quality_level)

            template = fish_templates.get(fish_id)
            if template:
                value = template.base_value * (1 + quality_level)
                quality_text = "（✨高品质）" if quality_level == 1 else ""
                stolen_summary.append(f"【{template.name}】x{count}{quality_text}")
                total_value_stolen += value * count
                stolen_fish_details.append({
                    'name': template.name,
                    'fish_id': template.fish_id,
                    'rarity': template.rarity,
                    'value': value * count,
                    'quantity': count,
                    'quality_level': quality_level
                })

        # 10. 更新电鱼的CD时间并保存
        thief.last_electric_fish_time = now
        self.user_repo.update(thief)

        # 11. 生成成功消息
        counter_message = ""
        if protection_buff:
            if penetration_buff:
                counter_message = "破灵符的力量穿透了海灵守护！\n"
            elif shadow_cloak_buff:
                counter_message = "🌑 暗影斗篷让你在阴影中行动！\n"

        stolen_details = "、".join(stolen_summary)
        actual_stolen_count = len(final_stolen_fish)

        # 计算收益占比
        steal_percentage = (actual_stolen_count / total_fish_count) * 100

        return {
            "success": True,
            "message": f"{counter_message}{success_type}！成功对【{victim.nickname}】的鱼塘进行了电击，捕获了{actual_stolen_count}条鱼（占其总数的{steal_percentage:.1f}%），总价值 {total_value_stolen} 金币！\n分别是：{stolen_details}。\n💡 本次成功率为 {final_success_rate*100:.1f}%",
            "stolen_fish": stolen_fish_details,
        }
    # ============================================================
    # ===================== 新增功能：电鱼 结束 =====================
    # ============================================================

    def dispel_steal_protection(self, target_id: str) -> Dict[str, Any]:
        """
        驱散目标的海灵守护效果
        """
        target = self.user_repo.get_by_id(target_id)
        if not target:
            return {"success": False, "message": "目标用户不存在"}

        protection_buff = self.buff_repo.get_active_by_user_and_type(
            target_id, "STEAL_PROTECTION_BUFF"
        )
        
        if not protection_buff:
            return {"success": False, "message": f"【{target.nickname}】没有海灵守护效果"}
        
        self.buff_repo.delete(protection_buff.id)
        
        return {
            "success": True, 
            "message": f"成功驱散了【{target.nickname}】的海灵守护效果"
        }

    def check_steal_protection(self, target_id: str) -> Dict[str, Any]:
        """
        检查目标是否有海灵守护效果
        """
        target = self.user_repo.get_by_id(target_id)
        if not target:
            return {"has_protection": False, "target_name": "未知用户", "message": "目标用户不存在"}

        protection_buff = self.buff_repo.get_active_by_user_and_type(
            target_id, "STEAL_PROTECTION_BUFF"
        )
        
        return {
            "has_protection": protection_buff is not None,
            "target_name": target.nickname,
            "message": f"【{target.nickname}】{'有' if protection_buff else '没有'}海灵守护效果"
        }

    def calculate_sell_price(self, item_type: str, rarity: int, refine_level: int) -> int:
        """
        计算物品的系统售价。

        Args:
            item_type: 物品类型 ('rod', 'accessory')
            rarity: 物品稀有度
            refine_level: 物品精炼等级

        Returns:
            计算出的售价。
        """
        sell_price_config = self.config.get("sell_prices", {})
        
        base_prices = sell_price_config.get(item_type, {})
        base_price = base_prices.get(str(rarity), 0)

        # 如果配置中没有该稀有度的基础价格，使用基于稀有度的公式计算默认值
        # 公式：基础价 = 100 * (2.5 ^ (rarity - 1))，确保高稀有度物品有合理的价格
        if base_price <= 0:
            # 使用指数增长公式：1星=100, 2星≈250, 3星≈625, 4星≈1562, 5星≈3906, 6星≈9765, 7星≈24414, 8星≈61035, 9星≈152587, 10星≈381469
            base_price = int(100 * (2.5 ** (rarity - 1)))
            # 确保最低价格为 100
            base_price = max(100, base_price)

        refine_multipliers = sell_price_config.get("refine_multiplier", {})
        refine_multiplier = refine_multipliers.get(str(refine_level), 1.0)

        final_price = int(base_price * refine_multiplier)

        # 确保最终价格至少为 30 金币（防止计算错误导致负值或零值）
        if final_price <= 0:
            return 30  # 默认最低价格

        return final_price

    # ============================================================
    # ==================== 新增功能：骰宝 (大小) 开始 ====================
    # ============================================================
    def play_sicbo(self, user_id: str, bet_type: str, amount: int) -> Dict[str, Any]:
        """处理骰宝（押大小）游戏的核心逻辑"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "❌ 用户不存在。"}

        # 1. 冷却时间检查 (例如：5秒)
        cooldown_seconds = 5
        now = get_now()
        if user.last_sicbo_time and (now - user.last_sicbo_time).total_seconds() < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - user.last_sicbo_time).total_seconds())
            return {"success": False, "message": f"⏳ 操作太快了，请等待 {remaining} 秒后再试。"}

        # 2. 验证下注
        valid_bets = ['大', '小']
        if bet_type not in valid_bets:
            return {"success": False, "message": "❌ 押注类型错误！只能押 `大` 或 `小`。"}
        if amount <= 0:
            return {"success": False, "message": "❌ 押注金额必须大于0！"}
        if not user.can_afford(amount):
            return {"success": False, "message": f"💰 你的金币不足！当前拥有 {user.coins:,} 金币。"}

        # 3. 扣除押金并开始游戏
        user.coins -= amount
        
        # 4. 投掷三个骰子
        dice = [random.randint(1, 6) for _ in range(3)]
        total = sum(dice)
        
        # 5. 判断结果
        is_triple = (dice[0] == dice[1] == dice[2])
        
        if 4 <= total <= 10:
            result_type = '小'
        elif 11 <= total <= 17:
            result_type = '大'
        else: # 只有豹子会落到这个区间外
            result_type = '豹子'

        # 6. 判断输赢
        # 规则：如果开出豹子，庄家通吃
        win = False
        if not is_triple and bet_type == result_type:
            win = True

        # 7. 结算
        profit = 0
        if win:
            winnings = amount * 2 # 1:1赔率，返还本金+1倍奖金
            profit = amount
            user.coins += winnings
        else:
            profit = -amount # 输了，损失本金

        # 8. 更新用户状态并保存
        user.last_sicbo_time = now
        self.user_repo.update(user)

        # 9. 返回详细的游戏结果
        return {
            "success": True,
            "win": win,
            "dice": dice,
            "total": total,
            "result_type": result_type,
            "is_triple": is_triple,
            "profit": profit,
            "new_balance": user.coins
        }