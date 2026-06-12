import hashlib
import random
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from models import Player, Character, ClassData, Inventory, Equipment, PlayerQuest, PlayerAchievement, Achievement, Skill, SkillCooldown, Item, Enemy


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def get_exp_required(level: int) -> int:
    return int(100 * (level ** 1.5))


def check_level_up(player: Player) -> list:
    level_ups = []
    while True:
        exp_required = get_exp_required(player.level)
        if player.exp >= exp_required:
            player.exp -= exp_required
            player.level += 1
            level_ups.append(player.level)
        else:
            break
    return level_ups


def create_character_for_player(db: Session, player_id: int, name: str, class_name: str) -> Character:
    class_data = db.query(ClassData).filter_by(class_name=class_name).first()
    if not class_data:
        raise ValueError(f"职业 {class_name} 不存在")
    
    character = Character(
        player_id=player_id,
        name=name,
        class_name=class_name,
        max_hp=class_data.base_hp,
        current_hp=class_data.base_hp,
        max_mp=class_data.base_mp,
        current_mp=class_data.base_mp,
        attack=class_data.base_attack,
        defense=class_data.base_defense,
        speed=class_data.base_speed
    )
    db.add(character)
    db.flush()
    
    starter_skills = db.query(Skill).filter_by(class_name=class_name, required_level=1).all()
    for skill in starter_skills:
        from models import CharacterSkill
        cs = CharacterSkill(character_id=character.id, skill_id=skill.id)
        db.add(cs)
    
    return character


def add_item_to_inventory(db: Session, player_id: int, item_id: int, quantity: int = 1) -> Inventory:
    item = db.query(Item).filter_by(id=item_id).first()
    if not item:
        raise ValueError(f"物品 {item_id} 不存在")
    
    if item.stackable:
        existing = db.query(Inventory).filter_by(player_id=player_id, item_id=item_id).first()
        if existing:
            existing.quantity = min(existing.quantity + quantity, item.max_stack)
            return existing
    
    inv = Inventory(player_id=player_id, item_id=item_id, quantity=quantity)
    db.add(inv)
    return inv


def remove_item_from_inventory(db: Session, player_id: int, item_id: int, quantity: int = 1) -> bool:
    inv = db.query(Inventory).filter_by(player_id=player_id, item_id=item_id).first()
    if not inv or inv.quantity < quantity:
        return False
    
    inv.quantity -= quantity
    if inv.quantity <= 0:
        db.delete(inv)
    return True


def get_equipment_stats(db: Session, player_id: int, character_id: int) -> dict:
    stats = {"attack": 0, "defense": 0, "max_hp": 0, "max_mp": 0, "speed": 0}
    equipment = db.query(Equipment).filter_by(player_id=player_id, character_id=character_id).all()
    
    for eq in equipment:
        if eq.item and eq.item.stats:
            for key, value in eq.item.stats.items():
                if key in stats:
                    stats[key] += value
    return stats


def calculate_skill_effect(skill: Skill, character: Character, equipment_stats: dict) -> dict:
    base_attack = character.attack + equipment_stats.get("attack", 0)
    damage = int(base_attack * skill.damage) if skill.damage > 0 else 0
    heal = int(character.max_hp * skill.heal) if skill.heal > 0 else 0
    
    return {
        "damage": damage,
        "heal": heal,
        "mp_cost": skill.mp_cost,
        "cooldown": skill.cooldown,
        "effect_type": skill.effect_type
    }


def generate_battle_id() -> str:
    return str(uuid.uuid4())


def process_battle(db: Session, player: Player, character: Character, enemy: Enemy, skill_id: int = None) -> dict:
    battle_log = []
    cooldowns = {}
    
    equipment_stats = get_equipment_stats(db, player.id, character.id)
    
    player_current_hp = character.current_hp
    player_current_mp = character.current_mp
    player_max_hp = character.max_hp + equipment_stats.get("max_hp", 0)
    player_max_mp = character.max_mp + equipment_stats.get("max_mp", 0)
    player_attack = character.attack + equipment_stats.get("attack", 0)
    player_defense = character.defense + equipment_stats.get("defense", 0)
    player_speed = character.speed + equipment_stats.get("speed", 0)
    
    enemy_current_hp = enemy.max_hp
    
    active_cooldowns = db.query(SkillCooldown).filter_by(
        player_id=player.id, character_id=character.id
    ).all()
    
    for cd in active_cooldowns:
        if cd.remaining_turns > 0:
            cooldowns[str(cd.skill_id)] = cd.remaining_turns
    
    player_turn = player_speed >= enemy.speed
    
    victory = False
    round_num = 1
    skill_used_this_battle = False
    
    while player_current_hp > 0 and enemy_current_hp > 0 and round_num <= 50:
        battle_log.append(f"--- 第 {round_num} 回合 ---")
        
        if player_turn:
            if skill_id and player_current_mp > 0 and not skill_used_this_battle:
                skill = db.query(Skill).filter_by(id=skill_id).first()
                char_skill = db.query(Character).filter_by(id=character.id).first()
                
                if skill and char_skill:
                    from models import CharacterSkill
                    has_skill = db.query(CharacterSkill).filter_by(
                        character_id=character.id, skill_id=skill_id
                    ).first()
                    
                    cd_remaining = cooldowns.get(str(skill_id), 0)
                    
                    if has_skill and cd_remaining <= 0:
                        effect = calculate_skill_effect(skill, character, equipment_stats)
                        
                        if player_current_mp >= effect["mp_cost"]:
                            player_current_mp -= effect["mp_cost"]
                            
                            if effect["effect_type"] == "damage":
                                actual_damage = max(1, effect["damage"] - enemy.defense)
                                enemy_current_hp -= actual_damage
                                battle_log.append(f"{character.name} 使用 {skill.name}，对 {enemy.name} 造成 {actual_damage} 点伤害！")
                            
                            elif effect["effect_type"] == "heal":
                                heal_amount = min(effect["heal"], player_max_hp - player_current_hp)
                                player_current_hp += heal_amount
                                battle_log.append(f"{character.name} 使用 {skill.name}，恢复了 {heal_amount} 点生命！")
                            
                            if effect["cooldown"] > 0:
                                existing_cd = db.query(SkillCooldown).filter_by(
                                    player_id=player.id, character_id=character.id,
                                    skill_id=skill_id
                                ).first()
                                if existing_cd:
                                    existing_cd.remaining_turns = effect["cooldown"]
                                else:
                                    cd = SkillCooldown(
                                        player_id=player.id,
                                        character_id=character.id,
                                        skill_id=skill_id,
                                        remaining_turns=effect["cooldown"]
                                    )
                                    db.add(cd)
                                cooldowns[str(skill_id)] = effect["cooldown"]
                            
                            skill_used_this_battle = True
                        else:
                            basic_damage = max(1, player_attack - enemy.defense)
                            enemy_current_hp -= basic_damage
                            battle_log.append(f"魔法不足！{character.name} 进行普通攻击，对 {enemy.name} 造成 {basic_damage} 点伤害！")
                    else:
                        if cd_remaining > 0:
                            battle_log.append(f"{skill.name} 冷却中，剩余 {cd_remaining} 回合，只能普通攻击")
                        basic_damage = max(1, player_attack - enemy.defense)
                        enemy_current_hp -= basic_damage
                        battle_log.append(f"{character.name} 进行普通攻击，对 {enemy.name} 造成 {basic_damage} 点伤害！")
            else:
                basic_damage = max(1, player_attack - enemy.defense)
                enemy_current_hp -= basic_damage
                battle_log.append(f"{character.name} 进行普通攻击，对 {enemy.name} 造成 {basic_damage} 点伤害！")
            
            if enemy_current_hp <= 0:
                victory = True
                battle_log.append(f"{enemy.name} 被击败了！")
                break
        else:
            enemy_damage = max(1, enemy.attack - player_defense)
            player_current_hp -= enemy_damage
            battle_log.append(f"{enemy.name} 攻击 {character.name}，造成 {enemy_damage} 点伤害！")
            
            if player_current_hp <= 0:
                battle_log.append(f"{character.name} 倒下了...")
                break
        
        player_turn = not player_turn
        round_num += 1
        
        for key in list(cooldowns.keys()):
            if cooldowns[key] > 0:
                cooldowns[key] -= 1
                existing_cd = db.query(SkillCooldown).filter_by(
                    player_id=player.id, character_id=character.id,
                    skill_id=int(key)
                ).first()
                if existing_cd:
                    existing_cd.remaining_turns = cooldowns[key]
    
    exp_gained = enemy.exp_reward if victory else 0
    gold_gained = enemy.gold_reward if victory else 0
    items_gained = []
    
    if victory:
        player.exp += exp_gained
        player.gold += gold_gained
        character.current_hp = max(1, player_current_hp)
        character.current_mp = player_current_mp
        
        for loot in enemy.loot_table:
            if random.random() < loot.get("chance", 0):
                item_id = loot["item_id"]
                quantity = loot.get("quantity", 1)
                add_item_to_inventory(db, player.id, item_id, quantity)
                item = db.query(Item).filter_by(id=item_id).first()
                if item:
                    items_gained.append({
                        "item_id": item_id,
                        "item_name": item.name,
                        "quantity": quantity
                    })
        
        level_ups = check_level_up(player)
        for lv in level_ups:
            battle_log.append(f"恭喜！升级到 {lv} 级！")
            update_character_stats_on_level(db, character, 1)
        
        update_kill_achievement(db, player, enemy.id)
        update_combat_achievement(db, player)
        update_wealth_achievement(db, player)
    
    db.commit()
    
    final_cooldowns = {}
    for key, value in cooldowns.items():
        if value > 0:
            final_cooldowns[key] = value
    
    return {
        "victory": victory,
        "exp_gained": exp_gained,
        "gold_gained": gold_gained,
        "items_gained": items_gained,
        "player_hp": player_current_hp,
        "enemy_hp": max(0, enemy_current_hp),
        "battle_log": battle_log,
        "cooldowns": final_cooldowns
    }


def update_character_stats_on_level(db: Session, character: Character, levels: int = 1):
    class_data = db.query(ClassData).filter_by(class_name=character.class_name).first()
    if class_data:
        for _ in range(levels):
            character.level += 1
            character.max_hp += class_data.hp_per_level
            character.current_hp = character.max_hp
            character.max_mp += class_data.mp_per_level
            character.current_mp = character.max_mp
            character.attack += class_data.attack_per_level
            character.defense += class_data.defense_per_level
            character.speed += class_data.speed_per_level
            
            from models import Skill, CharacterSkill
            new_skills = db.query(Skill).filter(
                Skill.class_name == character.class_name,
                Skill.required_level == character.level
            ).all()
            for skill in new_skills:
                existing = db.query(CharacterSkill).filter_by(
                    character_id=character.id, skill_id=skill.id
                ).first()
                if not existing:
                    cs = CharacterSkill(character_id=character.id, skill_id=skill.id)
                    db.add(cs)


def update_level_achievement(db: Session, player: Player):
    achievements = db.query(Achievement).filter_by(condition_type="level").all()
    for ach in achievements:
        if player.level >= ach.condition_value:
            player_ach = db.query(PlayerAchievement).filter_by(
                player_id=player.id, achievement_id=ach.id
            ).first()
            if not player_ach:
                player_ach = PlayerAchievement(
                    player_id=player.id,
                    achievement_id=ach.id,
                    progress=player.level,
                    unlocked=True,
                    unlocked_at=datetime.now()
                )
                db.add(player_ach)
            elif not player_ach.unlocked:
                player_ach.unlocked = True
                player_ach.unlocked_at = datetime.now()
                player_ach.progress = player.level


def update_kill_achievement(db: Session, player: Player, enemy_id: int):
    achievements = db.query(Achievement).filter_by(condition_type="boss_kill").all()
    for ach in achievements:
        if enemy_id == ach.condition_value:
            player_ach = db.query(PlayerAchievement).filter_by(
                player_id=player.id, achievement_id=ach.id
            ).first()
            if not player_ach:
                player_ach = PlayerAchievement(
                    player_id=player.id,
                    achievement_id=ach.id,
                    progress=1,
                    unlocked=True,
                    unlocked_at=datetime.now()
                )
                db.add(player_ach)
            elif not player_ach.unlocked:
                player_ach.unlocked = True
                player_ach.unlocked_at = datetime.now()


def update_combat_achievement(db: Session, player: Player):
    achievements = db.query(Achievement).filter_by(condition_type="kill_count").all()
    for ach in achievements:
        player_ach = db.query(PlayerAchievement).filter_by(
            player_id=player.id, achievement_id=ach.id
        ).first()
        if not player_ach:
            player_ach = PlayerAchievement(
                player_id=player.id,
                achievement_id=ach.id,
                progress=1
            )
            db.add(player_ach)
        else:
            player_ach.progress += 1
        
        if player_ach.progress >= ach.condition_value and not player_ach.unlocked:
            player_ach.unlocked = True
            player_ach.unlocked_at = datetime.now()


def update_wealth_achievement(db: Session, player: Player):
    achievements = db.query(Achievement).filter_by(condition_type="total_gold").all()
    for ach in achievements:
        player_ach = db.query(PlayerAchievement).filter_by(
            player_id=player.id, achievement_id=ach.id
        ).first()
        if not player_ach:
            player_ach = PlayerAchievement(
                player_id=player.id,
                achievement_id=ach.id,
                progress=player.gold
            )
            db.add(player_ach)
        else:
            player_ach.progress = max(player_ach.progress, player.gold)
        
        if player_ach.progress >= ach.condition_value and not player_ach.unlocked:
            player_ach.unlocked = True
            player_ach.unlocked_at = datetime.now()


def update_quest_achievement(db: Session, player: Player):
    completed_count = db.query(PlayerQuest).filter_by(
        player_id=player.id, status="completed"
    ).count()
    
    achievements = db.query(Achievement).filter_by(condition_type="quest_completed").all()
    for ach in achievements:
        player_ach = db.query(PlayerAchievement).filter_by(
            player_id=player.id, achievement_id=ach.id
        ).first()
        if not player_ach:
            player_ach = PlayerAchievement(
                player_id=player.id,
                achievement_id=ach.id,
                progress=completed_count
            )
            db.add(player_ach)
        else:
            player_ach.progress = completed_count
        
        if player_ach.progress >= ach.condition_value and not player_ach.unlocked:
            player_ach.unlocked = True
            player_ach.unlocked_at = datetime.now()


def update_main_quest_achievement(db: Session, player: Player):
    from models import Quest
    main_quests = db.query(Quest).filter_by(type="main").all()
    completed_main = db.query(PlayerQuest).join(Quest).filter(
        PlayerQuest.player_id == player.id,
        PlayerQuest.status == "completed",
        Quest.type == "main"
    ).count()
    
    achievements = db.query(Achievement).filter_by(condition_type="main_quest_clear").all()
    for ach in achievements:
        player_ach = db.query(PlayerAchievement).filter_by(
            player_id=player.id, achievement_id=ach.id
        ).first()
        if not player_ach:
            player_ach = PlayerAchievement(
                player_id=player.id,
                achievement_id=ach.id,
                progress=completed_main
            )
            db.add(player_ach)
        else:
            player_ach.progress = completed_main
        
        if player_ach.progress >= ach.condition_value and not player_ach.unlocked:
            player_ach.unlocked = True
            player_ach.unlocked_at = datetime.now()


def update_speedrun_achievement(db: Session, player: Player):
    achievements = db.query(Achievement).filter_by(condition_type="clear_time").all()
    for ach in achievements:
        if player.play_time > 0 and player.play_time <= ach.condition_value:
            player_ach = db.query(PlayerAchievement).filter_by(
                player_id=player.id, achievement_id=ach.id
            ).first()
            if not player_ach:
                player_ach = PlayerAchievement(
                    player_id=player.id,
                    achievement_id=ach.id,
                    progress=player.play_time,
                    unlocked=True,
                    unlocked_at=datetime.now()
                )
                db.add(player_ach)


def can_claim_reward(db: Session, player_id: int, achievement_id: int) -> tuple:
    player_ach = db.query(PlayerAchievement).filter_by(
        player_id=player_id, achievement_id=achievement_id
    ).first()
    
    if not player_ach:
        return False, "成就未解锁"
    if not player_ach.unlocked:
        return False, "成就尚未达成"
    if player_ach.reward_claimed:
        return False, "奖励已领取，不能重复领取"
    
    return True, ""


def claim_achievement_reward(db: Session, player: Player, achievement_id: int) -> dict:
    can_claim, message = can_claim_reward(db, player.id, achievement_id)
    if not can_claim:
        return {"success": False, "reward": {}, "message": message}
    
    achievement = db.query(Achievement).filter_by(id=achievement_id).first()
    if not achievement:
        return {"success": False, "reward": {}, "message": "成就不存在"}
    
    reward = {
        "exp": achievement.exp_reward,
        "gold": achievement.gold_reward,
        "items": []
    }
    
    player.exp += achievement.exp_reward
    player.gold += achievement.gold_reward
    
    if achievement.item_reward:
        item_id = achievement.item_reward.get("item_id")
        quantity = achievement.item_reward.get("quantity", 1)
        if item_id:
            add_item_to_inventory(db, player.id, item_id, quantity)
            item = db.query(Item).filter_by(id=item_id).first()
            if item:
                reward["items"].append({
                    "item_id": item_id,
                    "item_name": item.name,
                    "quantity": quantity
                })
    
    check_level_up(player)
    update_level_achievement(db, player)
    
    player_ach = db.query(PlayerAchievement).filter_by(
        player_id=player.id, achievement_id=achievement_id
    ).first()
    player_ach.reward_claimed = True
    player_ach.claimed_at = datetime.now()
    
    db.commit()
    
    return {"success": True, "reward": reward, "message": "奖励领取成功"}
