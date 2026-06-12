from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Player, Enemy, Skill, CharacterSkill, SkillCooldown
from schemas import BattleRequest, BattleResponse, SkillResponse
from routers.account import get_current_player
from game_utils import process_battle, calculate_skill_effect, get_equipment_stats

router = APIRouter(prefix="/api/battle", tags=["战斗结算"])


@router.get("/enemies")
def get_enemies(
    level: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Enemy)
    if level > 0:
        query = query.filter(Enemy.level <= level + 2, Enemy.level >= max(1, level - 2))
    
    enemies = query.all()
    return [{
        "id": e.id,
        "name": e.name,
        "description": e.description,
        "level": e.level,
        "max_hp": e.max_hp,
        "attack": e.attack,
        "defense": e.defense,
        "speed": e.speed,
        "exp_reward": e.exp_reward,
        "gold_reward": e.gold_reward
    } for e in enemies]


@router.get("/enemy/{enemy_id}")
def get_enemy(enemy_id: int, db: Session = Depends(get_db)):
    enemy = db.query(Enemy).filter_by(id=enemy_id).first()
    if not enemy:
        raise HTTPException(status_code=404, detail="敌人不存在")
    
    return {
        "id": enemy.id,
        "name": enemy.name,
        "description": enemy.description,
        "level": enemy.level,
        "max_hp": enemy.max_hp,
        "attack": enemy.attack,
        "defense": enemy.defense,
        "speed": enemy.speed,
        "exp_reward": enemy.exp_reward,
        "gold_reward": enemy.gold_reward,
        "loot_table": enemy.loot_table,
        "skills": enemy.skills
    }


@router.get("/skills/{character_id}", response_model=list[SkillResponse])
def get_character_skills(
    character_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from models import Character
    character = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    char_skills = db.query(CharacterSkill).filter_by(character_id=character_id).all()
    
    skills = []
    for cs in char_skills:
        skill = db.query(Skill).filter_by(id=cs.skill_id).first()
        if skill:
            cooldown = db.query(SkillCooldown).filter_by(
                player_id=player.id, character_id=character_id, skill_id=skill.id
            ).first()
            
            skills.append({
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "damage": skill.damage,
                "mp_cost": skill.mp_cost,
                "cooldown": skill.cooldown,
                "current_cooldown": cooldown.remaining_turns if cooldown else 0
            })
    
    return skills


@router.post("/start", response_model=BattleResponse)
def start_battle(
    data: BattleRequest,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from models import Character
    character = db.query(Character).filter_by(id=data.character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if character.current_hp <= 0:
        raise HTTPException(status_code=400, detail="角色生命值为0，请先恢复")
    
    enemy = db.query(Enemy).filter_by(id=data.enemy_id).first()
    if not enemy:
        raise HTTPException(status_code=404, detail="敌人不存在")
    
    result = process_battle(db, player, character, enemy, data.skill_id)
    
    return result


@router.get("/simulate")
def simulate_battle(
    enemy_id: int,
    character_id: int,
    skill_id: int = None,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from models import Character
    character = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    enemy = db.query(Enemy).filter_by(id=enemy_id).first()
    if not enemy:
        raise HTTPException(status_code=404, detail="敌人不存在")
    
    equipment_stats = get_equipment_stats(db, player.id, character_id)
    player_attack = character.attack + equipment_stats.get("attack", 0)
    player_defense = character.defense + equipment_stats.get("defense", 0)
    player_speed = character.speed + equipment_stats.get("speed", 0)
    player_max_hp = character.max_hp + equipment_stats.get("max_hp", 0)
    player_max_mp = character.max_mp + equipment_stats.get("max_mp", 0)
    
    estimated_damage = max(1, player_attack - enemy.defense)
    estimated_damage_taken = max(1, enemy.attack - player_defense)
    
    turns_to_kill = (enemy.max_hp + estimated_damage - 1) // estimated_damage
    turns_to_die = (character.current_hp + estimated_damage_taken - 1) // estimated_damage_taken
    
    skill_info = None
    if skill_id:
        skill = db.query(Skill).filter_by(id=skill_id).first()
        if skill:
            effect = calculate_skill_effect(skill, character, equipment_stats)
            skill_info = {
                "skill_name": skill.name,
                "skill_damage": effect["damage"],
                "skill_heal": effect["heal"],
                "mp_cost": effect["mp_cost"]
            }
    
    return {
        "player": {
            "name": character.name,
            "level": character.level,
            "hp": character.current_hp,
            "max_hp": player_max_hp,
            "mp": character.current_mp,
            "max_mp": player_max_mp,
            "attack": player_attack,
            "defense": player_defense,
            "speed": player_speed
        },
        "enemy": {
            "name": enemy.name,
            "level": enemy.level,
            "max_hp": enemy.max_hp,
            "attack": enemy.attack,
            "defense": enemy.defense,
            "speed": enemy.speed
        },
        "battle_analysis": {
            "estimated_player_damage": estimated_damage,
            "estimated_enemy_damage": estimated_damage_taken,
            "turns_to_kill_enemy": turns_to_kill,
            "turns_to_die": turns_to_die,
            "victory_chance": "高" if turns_to_kill <= turns_to_die else ("中" if turns_to_kill <= turns_to_die + 2 else "低")
        },
        "skill_info": skill_info,
        "rewards": {
            "exp": enemy.exp_reward,
            "gold": enemy.gold_reward
        }
    }


@router.post("/restore_hp")
def restore_hp(
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    character_id = data.get("character_id")
    amount = data.get("amount", 0)
    
    from models import Character
    character = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    equipment_stats = get_equipment_stats(db, player.id, character_id)
    max_hp = character.max_hp + equipment_stats.get("max_hp", 0)
    
    if amount == 0:
        character.current_hp = max_hp
        character.current_mp = character.max_mp + equipment_stats.get("max_mp", 0)
    else:
        character.current_hp = min(character.current_hp + amount, max_hp)
    
    db.commit()
    
    return {
        "success": True,
        "current_hp": character.current_hp,
        "current_mp": character.current_mp,
        "message": f"恢复了 {amount if amount > 0 else '全部'} 生命值"
    }


@router.get("/cooldowns/{character_id}")
def get_cooldowns(
    character_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    cooldowns = db.query(SkillCooldown).filter_by(
        player_id=player.id, character_id=character_id
    ).all()
    
    result = {}
    for cd in cooldowns:
        skill = db.query(Skill).filter_by(id=cd.skill_id).first()
        if skill:
            result[str(cd.skill_id)] = {
                "skill_name": skill.name,
                "remaining_turns": cd.remaining_turns
            }
    
    return {
        "character_id": character_id,
        "cooldowns": result
    }


@router.post("/reset_cooldowns")
def reset_cooldowns(
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    character_id = data.get("character_id")
    
    cooldowns = db.query(SkillCooldown).filter_by(
        player_id=player.id, character_id=character_id
    ).all()
    
    for cd in cooldowns:
        db.delete(cd)
    
    db.commit()
    
    return {
        "success": True,
        "message": "所有技能冷却已重置"
    }
