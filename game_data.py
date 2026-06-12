from sqlalchemy.orm import Session
from models import ClassData, Item, Skill, Enemy, Quest, Dialogue, Achievement


def init_game_data(db: Session):
    init_classes(db)
    init_items(db)
    init_skills(db)
    init_enemies(db)
    init_quests(db)
    init_dialogues(db)
    init_achievements(db)
    db.commit()


def init_classes(db: Session):
    classes = [
        {
            "class_name": "战士",
            "description": "高血量高防御的近战职业，擅长使用剑盾",
            "base_hp": 150,
            "base_mp": 30,
            "base_attack": 12,
            "base_defense": 8,
            "base_speed": 4,
            "hp_per_level": 15,
            "mp_per_level": 3,
            "attack_per_level": 3,
            "defense_per_level": 2,
            "speed_per_level": 1,
        },
        {
            "class_name": "法师",
            "description": "高魔法伤害的远程职业，擅长使用法杖",
            "base_hp": 80,
            "base_mp": 100,
            "base_attack": 6,
            "base_defense": 3,
            "base_speed": 5,
            "hp_per_level": 8,
            "mp_per_level": 12,
            "attack_per_level": 1,
            "defense_per_level": 1,
            "speed_per_level": 1,
        },
        {
            "class_name": "弓箭手",
            "description": "高攻速高暴击的远程职业，擅长使用弓箭",
            "base_hp": 100,
            "base_mp": 60,
            "base_attack": 14,
            "base_defense": 4,
            "base_speed": 8,
            "hp_per_level": 10,
            "mp_per_level": 6,
            "attack_per_level": 4,
            "defense_per_level": 1,
            "speed_per_level": 2,
        },
        {
            "class_name": "刺客",
            "description": "高爆发高闪避的近战职业，擅长使用匕首",
            "base_hp": 90,
            "base_mp": 50,
            "base_attack": 16,
            "base_defense": 3,
            "base_speed": 10,
            "hp_per_level": 9,
            "mp_per_level": 5,
            "attack_per_level": 5,
            "defense_per_level": 1,
            "speed_per_level": 3,
        },
    ]
    for c in classes:
        if not db.query(ClassData).filter_by(class_name=c["class_name"]).first():
            db.add(ClassData(**c))


def init_items(db: Session):
    items = [
        {"id": 1, "name": "生命药水", "description": "恢复50点生命值", "type": "consumable", "sub_type": "potion", "rarity": "common", "price": 20, "stats": {"heal_hp": 50}, "required_level": 1, "stackable": True, "max_stack": 99, "is_equipment": False},
        {"id": 2, "name": "魔法药水", "description": "恢复30点魔法值", "type": "consumable", "sub_type": "potion", "rarity": "common", "price": 30, "stats": {"heal_mp": 30}, "required_level": 1, "stackable": True, "max_stack": 99, "is_equipment": False},
        {"id": 3, "name": "大生命药水", "description": "恢复200点生命值", "type": "consumable", "sub_type": "potion", "rarity": "uncommon", "price": 80, "stats": {"heal_hp": 200}, "required_level": 5, "stackable": True, "max_stack": 99, "is_equipment": False},
        {"id": 11, "name": "铁剑", "description": "普通的铁制长剑，攻击+5", "type": "equipment", "sub_type": "weapon", "rarity": "common", "price": 100, "stats": {"attack": 5}, "required_level": 1, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "weapon"},
        {"id": 12, "name": "钢剑", "description": "精钢打造的长剑，攻击+12", "type": "equipment", "sub_type": "weapon", "rarity": "uncommon", "price": 300, "stats": {"attack": 12}, "required_level": 5, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "weapon"},
        {"id": 13, "name": "火焰之刃", "description": "附魔火焰的魔法剑，攻击+25，附带灼烧效果", "type": "equipment", "sub_type": "weapon", "rarity": "rare", "price": 1000, "stats": {"attack": 25, "fire_damage": 5}, "required_level": 15, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "weapon"},
        {"id": 21, "name": "木杖", "description": "普通的木杖，攻击+3，魔法+5", "type": "equipment", "sub_type": "weapon", "rarity": "common", "price": 80, "stats": {"attack": 3, "max_mp": 5}, "required_level": 1, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "weapon"},
        {"id": 22, "name": "魔法杖", "description": "蕴含魔力的法杖，攻击+8，魔法+20", "type": "equipment", "sub_type": "weapon", "rarity": "uncommon", "price": 280, "stats": {"attack": 8, "max_mp": 20}, "required_level": 5, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "weapon"},
        {"id": 31, "name": "皮甲", "description": "轻便的皮制护甲，防御+5", "type": "equipment", "sub_type": "armor", "rarity": "common", "price": 120, "stats": {"defense": 5}, "required_level": 1, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "armor"},
        {"id": 32, "name": "锁子甲", "description": "坚固的锁子甲，防御+12", "type": "equipment", "sub_type": "armor", "rarity": "uncommon", "price": 350, "stats": {"defense": 12, "max_hp": 20}, "required_level": 5, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "armor"},
        {"id": 33, "name": "板甲", "description": "重型板甲，防御+25，速度-2", "type": "equipment", "sub_type": "armor", "rarity": "rare", "price": 1200, "stats": {"defense": 25, "max_hp": 50, "speed": -2}, "required_level": 15, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "armor"},
        {"id": 41, "name": "铁盾", "description": "小型铁盾，防御+3，生命+10", "type": "equipment", "sub_type": "shield", "rarity": "common", "price": 150, "stats": {"defense": 3, "max_hp": 10}, "required_level": 1, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "shield"},
        {"id": 51, "name": "力量戒指", "description": "提升力量的戒指，攻击+5", "type": "equipment", "sub_type": "accessory", "rarity": "uncommon", "price": 200, "stats": {"attack": 5}, "required_level": 3, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "accessory"},
        {"id": 52, "name": "生命吊坠", "description": "提升生命上限的吊坠，生命+30", "type": "equipment", "sub_type": "accessory", "rarity": "uncommon", "price": 220, "stats": {"max_hp": 30}, "required_level": 3, "stackable": False, "max_stack": 1, "is_equipment": True, "slot": "accessory"},
        {"id": 101, "name": "史莱姆黏液", "description": "史莱姆掉落的黏液，可用于炼金", "type": "material", "sub_type": "monster_drop", "rarity": "common", "price": 5, "required_level": 1, "stackable": True, "max_stack": 99, "is_equipment": False},
        {"id": 102, "name": "狼人皮毛", "description": "狼人掉落的皮毛，可用于制作装备", "type": "material", "sub_type": "monster_drop", "rarity": "uncommon", "price": 30, "required_level": 5, "stackable": True, "max_stack": 99, "is_equipment": False},
    ]
    for i in items:
        if not db.query(Item).filter_by(id=i["id"]).first():
            db.add(Item(**i))


def init_skills(db: Session):
    skills = [
        {"id": 1, "name": "重击", "description": "战士的基础技能，造成150%攻击力伤害", "class_name": "战士", "damage": 1.5, "mp_cost": 10, "cooldown": 1, "required_level": 1, "effect_type": "damage", "target_type": "single"},
        {"id": 2, "name": "旋风斩", "description": "挥舞武器攻击所有敌人，造成100%攻击力伤害", "class_name": "战士", "damage": 1.0, "mp_cost": 20, "cooldown": 3, "required_level": 5, "effect_type": "damage", "target_type": "all"},
        {"id": 3, "name": "防御姿态", "description": "进入防御姿态，本回合受到伤害减半", "class_name": "战士", "mp_cost": 15, "cooldown": 4, "required_level": 10, "effect_type": "buff", "target_type": "self"},
        {"id": 11, "name": "火球术", "description": "发射一个火球，造成200%攻击力的魔法伤害", "class_name": "法师", "damage": 2.0, "mp_cost": 15, "cooldown": 1, "required_level": 1, "effect_type": "damage", "target_type": "single"},
        {"id": 12, "name": "冰冻术", "description": "冰冻敌人，造成120%伤害并有几率冻结", "class_name": "法师", "damage": 1.2, "mp_cost": 20, "cooldown": 2, "required_level": 5, "effect_type": "damage", "target_type": "single"},
        {"id": 13, "name": "治疗术", "description": "恢复30%最大生命值", "class_name": "法师", "heal": 0.3, "mp_cost": 25, "cooldown": 3, "required_level": 3, "effect_type": "heal", "target_type": "self"},
        {"id": 21, "name": "精准射击", "description": "精准射击敌人要害，造成180%攻击力伤害", "class_name": "弓箭手", "damage": 1.8, "mp_cost": 12, "cooldown": 1, "required_level": 1, "effect_type": "damage", "target_type": "single"},
        {"id": 22, "name": "连射", "description": "连续射出3支箭，每支造成60%攻击力伤害", "class_name": "弓箭手", "damage": 0.6, "mp_cost": 18, "cooldown": 2, "required_level": 5, "effect_type": "damage", "target_type": "single"},
        {"id": 23, "name": "毒箭", "description": "射出毒箭，造成100%伤害并使敌人中毒3回合", "class_name": "弓箭手", "damage": 1.0, "mp_cost": 20, "cooldown": 3, "required_level": 8, "effect_type": "damage", "target_type": "single"},
        {"id": 31, "name": "背刺", "description": "从背后攻击敌人，造成250%攻击力伤害", "class_name": "刺客", "damage": 2.5, "mp_cost": 15, "cooldown": 1, "required_level": 1, "effect_type": "damage", "target_type": "single"},
        {"id": 32, "name": "影袭", "description": "瞬移到敌人身边攻击，造成150%伤害并提升闪避", "class_name": "刺客", "damage": 1.5, "mp_cost": 20, "cooldown": 2, "required_level": 5, "effect_type": "damage", "target_type": "single"},
        {"id": 33, "name": "致命一击", "description": "使出致命一击，造成400%攻击力伤害", "class_name": "刺客", "damage": 4.0, "mp_cost": 35, "cooldown": 5, "required_level": 15, "effect_type": "damage", "target_type": "single"},
    ]
    for s in skills:
        if not db.query(Skill).filter_by(id=s["id"]).first():
            db.add(Skill(**s))


def init_enemies(db: Session):
    enemies = [
        {"id": 1, "name": "史莱姆", "description": "最弱的怪物，软软的绿色生物", "level": 1, "max_hp": 30, "attack": 5, "defense": 1, "speed": 2, "exp_reward": 10, "gold_reward": 5, "loot_table": [{"item_id": 101, "chance": 0.8, "quantity": 1}]},
        {"id": 2, "name": "哥布林", "description": "狡猾的小型怪物，经常成群出现", "level": 3, "max_hp": 50, "attack": 10, "defense": 3, "speed": 5, "exp_reward": 25, "gold_reward": 15, "loot_table": [{"item_id": 1, "chance": 0.3, "quantity": 1}]},
        {"id": 3, "name": "野狼", "description": "凶猛的野狼，攻击速度很快", "level": 5, "max_hp": 80, "attack": 15, "defense": 5, "speed": 8, "exp_reward": 40, "gold_reward": 25, "loot_table": [{"item_id": 2, "chance": 0.2, "quantity": 1}]},
        {"id": 4, "name": "兽人战士", "description": "强壮的兽人，力大无穷", "level": 8, "max_hp": 150, "attack": 22, "defense": 10, "speed": 4, "exp_reward": 80, "gold_reward": 50, "loot_table": [{"item_id": 11, "chance": 0.1, "quantity": 1}, {"item_id": 31, "chance": 0.1, "quantity": 1}]},
        {"id": 5, "name": "狼人", "description": "半人半狼的怪物，攻击力很高", "level": 10, "max_hp": 200, "attack": 30, "defense": 12, "speed": 10, "exp_reward": 120, "gold_reward": 80, "loot_table": [{"item_id": 102, "chance": 0.5, "quantity": 1}, {"item_id": 12, "chance": 0.05, "quantity": 1}]},
        {"id": 6, "name": "石像鬼", "description": "会飞的石头怪物，防御很高", "level": 12, "max_hp": 180, "attack": 25, "defense": 20, "speed": 6, "exp_reward": 150, "gold_reward": 100, "loot_table": [{"item_id": 32, "chance": 0.08, "quantity": 1}]},
        {"id": 7, "name": "黑暗法师", "description": "堕落的法师，会使用黑暗魔法", "level": 15, "max_hp": 160, "attack": 40, "defense": 8, "speed": 7, "exp_reward": 200, "gold_reward": 150, "loot_table": [{"item_id": 22, "chance": 0.1, "quantity": 1}, {"item_id": 3, "chance": 0.3, "quantity": 1}]},
        {"id": 8, "name": "巨龙", "description": "传说中的巨龙，极其强大", "level": 20, "max_hp": 500, "attack": 60, "defense": 30, "speed": 8, "exp_reward": 500, "gold_reward": 500, "loot_table": [{"item_id": 13, "chance": 0.2, "quantity": 1}, {"item_id": 33, "chance": 0.2, "quantity": 1}]},
    ]
    for e in enemies:
        if not db.query(Enemy).filter_by(id=e["id"]).first():
            db.add(Enemy(**e))


def init_quests(db: Session):
    quests = [
        {"id": 1, "name": "初入冒险", "description": "击败3只史莱姆，证明你的实力", "type": "main", "chapter": 1, "required_level": 1, "exp_reward": 50, "gold_reward": 30, "item_rewards": [{"item_id": 1, "quantity": 3}]},
        {"id": 2, "name": "村庄保卫战", "description": "击退骚扰村庄的哥布林，击败5只", "type": "main", "chapter": 1, "required_level": 2, "exp_reward": 100, "gold_reward": 80, "item_rewards": [{"item_id": 2, "quantity": 2}], "pre_quest_id": 1},
        {"id": 3, "name": "森林狩猎", "description": "前往迷雾森林，消灭4只野狼", "type": "main", "chapter": 2, "required_level": 4, "exp_reward": 200, "gold_reward": 150, "item_rewards": [{"item_id": 11, "quantity": 1}], "pre_quest_id": 2},
        {"id": 4, "name": "兽人营地", "description": "突袭兽人营地，击败3个兽人战士", "type": "main", "chapter": 3, "required_level": 7, "exp_reward": 350, "gold_reward": 250, "item_rewards": [{"item_id": 31, "quantity": 1}], "pre_quest_id": 3},
        {"id": 5, "name": "狼人之祸", "description": "调查狼人出没事件，击败5只狼人", "type": "main", "chapter": 4, "required_level": 9, "exp_reward": 500, "gold_reward": 400, "item_rewards": [{"item_id": 12, "quantity": 1}], "pre_quest_id": 4},
        {"id": 6, "name": "山脉探险", "description": "穿越黑暗山脉，击败3只石像鬼", "type": "main", "chapter": 5, "required_level": 11, "exp_reward": 700, "gold_reward": 500, "item_rewards": [{"item_id": 32, "quantity": 1}], "pre_quest_id": 5},
        {"id": 7, "name": "黑暗教团", "description": "击败黑暗法师，阻止他的邪恶计划", "type": "main", "chapter": 6, "required_level": 14, "exp_reward": 1000, "gold_reward": 800, "item_rewards": [{"item_id": 22, "quantity": 1}], "pre_quest_id": 6},
        {"id": 8, "name": "最终决战", "description": "挑战远古巨龙，拯救世界！", "type": "main", "chapter": 7, "required_level": 18, "exp_reward": 2000, "gold_reward": 2000, "item_rewards": [{"item_id": 13, "quantity": 1}, {"item_id": 33, "quantity": 1}], "pre_quest_id": 7},
        {"id": 101, "name": "收集药水", "description": "收集5瓶生命药水", "type": "side", "chapter": 1, "required_level": 1, "exp_reward": 30, "gold_reward": 20},
        {"id": 102, "name": "材料收集", "description": "收集10个史莱姆黏液", "type": "side", "chapter": 1, "required_level": 1, "exp_reward": 40, "gold_reward": 30},
    ]
    for q in quests:
        if not db.query(Quest).filter_by(id=q["id"]).first():
            db.add(Quest(**q))


def init_dialogues(db: Session):
    dialogues = [
        {
            "id": 1,
            "npc_id": 1,
            "chapter": 1,
            "content": "欢迎来到冒险世界，年轻的冒险者！我是村长，你愿意帮助我们的村庄吗？",
            "choices": [
                {"id": 1, "text": "我愿意帮助你们！", "branch_path": "main_help", "next_dialogue": 2},
                {"id": 2, "text": "让我先考虑一下...", "branch_path": "neutral_wait", "next_dialogue": 3},
                {"id": 3, "text": "没兴趣，我要走了", "branch_path": "refuse_leave", "next_dialogue": 4}
            ]
        },
        {
            "id": 2,
            "npc_id": 1,
            "chapter": 1,
            "content": "太好了！最近史莱姆在村外骚扰村民，请你去击败3只，我会给你丰厚的奖励。",
            "choices": [
                {"id": 1, "text": "没问题，交给我！", "branch_path": "accept_quest", "quest_id": 1},
                {"id": 2, "text": "我需要准备一下", "branch_path": "prepare"}
            ]
        },
        {
            "id": 3,
            "npc_id": 1,
            "chapter": 1,
            "content": "没关系，你可以先四处看看。不过史莱姆的问题越来越严重了，希望你能尽快决定。",
            "choices": [
                {"id": 1, "text": "好的，我决定帮忙！", "branch_path": "accept_quest", "next_dialogue": 2},
                {"id": 2, "text": "我再想想", "branch_path": "think_more"}
            ]
        },
        {
            "id": 4,
            "npc_id": 1,
            "chapter": 1,
            "content": "唉...如果你改变主意了，随时回来找我。村庄需要英雄。",
            "choices": [
                {"id": 1, "text": "等等，我愿意帮忙", "branch_path": "change_mind", "next_dialogue": 2},
                {"id": 2, "text": "再见", "branch_path": "goodbye"}
            ]
        },
        {
            "id": 5,
            "npc_id": 2,
            "chapter": 2,
            "content": "你终于来了！森林深处出现了很多野狼，猎人们都不敢去打猎了。",
            "choices": [
                {"id": 1, "text": "我去解决它们！", "branch_path": "accept_wolf_quest", "quest_id": 3},
                {"id": 2, "text": "有什么奖励吗？", "branch_path": "ask_reward"}
            ]
        },
    ]
    for d in dialogues:
        if not db.query(Dialogue).filter_by(id=d["id"]).first():
            db.add(Dialogue(**d))


def init_achievements(db: Session):
    achievements = [
        {"id": 1, "name": "初出茅庐", "description": "等级达到5级", "category": "level", "condition_type": "level", "condition_value": 5, "exp_reward": 100, "gold_reward": 100, "is_rare": False},
        {"id": 2, "name": "小有名气", "description": "等级达到10级", "category": "level", "condition_type": "level", "condition_value": 10, "exp_reward": 300, "gold_reward": 300, "is_rare": False},
        {"id": 3, "name": "冒险达人", "description": "等级达到15级", "category": "level", "condition_type": "level", "condition_value": 15, "exp_reward": 500, "gold_reward": 500, "is_rare": True},
        {"id": 4, "name": "传说英雄", "description": "等级达到20级", "category": "level", "condition_type": "level", "condition_value": 20, "exp_reward": 1000, "gold_reward": 1000, "is_rare": True},
        {"id": 11, "name": "首次击杀", "description": "击败第1个敌人", "category": "combat", "condition_type": "kill_count", "condition_value": 1, "exp_reward": 20, "gold_reward": 20, "is_rare": False},
        {"id": 12, "name": "百人斩", "description": "累计击败100个敌人", "category": "combat", "condition_type": "kill_count", "condition_value": 100, "exp_reward": 200, "gold_reward": 200, "is_rare": False},
        {"id": 13, "name": "千人斩", "description": "累计击败1000个敌人", "category": "combat", "condition_type": "kill_count", "condition_value": 1000, "exp_reward": 800, "gold_reward": 800, "is_rare": True},
        {"id": 21, "name": "初识财富", "description": "累计获得1000金币", "category": "wealth", "condition_type": "total_gold", "condition_value": 1000, "exp_reward": 50, "gold_reward": 100, "is_rare": False},
        {"id": 22, "name": "富甲一方", "description": "累计获得10000金币", "category": "wealth", "condition_type": "total_gold", "condition_value": 10000, "exp_reward": 300, "gold_reward": 500, "is_rare": True},
        {"id": 31, "name": "任务新手", "description": "完成5个任务", "category": "quest", "condition_type": "quest_completed", "condition_value": 5, "exp_reward": 100, "gold_reward": 100, "is_rare": False},
        {"id": 32, "name": "任务大师", "description": "完成50个任务", "category": "quest", "condition_type": "quest_completed", "condition_value": 50, "exp_reward": 500, "gold_reward": 500, "is_rare": True},
        {"id": 41, "name": "屠龙勇士", "description": "击败巨龙", "category": "boss", "condition_type": "boss_kill", "condition_value": 8, "exp_reward": 1000, "gold_reward": 1000, "item_reward": {"item_id": 51, "quantity": 1}, "is_rare": True},
        {"id": 51, "name": "快速通关", "description": "5小时内通关游戏", "category": "speedrun", "condition_type": "clear_time", "condition_value": 18000, "exp_reward": 1000, "gold_reward": 1000, "is_rare": True},
        {"id": 52, "name": "完美通关", "description": "完成所有主线任务", "category": "completion", "condition_type": "main_quest_clear", "condition_value": 8, "exp_reward": 1500, "gold_reward": 1500, "is_rare": True},
    ]
    for a in achievements:
        if not db.query(Achievement).filter_by(id=a["id"]).first():
            db.add(Achievement(**a))
