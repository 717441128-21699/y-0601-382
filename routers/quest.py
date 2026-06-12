from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Player, PlayerQuest, Quest, Dialogue, DialogueChoice
from schemas import QuestAccept, QuestComplete, QuestResponse, DialogueChoice as DialogueChoiceSchema, DialogueResponse
from routers.account import get_current_player
from game_utils import add_item_to_inventory, update_quest_achievement, update_main_quest_achievement, update_level_achievement

router = APIRouter(prefix="/api/quest", tags=["任务状态"])


@router.get("/available")
def get_available_quests(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    accepted_quest_ids = [pq.quest_id for pq in player.quests]
    
    available_quests = db.query(Quest).filter(
        Quest.id.notin_(accepted_quest_ids),
        Quest.required_level <= player.level
    ).all()
    
    return [{
        "id": q.id,
        "name": q.name,
        "description": q.description,
        "type": q.type,
        "chapter": q.chapter,
        "required_level": q.required_level,
        "exp_reward": q.exp_reward,
        "gold_reward": q.gold_reward,
        "item_rewards": q.item_rewards,
        "pre_quest_id": q.pre_quest_id
    } for q in available_quests]


@router.get("/list", response_model=list[QuestResponse])
def get_player_quests(
    status: str = None,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    query = db.query(PlayerQuest).filter_by(player_id=player.id)
    if status:
        query = query.filter_by(status=status)
    
    pquests = query.all()
    result = []
    for pq in pquests:
        quest = db.query(Quest).filter_by(id=pq.quest_id).first()
        result.append({
            "id": pq.id,
            "quest_id": pq.quest_id,
            "quest_name": quest.name if quest else "未知任务",
            "status": pq.status,
            "progress": pq.progress,
            "accepted_at": pq.accepted_at,
            "completed_at": pq.completed_at
        })
    return result


@router.post("/accept")
def accept_quest(
    data: QuestAccept,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    quest = db.query(Quest).filter_by(id=data.quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if quest.required_level > player.level:
        raise HTTPException(status_code=400, detail=f"等级不足，需要 {quest.required_level} 级")
    
    existing = db.query(PlayerQuest).filter_by(
        player_id=player.id, quest_id=data.quest_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已经接取过该任务")
    
    if quest.pre_quest_id:
        pre_quest = db.query(PlayerQuest).filter_by(
            player_id=player.id, quest_id=quest.pre_quest_id, status="completed"
        ).first()
        if not pre_quest:
            raise HTTPException(status_code=400, detail="请先完成前置任务")
    
    pquest = PlayerQuest(
        player_id=player.id,
        quest_id=data.quest_id,
        status="in_progress",
        progress=0,
        target_progress=1,
        accepted_at=datetime.now()
    )
    db.add(pquest)
    db.commit()
    
    return {
        "success": True,
        "quest_id": data.quest_id,
        "quest_name": quest.name,
        "message": f"成功接取任务: {quest.name}"
    }


@router.post("/complete")
def complete_quest(
    data: QuestComplete,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_
    pquest = db.query(PlayerQuest).filter(
        PlayerQuest.player_id == player.id,
        PlayerQuest.quest_id == data.quest_id,
        or_(PlayerQuest.status == "in_progress", PlayerQuest.status == "ready_to_complete")
    ).first()
    if not pquest:
        raise HTTPException(status_code=400, detail="任务未接取或已完成")
    
    quest = db.query(Quest).filter_by(id=data.quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    pquest.progress = pquest.target_progress
    pquest.status = "completed"
    pquest.completed_at = datetime.now()
    
    player.exp += quest.exp_reward
    player.gold += quest.gold_reward
    
    from game_utils import check_level_up
    level_ups = check_level_up(player)
    for lv in level_ups:
        for char in player.characters:
            from game_utils import update_character_stats_on_level
            update_character_stats_on_level(db, char, 1)
    
    for item_reward in quest.item_rewards:
        add_item_to_inventory(db, player.id, item_reward["item_id"], item_reward.get("quantity", 1))
    
    update_quest_achievement(db, player)
    update_main_quest_achievement(db, player)
    update_level_achievement(db, player)
    
    if quest.type == "main":
        player.current_chapter = max(player.current_chapter, quest.chapter)
    
    db.commit()
    
    reward_items = []
    for item_reward in quest.item_rewards:
        from models import Item
        item = db.query(Item).filter_by(id=item_reward["item_id"]).first()
        if item:
            reward_items.append({
                "item_id": item_reward["item_id"],
                "item_name": item.name,
                "quantity": item_reward.get("quantity", 1)
            })
    
    return {
        "success": True,
        "quest_id": data.quest_id,
        "quest_name": quest.name,
        "rewards": {
            "exp": quest.exp_reward,
            "gold": quest.gold_reward,
            "items": reward_items
        },
        "level_ups": level_ups,
        "message": f"任务完成: {quest.name}"
    }


@router.post("/progress")
def update_quest_progress(
    data: dict,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    quest_id = data.get("quest_id")
    progress = data.get("progress", 1)
    
    pquest = db.query(PlayerQuest).filter_by(
        player_id=player.id, quest_id=quest_id, status="in_progress"
    ).first()
    if not pquest:
        raise HTTPException(status_code=400, detail="任务未接取")
    
    pquest.progress = min(pquest.progress + progress, pquest.target_progress)
    
    if pquest.progress >= pquest.target_progress:
        pquest.status = "ready_to_complete"
    
    db.commit()
    
    return {
        "success": True,
        "quest_id": quest_id,
        "current_progress": pquest.progress,
        "target_progress": pquest.target_progress,
        "can_complete": pquest.status == "ready_to_complete"
    }


dialogue_router = APIRouter(prefix="/api/dialogue", tags=["对话选择"])


@dialogue_router.get("/list")
def get_dialogue_list(chapter: int = 1, db: Session = Depends(get_db)):
    dialogues = db.query(Dialogue).filter_by(chapter=chapter).all()
    return [{
        "id": d.id,
        "npc_id": d.npc_id,
        "chapter": d.chapter,
        "content": d.content[:50] + "..." if len(d.content) > 50 else d.content
    } for d in dialogues]


@dialogue_router.get("/history")
def get_dialogue_history(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    choices = db.query(DialogueChoice).filter_by(
        player_id=player.id
    ).order_by(DialogueChoice.timestamp.desc()).all()
    
    return [{
        "id": c.id,
        "dialogue_id": c.dialogue_id,
        "choice_id": c.choice_id,
        "branch_path": c.branch_path,
        "timestamp": c.timestamp
    } for c in choices]


@dialogue_router.get("/current_branch")
def get_current_branch(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    latest_choice = db.query(DialogueChoice).filter_by(
        player_id=player.id
    ).order_by(DialogueChoice.timestamp.desc()).first()
    
    return {
        "chapter": player.current_chapter,
        "chapter_progress": player.chapter_progress,
        "current_branch": latest_choice.branch_path if latest_choice else "main",
        "last_choice_id": latest_choice.choice_id if latest_choice else None,
        "last_choice_time": latest_choice.timestamp if latest_choice else None
    }


@dialogue_router.post("/choice")
def make_choice(
    data: DialogueChoiceSchema,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    dialogue = db.query(Dialogue).filter_by(id=data.dialogue_id).first()
    if not dialogue:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    choice_found = None
    for choice in dialogue.choices:
        if choice["id"] == data.choice_id:
            choice_found = choice
            break
    
    if not choice_found:
        raise HTTPException(status_code=400, detail="选项不存在")
    
    dchoice = DialogueChoice(
        player_id=player.id,
        dialogue_id=data.dialogue_id,
        choice_id=data.choice_id,
        branch_path=data.branch_path
    )
    db.add(dchoice)
    
    if choice_found.get("quest_id"):
        existing = db.query(PlayerQuest).filter_by(
            player_id=player.id, quest_id=choice_found["quest_id"]
        ).first()
        if not existing:
            quest = db.query(Quest).filter_by(id=choice_found["quest_id"]).first()
            if quest and quest.required_level <= player.level:
                pquest = PlayerQuest(
                    player_id=player.id,
                    quest_id=choice_found["quest_id"],
                    status="in_progress",
                    progress=0,
                    target_progress=1,
                    accepted_at=datetime.now()
                )
                db.add(pquest)
    
    player.chapter_progress = max(player.chapter_progress, data.dialogue_id)
    
    db.commit()
    db.refresh(dchoice)
    
    return {
        "success": True,
        "choice": {
            "id": dchoice.id,
            "dialogue_id": dchoice.dialogue_id,
            "choice_id": dchoice.choice_id,
            "branch_path": dchoice.branch_path,
            "timestamp": dchoice.timestamp
        },
        "next_dialogue": choice_found.get("next_dialogue"),
        "quest_accepted": choice_found.get("quest_id"),
        "message": f"选择了分支: {data.branch_path}"
    }


@dialogue_router.get("/{dialogue_id}")
def get_dialogue(dialogue_id: int, db: Session = Depends(get_db)):
    dialogue = db.query(Dialogue).filter_by(id=dialogue_id).first()
    if not dialogue:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return {
        "id": dialogue.id,
        "npc_id": dialogue.npc_id,
        "chapter": dialogue.chapter,
        "content": dialogue.content,
        "choices": dialogue.choices
    }
