from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Player
from schemas import PlayerCreate, PlayerLogin, PlayerResponse, CharacterCreate, CharacterResponse, ProfileUpdate
from game_utils import hash_password, verify_password, create_character_for_player, update_level_achievement

router = APIRouter(prefix="/api/account", tags=["账号角色"])


def get_current_player(player_id: int = Header(0), db: Session = Depends(get_db)) -> Player:
    if player_id == 0:
        raise HTTPException(status_code=401, detail="请先登录")
    player = db.query(Player).filter_by(id=player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="玩家不存在")
    return player


@router.post("/register", response_model=PlayerResponse)
def register(data: PlayerCreate, db: Session = Depends(get_db)):
    existing = db.query(Player).filter_by(username=data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    player = Player(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        level=1,
        exp=0,
        gold=100
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.post("/login")
def login(data: PlayerLogin, db: Session = Depends(get_db)):
    player = db.query(Player).filter_by(username=data.username).first()
    if not player or not verify_password(data.password, player.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    player.is_online = True
    player.last_login = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "player_id": player.id,
        "nickname": player.nickname,
        "level": player.level,
        "message": "登录成功"
    }


@router.post("/logout")
def logout(player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    player.is_online = False
    db.commit()
    return {"success": True, "message": "登出成功"}


@router.get("/profile", response_model=PlayerResponse)
def get_profile(player: Player = Depends(get_current_player)):
    return player


@router.put("/profile", response_model=PlayerResponse)
def update_profile(
    data: ProfileUpdate,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if data.nickname:
        player.nickname = data.nickname
    if data.avatar:
        player.avatar = data.avatar
    db.commit()
    db.refresh(player)
    return player


@router.get("/exp_required")
def get_exp_required(level: int = 1):
    from game_utils import get_exp_required
    return {"level": level, "exp_required": get_exp_required(level)}


@router.post("/character", response_model=CharacterResponse)
def create_character(
    data: CharacterCreate,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if len(player.characters) >= 3:
        raise HTTPException(status_code=400, detail="最多创建3个角色")
    
    try:
        character = create_character_for_player(db, player.id, data.name, data.class_name)
        db.commit()
        db.refresh(character)
        return character
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/characters", response_model=list[CharacterResponse])
def get_characters(player: Player = Depends(get_current_player)):
    return player.characters


@router.get("/character/{character_id}")
def get_character(
    character_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from models import Character, Equipment
    character = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    from game_utils import get_equipment_stats
    eq_stats = get_equipment_stats(db, player.id, character.id)
    equipment = db.query(Equipment).filter_by(
        player_id=player.id, character_id=character.id
    ).all()
    equip_slots = {}
    for eq in equipment:
        if eq.item:
            equip_slots[eq.slot] = {
                "item_id": eq.item_id,
                "name": eq.item.name,
                "rarity": eq.item.rarity
            }

    base_max_hp = character.max_hp
    base_max_mp = character.max_mp
    base_attack = character.attack
    base_defense = character.defense
    base_speed = character.speed
    added_max_hp = character.added_max_hp or 0
    added_attack = character.added_attack or 0
    added_defense = character.added_defense or 0
    added_speed = character.added_speed or 0
    pre_eq_max_hp = base_max_hp + added_max_hp
    pre_eq_max_mp = base_max_mp
    pre_eq_attack = base_attack + added_attack
    pre_eq_defense = base_defense + added_defense
    pre_eq_speed = base_speed + added_speed

    return {
        "id": character.id,
        "name": character.name,
        "class_name": character.class_name,
        "level": character.level,
        "exp": character.exp,
        "stat_points": character.stat_points or 0,
        "base_stats": {
            "max_hp": base_max_hp,
            "max_mp": base_max_mp,
            "attack": base_attack,
            "defense": base_defense,
            "speed": base_speed
        },
        "allocated_stats": {
            "max_hp": added_max_hp,
            "attack": added_attack,
            "defense": added_defense,
            "speed": added_speed
        },
        "pre_equipment_stats": {
            "max_hp": pre_eq_max_hp,
            "max_mp": pre_eq_max_mp,
            "attack": pre_eq_attack,
            "defense": pre_eq_defense,
            "speed": pre_eq_speed
        },
        "equipment_bonus": {
            "max_hp": eq_stats.get("max_hp", 0),
            "max_mp": eq_stats.get("max_mp", 0),
            "attack": eq_stats.get("attack", 0),
            "defense": eq_stats.get("defense", 0),
            "speed": eq_stats.get("speed", 0)
        },
        "final_stats": {
            "max_hp": pre_eq_max_hp + eq_stats.get("max_hp", 0),
            "max_mp": pre_eq_max_mp + eq_stats.get("max_mp", 0),
            "attack": pre_eq_attack + eq_stats.get("attack", 0),
            "defense": pre_eq_defense + eq_stats.get("defense", 0),
            "speed": pre_eq_speed + eq_stats.get("speed", 0)
        },
        "current_hp": min(character.current_hp, pre_eq_max_hp + eq_stats.get("max_hp", 0)),
        "current_mp": min(character.current_mp, pre_eq_max_mp + eq_stats.get("max_mp", 0)),
        "avatar": character.avatar,
        "equipped_items": equip_slots,
        "created_at": character.created_at
    }


@router.post("/character/{character_id}/allocate_stats")
def allocate_stats(
    character_id: int,
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from models import Character
    character = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    available = character.stat_points or 0
    hp_add = max(0, int(data.get("max_hp", 0)))
    atk_add = max(0, int(data.get("attack", 0)))
    def_add = max(0, int(data.get("defense", 0)))
    spd_add = max(0, int(data.get("speed", 0)))

    total = hp_add + atk_add + def_add + spd_add
    if total == 0:
        raise HTTPException(status_code=400, detail="至少分配1点属性")
    if total > available:
        raise HTTPException(status_code=400, detail=f"分配点数({total})超过可用点数({available})")

    character.stat_points = available - total
    character.added_max_hp = (character.added_max_hp or 0) + hp_add
    character.added_attack = (character.added_attack or 0) + atk_add
    character.added_defense = (character.added_defense or 0) + def_add
    character.added_speed = (character.added_speed or 0) + spd_add

    if hp_add > 0:
        character.current_hp = (character.current_hp or 0) + hp_add

    db.commit()

    from game_utils import get_equipment_stats
    eq_stats = get_equipment_stats(db, player.id, character.id)
    final_max_hp = character.max_hp + (character.added_max_hp or 0) + eq_stats.get("max_hp", 0)
    character.current_hp = min(character.current_hp, final_max_hp)
    db.commit()

    return {
        "success": True,
        "message": f"成功分配 {total} 点属性",
        "stat_points_remaining": character.stat_points or 0,
        "allocated": {
            "max_hp": hp_add,
            "attack": atk_add,
            "defense": def_add,
            "speed": spd_add
        },
        "final_stats": {
            "max_hp": character.max_hp + (character.added_max_hp or 0) + eq_stats.get("max_hp", 0),
            "attack": character.attack + (character.added_attack or 0) + eq_stats.get("attack", 0),
            "defense": character.defense + (character.added_defense or 0) + eq_stats.get("defense", 0),
            "speed": character.speed + (character.added_speed or 0) + eq_stats.get("speed", 0)
        }
    }


@router.put("/character/{character_id}/avatar")
def update_character_avatar(
    character_id: int,
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from models import Character
    character = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    character.avatar = data.get("avatar")
    db.commit()
    return {"success": True, "message": "头像更新成功"}


@router.post("/add_exp")
def add_exp(
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    exp = data.get("exp", 0)
    if exp <= 0:
        raise HTTPException(status_code=400, detail="经验值必须大于0")
    
    player.exp += exp
    from game_utils import check_level_up
    level_ups = check_level_up(player)
    
    for lv in level_ups:
        for char in player.characters:
            from game_utils import update_character_stats_on_level
            update_character_stats_on_level(db, char, 1)
    
    update_level_achievement(db, player)
    db.commit()
    
    return {
        "success": True,
        "exp_added": exp,
        "new_level": player.level,
        "current_exp": player.exp,
        "level_ups": level_ups
    }


@router.post("/add_gold")
def add_gold(
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    gold = data.get("gold", 0)
    if gold == 0:
        raise HTTPException(status_code=400, detail="金币数量不能为0")
    
    player.gold = max(0, player.gold + gold)
    
    from game_utils import update_wealth_achievement
    update_wealth_achievement(db, player)
    db.commit()
    
    return {
        "success": True,
        "gold_changed": gold,
        "current_gold": player.gold
    }
