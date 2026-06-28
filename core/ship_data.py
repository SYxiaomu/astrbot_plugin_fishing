"""
船舶初始数据
"""
SHIP_DATA = [
    # Format: (name, level, description, cost_coins, required_fish, max_ocean_zone_level)
    ("独木舟", 1, "最简陋的水上工具，勉强能出海。", 10000, '[{"fish_tag":"tropical_rainforest","quantity":5}]', 1),
    ("小渔船", 2, "木质渔船，适合近海作业。", 50000, '[{"fish_tag":"subtropical_estuary","quantity":10}]', 2),
    ("机动渔船", 3, "装备了发动机的渔船，航程更远。", 200000, '[{"fish_tag":"temperate_lake","quantity":15}]', 3),
    ("远洋渔船", 4, "大型远洋捕捞船，能到达深海区域。", 1000000, '[{"fish_tag":"cold_fjord","quantity":20}]', 4),
    ("极地破冰船", 5, "专为极寒海域设计的特种船只。", 5000000, '[{"fish_tag":"oceanic_ridge","quantity":25}]', 5),
]
