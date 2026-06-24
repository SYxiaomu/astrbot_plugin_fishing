from .base import BaseAchievement, UserContext

class TotalCoinsEarned1M(BaseAchievement):
    id = 12 # 对应原数据库中的 achievement_id
    name = "富可敌国"
    description = "累计赚取1,000,000金币"
    target_value = 1000000
    reward = ("title", 5, 1) # 奖励 "百万富翁" 称号

    def get_progress(self, context: UserContext) -> int:
        """返回用户累计获得的金币数作为当前进度。"""
        return context.user.total_coins_earned

    def check(self, context: UserContext) -> bool:
        return context.user.total_coins_earned >= 1000000