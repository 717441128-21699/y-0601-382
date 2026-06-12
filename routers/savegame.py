from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Player, SaveGame, Equipment, Inventory, CharacterSkill, PlayerQuest, SkillCooldown, DialogueChoice, PlayerAchievement, BattleRecord
from schemas import SaveGameCreate, SaveGameResponse, ChapterProgress
from routers.account import get_current_player

router = APIRouter(prefix="/api/savegame", tags=["存档读取"])


@router.post("/save")
def save_game(
    data: SaveGameCreate,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if data.slot < 0 or data.slot > 9:
        raise HTTPException(status_code=400, detail="存档槽位必须在0-9之间")
    
    equipment_data = []
    for eq in player.equipment:
        equipment_data.append({
            "item_id": eq.item_id,
            "slot": eq.slot,
            "character_id": eq.character_id
        })
    
    inventory_data = []
    for inv in player.inventory:
        inventory_data.append({
            "item_id": inv.item_id,
            "quantity": inv.quantity
        })
    
    quest_data = []
    for pq in player.quests:
        quest_data.append({
            "quest_id": pq.quest_id,
            "status": pq.status,
            "progress": pq.progress,
            "target_progress": pq.target_progress
        })
    
    character_data = []
    for char in player.characters:
        skills = db.query(CharacterSkill).filter_by(character_id=char.id).all()
        skill_list = [{"skill_id": s.skill_id, "level": s.level} for s in skills]
        save_key = f"{char.name}__{char.class_name}"
        character_data.append({
            "__save_key": save_key,
            "original_id": char.id,
            "name": char.name,
            "class_name": char.class_name,
            "level": char.level,
            "exp": char.exp,
            "max_hp": char.max_hp,
            "current_hp": char.current_hp,
            "max_mp": char.max_mp,
            "current_mp": char.current_mp,
            "attack": char.attack,
            "defense": char.defense,
            "speed": char.speed,
            "avatar": char.avatar,
            "stat_points": char.stat_points or 0,
            "added_max_hp": char.added_max_hp or 0,
            "added_attack": char.added_attack or 0,
            "added_defense": char.added_defense or 0,
            "added_speed": char.added_speed or 0,
            "skills": skill_list
        })

    equipment_data = []
    for eq in player.equipment:
        char_obj = next((c for c in player.characters if c.id == eq.character_id), None)
        save_key = f"{char_obj.name}__{char_obj.class_name}" if char_obj else None
        equipment_data.append({
            "character_save_key": save_key,
            "character_id": eq.character_id,
            "item_id": eq.item_id,
            "slot": eq.slot
        })

    cooldown_data = []
    for cd in player.cooldowns:
        char_obj = next((c for c in player.characters if c.id == cd.character_id), None)
        save_key = f"{char_obj.name}__{char_obj.class_name}" if char_obj else None
        cooldown_data.append({
            "character_save_key": save_key,
            "character_id": cd.character_id,
            "skill_id": cd.skill_id,
            "remaining_turns": cd.remaining_turns
        })

    dialogue_data = []
    for dc in player.dialogue_choices:
        dialogue_data.append({
            "dialogue_id": dc.dialogue_id,
            "choice_id": dc.choice_id,
            "branch_path": dc.branch_path
        })

    achievement_data = []
    for pa in player.achievements:
        achievement_data.append({
            "achievement_id": pa.achievement_id,
            "progress": pa.progress,
            "unlocked": pa.unlocked,
            "reward_claimed": pa.reward_claimed
        })

    battle_data = []
    for br in player.battle_records:
        char_obj = next((c for c in player.characters if c.id == br.character_id), None)
        save_key = f"{char_obj.name}__{char_obj.class_name}" if char_obj else None
        battle_data.append({
            "character_save_key": save_key,
            "character_id": br.character_id,
            "enemy_id": br.enemy_id,
            "enemy_name": br.enemy_name,
            "enemy_level": br.enemy_level,
            "victory": br.victory,
            "rounds": br.rounds,
            "exp_gained": br.exp_gained,
            "gold_gained": br.gold_gained,
            "skills_used": br.skills_used,
            "items_dropped": br.items_dropped,
            "player_level_before": br.player_level_before,
            "player_level_after": br.player_level_after,
            "player_gold_before": br.player_gold_before,
            "player_gold_after": br.player_gold_after,
            "character_level_before": br.character_level_before,
            "character_level_after": br.character_level_after,
            "character_hp_before": br.character_hp_before,
            "character_hp_after": br.character_hp_after,
            "round_summary": br.round_summary,
            "created_at": br.created_at.isoformat() if br.created_at else None
        })

    save_data = {
        "player": {
            "level": player.level,
            "exp": player.exp,
            "gold": player.gold,
            "nickname": player.nickname,
            "avatar": player.avatar
        },
        "characters": character_data,
        "equipment": equipment_data,
        "inventory": inventory_data,
        "quests": quest_data,
        "dialogue_choices": dialogue_data,
        "skill_cooldowns": cooldown_data,
        "achievements": achievement_data,
        "battle_records": battle_data,
        "current_chapter": player.current_chapter,
        "chapter_progress": player.chapter_progress,
        "play_time": player.play_time
    }
    
    existing_save = db.query(SaveGame).filter_by(
        player_id=player.id, slot=data.slot
    ).first()
    
    if existing_save:
        existing_save.name = data.name or f"存档 {data.slot + 1}"
        existing_save.chapter = player.current_chapter
        existing_save.chapter_progress = player.chapter_progress
        existing_save.play_time = player.play_time
        existing_save.data = save_data
        existing_save.updated_at = datetime.now()
        save = existing_save
    else:
        save = SaveGame(
            player_id=player.id,
            slot=data.slot,
            name=data.name or f"存档 {data.slot + 1}",
            chapter=player.current_chapter,
            chapter_progress=player.chapter_progress,
            play_time=player.play_time,
            data=save_data
        )
        db.add(save)
    
    db.commit()
    db.refresh(save)
    
    return {
        "success": True,
        "save_id": save.id,
        "slot": data.slot,
        "name": save.name,
        "chapter": save.chapter,
        "play_time": save.play_time,
        "created_at": save.created_at,
        "message": "存档成功"
    }


@router.get("/list")
def get_save_list(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    saves = db.query(SaveGame).filter_by(player_id=player.id).order_by(SaveGame.slot).all()
    return [{
        "id": s.id,
        "player_id": s.player_id,
        "slot": s.slot,
        "name": s.name,
        "chapter": s.chapter,
        "play_time": s.play_time,
        "created_at": s.created_at,
        "data": s.data
    } for s in saves]


@router.get("/auto_save")
def auto_save(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    auto_save_data = SaveGameCreate(slot=0, name="自动存档")
    return save_game(auto_save_data, player, db)


@router.put("/chapter_progress")
def update_chapter_progress(
    data: ChapterProgress,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    player.current_chapter = max(player.current_chapter, data.chapter)
    player.chapter_progress = max(player.chapter_progress, data.progress)
    db.commit()
    
    return {
        "success": True,
        "current_chapter": player.current_chapter,
        "chapter_progress": player.chapter_progress,
        "message": "章节进度已更新"
    }


@router.get("/play_time/add")
def add_play_time(
    seconds: int = 60,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    player.play_time += seconds
    
    from game_utils import update_speedrun_achievement
    update_speedrun_achievement(db, player)
    
    db.commit()
    
    hours = player.play_time // 3600
    minutes = (player.play_time % 3600) // 60
    secs = player.play_time % 60
    
    return {
        "success": True,
        "added_seconds": seconds,
        "total_play_time": player.play_time,
        "formatted_time": f"{hours:02d}:{minutes:02d}:{secs:02d}"
    }


@router.get("/{save_id}")
def get_save_detail(
    save_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    save = db.query(SaveGame).filter_by(id=save_id, player_id=player.id).first()
    if not save:
        raise HTTPException(status_code=404, detail="存档不存在")
    
    return {
        "id": save.id,
        "slot": save.slot,
        "name": save.name,
        "chapter": save.chapter,
        "chapter_progress": save.chapter_progress,
        "play_time": save.play_time,
        "created_at": save.created_at,
        "updated_at": save.updated_at,
        "summary": {
            "player_level": save.data.get("player", {}).get("level", 1),
            "gold": save.data.get("player", {}).get("gold", 0),
            "character_count": len(save.data.get("characters", [])),
            "quest_completed": sum(1 for q in save.data.get("quests", []) if q.get("status") == "completed")
        }
    }


@router.post("/load/{save_id}")
def load_game(
    save_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    save = db.query(SaveGame).filter_by(id=save_id, player_id=player.id).first()
    if not save:
        raise HTTPException(status_code=404, detail="存档不存在")
    
    save_data = save.data
    
    player_data = save_data.get("player", {})
    player.level = player_data.get("level", 1)
    player.exp = player_data.get("exp", 0)
    player.gold = player_data.get("gold", 0)
    player.nickname = player_data.get("nickname", player.nickname)
    player.avatar = player_data.get("avatar", player.avatar)
    player.current_chapter = save_data.get("current_chapter", 1)
    player.chapter_progress = save_data.get("chapter_progress", 0)
    player.play_time = save_data.get("play_time", 0)
    
    for eq in player.equipment:
        db.delete(eq)
    for inv in player.inventory:
        db.delete(inv)
    for pq in player.quests:
        db.delete(pq)
    for dc in player.dialogue_choices:
        db.delete(dc)
    for cd in player.cooldowns:
        db.delete(cd)
    for pa in player.achievements:
        db.delete(pa)
    for br in player.battle_records:
        db.delete(br)
    for char in player.characters:
        for skill in char.skills:
            db.delete(skill)
        db.delete(char)

    from models import Character, Equipment, Inventory, PlayerQuest, CharacterSkill, DialogueChoice as DC, SkillCooldown as SCD, PlayerAchievement as PA, BattleRecord as BR
    from datetime import datetime

    char_id_map = {}
    for char_data in save_data.get("characters", []):
        char = Character(
            player_id=player.id,
            name=char_data.get("name"),
            class_name=char_data.get("class_name"),
            level=char_data.get("level", 1),
            exp=char_data.get("exp", 0),
            max_hp=char_data.get("max_hp", 100),
            current_hp=char_data.get("current_hp", 100),
            max_mp=char_data.get("max_mp", 50),
            current_mp=char_data.get("current_mp", 50),
            attack=char_data.get("attack", 10),
            defense=char_data.get("defense", 5),
            speed=char_data.get("speed", 5),
            avatar=char_data.get("avatar"),
            stat_points=char_data.get("stat_points", 0),
            added_max_hp=char_data.get("added_max_hp", 0),
            added_attack=char_data.get("added_attack", 0),
            added_defense=char_data.get("added_defense", 0),
            added_speed=char_data.get("added_speed", 0)
        )
        db.add(char)
        db.flush()

        save_key = char_data.get("__save_key") or f"{char_data.get('name')}__{char_data.get('class_name')}"
        char_id_map[save_key] = char.id
        orig_id = char_data.get("original_id") or char_data.get("id")
        if orig_id:
            char_id_map[f"orig:{orig_id}"] = char.id

        for skill_data in char_data.get("skills", []):
            cs = CharacterSkill(
                character_id=char.id,
                skill_id=skill_data.get("skill_id"),
                level=skill_data.get("level", 1)
            )
            db.add(cs)

    def resolve_cid(entry):
        sk = entry.get("character_save_key")
        if sk and sk in char_id_map:
            return char_id_map[sk]
        orig = entry.get("character_id")
        if orig and f"orig:{orig}" in char_id_map:
            return char_id_map[f"orig:{orig}"]
        if orig and orig in char_id_map.values():
            return orig
        return list(char_id_map.values())[0] if char_id_map else orig

    for eq_data in save_data.get("equipment", []):
        eq = Equipment(
            player_id=player.id,
            character_id=resolve_cid(eq_data),
            item_id=eq_data.get("item_id"),
            slot=eq_data.get("slot")
        )
        db.add(eq)

    for inv_data in save_data.get("inventory", []):
        inv = Inventory(
            player_id=player.id,
            item_id=inv_data.get("item_id"),
            quantity=inv_data.get("quantity", 1)
        )
        db.add(inv)

    for q_data in save_data.get("quests", []):
        pq = PlayerQuest(
            player_id=player.id,
            quest_id=q_data.get("quest_id"),
            status=q_data.get("status", "available"),
            progress=q_data.get("progress", 0),
            target_progress=q_data.get("target_progress", 1)
        )
        db.add(pq)

    for dc_data in save_data.get("dialogue_choices", []):
        dc = DC(
            player_id=player.id,
            dialogue_id=dc_data.get("dialogue_id"),
            choice_id=dc_data.get("choice_id"),
            branch_path=dc_data.get("branch_path", "")
        )
        db.add(dc)

    for cd_data in save_data.get("skill_cooldowns", []):
        remaining = cd_data.get("remaining_turns", 0)
        if remaining > 0:
            cd = SCD(
                player_id=player.id,
                character_id=resolve_cid(cd_data),
                skill_id=cd_data.get("skill_id"),
                remaining_turns=remaining
            )
            db.add(cd)

    for pa_data in save_data.get("achievements", []):
        pa = PA(
            player_id=player.id,
            achievement_id=pa_data.get("achievement_id"),
            progress=pa_data.get("progress", 0),
            unlocked=pa_data.get("unlocked", False),
            reward_claimed=pa_data.get("reward_claimed", False)
        )
        if pa.unlocked:
            pa.unlocked_at = datetime.now()
        if pa.reward_claimed:
            pa.claimed_at = datetime.now()
        db.add(pa)

    for br_data in save_data.get("battle_records", []):
        br = BR(
            player_id=player.id,
            character_id=resolve_cid(br_data),
            enemy_id=br_data.get("enemy_id"),
            enemy_name=br_data.get("enemy_name"),
            enemy_level=br_data.get("enemy_level", 1),
            victory=br_data.get("victory", False),
            rounds=br_data.get("rounds", 0),
            exp_gained=br_data.get("exp_gained", 0),
            gold_gained=br_data.get("gold_gained", 0),
            skills_used=br_data.get("skills_used", []),
            items_dropped=br_data.get("items_dropped", []),
            battle_log=[],
            player_level_before=br_data.get("player_level_before", 1),
            player_level_after=br_data.get("player_level_after", 1),
            player_gold_before=br_data.get("player_gold_before", 0),
            player_gold_after=br_data.get("player_gold_after", 0),
            character_level_before=br_data.get("character_level_before", 1),
            character_level_after=br_data.get("character_level_after", 1),
            character_hp_before=br_data.get("character_hp_before", 0),
            character_hp_after=br_data.get("character_hp_after", 0),
            round_summary=br_data.get("round_summary", [])
        )
        created_str = br_data.get("created_at")
        if created_str:
            try:
                br.created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00').replace('+00:00', ''))
            except Exception:
                pass
        db.add(br)

    from game_utils import update_speedrun_achievement
    update_speedrun_achievement(db, player)
    
    db.commit()
    
    return {
        "success": True,
        "save_id": save_id,
        "name": save.name,
        "player": {
            "level": player.level,
            "gold": player.gold,
            "chapter": player.current_chapter
        },
        "message": "存档加载成功"
    }


@router.delete("/{save_id}")
def delete_save(
    save_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    save = db.query(SaveGame).filter_by(id=save_id, player_id=player.id).first()
    if not save:
        raise HTTPException(status_code=404, detail="存档不存在")
    
    save_name = save.name
    db.delete(save)
    db.commit()
    
    return {
        "success": True,
        "save_id": save_id,
        "name": save_name,
        "message": "存档已删除"
    }
