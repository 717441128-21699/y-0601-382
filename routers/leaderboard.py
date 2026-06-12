from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Player, PlayerAchievement, Achievement, Leaderboard
from schemas import AchievementResponse, LeaderboardEntry, ClaimRewardRequest, ClaimRewardResponse
from routers.account import get_current_player
from game_utils import claim_achievement_reward

router = APIRouter(prefix="/api/leaderboard", tags=["排行榜"])
achievement_router = APIRouter(prefix="/api/achievement", tags=["成就系统"])


@achievement_router.get("/all")
def get_all_achievements(db: Session = Depends(get_db)):
    achievements = db.query(Achievement).all()
    return [{
        "id": a.id,
        "name": a.name,
        "description": a.description,
        "category": a.category,
        "condition_type": a.condition_type,
        "condition_value": a.condition_value,
        "exp_reward": a.exp_reward,
        "gold_reward": a.gold_reward,
        "is_rare": a.is_rare
    } for a in achievements]


@achievement_router.get("/player")
def get_player_achievements(
    unlocked: bool = None,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    query = db.query(PlayerAchievement).filter_by(player_id=player.id)
    if unlocked is not None:
        query = query.filter_by(unlocked=unlocked)
    
    pachs = query.all()
    result = []
    for pa in pachs:
        ach = db.query(Achievement).filter_by(id=pa.achievement_id).first()
        if ach:
            result.append({
                "id": pa.id,
                "achievement_id": pa.achievement_id,
                "name": ach.name,
                "description": ach.description,
                "unlocked_at": pa.unlocked_at,
                "reward_claimed": pa.reward_claimed
            })
    return result


@achievement_router.post("/claim")
def claim_reward(
    data: ClaimRewardRequest,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    result = claim_achievement_reward(db, player, data.achievement_id)
    return result


@achievement_router.get("/unlock_check")
def check_unlocked_achievements(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    from game_utils import (
        update_level_achievement,
        update_quest_achievement,
        update_main_quest_achievement,
        update_speedrun_achievement
    )

    before_ids = set(
        pa.achievement_id for pa in
        db.query(PlayerAchievement).filter_by(
            player_id=player.id, unlocked=True
        ).all()
    )

    update_level_achievement(db, player)
    update_quest_achievement(db, player)
    update_main_quest_achievement(db, player)
    update_speedrun_achievement(db, player)

    db.commit()

    after_all = db.query(PlayerAchievement).filter_by(
        player_id=player.id, unlocked=True
    ).all()
    newly_unlocked = [
        pa for pa in after_all if pa.achievement_id not in before_ids
    ]

    result = []
    for pa in newly_unlocked:
        ach = db.query(Achievement).filter_by(id=pa.achievement_id).first()
        if ach:
            result.append({
                "id": pa.achievement_id,
                "name": ach.name,
                "description": ach.description,
                "category": ach.category,
                "condition_type": ach.condition_type,
                "condition_value": ach.condition_value,
                "progress": pa.progress,
                "unlocked_at": pa.unlocked_at,
                "rewards": {
                    "exp": ach.exp_reward,
                    "gold": ach.gold_reward
                }
            })

    claimed_count = sum(1 for pa in after_all if pa.reward_claimed)
    total_unlocked = len(after_all)

    return {
        "success": True,
        "unlocked_count": len(result),
        "total_unlocked": total_unlocked,
        "claimed_count": claimed_count,
        "pending_claim_count": total_unlocked - claimed_count,
        "newly_unlocked": result
    }


@achievement_router.get("/{achievement_id}")
def get_achievement_detail(
    achievement_id: int,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    achievement = db.query(Achievement).filter_by(id=achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="成就不存在")
    
    player_ach = db.query(PlayerAchievement).filter_by(
        player_id=player.id, achievement_id=achievement_id
    ).first()
    
    return {
        "achievement": {
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "category": achievement.category,
            "condition_type": achievement.condition_type,
            "condition_value": achievement.condition_value,
            "exp_reward": achievement.exp_reward,
            "gold_reward": achievement.gold_reward,
            "item_reward": achievement.item_reward,
            "is_rare": achievement.is_rare
        },
        "player_progress": {
            "unlocked": player_ach.unlocked if player_ach else False,
            "progress": player_ach.progress if player_ach else 0,
            "unlocked_at": player_ach.unlocked_at if player_ach else None,
            "reward_claimed": player_ach.reward_claimed if player_ach else False
        }
    }


@router.get("/level")
def get_level_leaderboard(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    players = db.query(Player).order_by(Player.level.desc(), Player.exp.desc()).limit(limit).all()
    
    result = []
    for rank, p in enumerate(players, 1):
        result.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "exp": p.exp,
            "value": p.level,
            "rank": rank
        })
    
    _update_leaderboard(db, "level", result)
    
    return result


@router.get("/gold")
def get_gold_leaderboard(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    players = db.query(Player).order_by(Player.gold.desc()).limit(limit).all()
    
    result = []
    for rank, p in enumerate(players, 1):
        result.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "gold": p.gold,
            "value": p.gold,
            "rank": rank
        })
    
    _update_leaderboard(db, "gold", result)
    
    return result


@router.get("/play_time")
def get_play_time_leaderboard(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    players = db.query(Player).filter(Player.play_time > 0).order_by(Player.play_time.desc()).limit(limit).all()
    
    result = []
    for rank, p in enumerate(players, 1):
        hours = p.play_time // 3600
        minutes = (p.play_time % 3600) // 60
        result.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "play_time": p.play_time,
            "play_time_formatted": f"{hours:02d}:{minutes:02d}",
            "value": p.play_time,
            "rank": rank
        })
    
    _update_leaderboard(db, "play_time", result)
    
    return result


@router.get("/speedrun")
def get_speedrun_leaderboard(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    from models import Quest, PlayerQuest
    
    completed_players = db.query(Player).join(PlayerQuest).join(Quest).filter(
        Quest.id == 8,
        PlayerQuest.status == "completed"
    ).all()
    
    valid_players = [p for p in completed_players if p.play_time > 0]
    valid_players.sort(key=lambda x: x.play_time)
    
    result = []
    for rank, p in enumerate(valid_players[:limit], 1):
        hours = p.play_time // 3600
        minutes = (p.play_time % 3600) // 60
        result.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "clear_time": p.play_time,
            "clear_time_formatted": f"{hours:02d}:{minutes:02d}",
            "value": p.play_time,
            "rank": rank
        })
    
    _update_leaderboard(db, "speedrun", result)
    
    return result


@router.get("/achievement_count")
def get_achievement_leaderboard(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    players = db.query(Player).all()
    
    player_ach_counts = []
    for p in players:
        ach_count = db.query(PlayerAchievement).filter_by(
            player_id=p.id, unlocked=True
        ).count()
        player_ach_counts.append((p, ach_count))
    
    player_ach_counts.sort(key=lambda x: x[1], reverse=True)
    
    result = []
    for rank, (p, count) in enumerate(player_ach_counts[:limit], 1):
        if count == 0:
            continue
        result.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "achievement_count": count,
            "value": count,
            "rank": rank
        })
    
    _update_leaderboard(db, "achievement_count", result)
    
    return result


@router.get("/query")
def get_player_rank(
    category: str = "level",
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if category == "level":
        all_players = db.query(Player).order_by(Player.level.desc(), Player.exp.desc()).all()
    elif category == "gold":
        all_players = db.query(Player).order_by(Player.gold.desc()).all()
    elif category == "play_time":
        all_players = db.query(Player).filter(Player.play_time > 0).order_by(Player.play_time.desc()).all()
    elif category == "speedrun":
        from models import Quest, PlayerQuest
        all_players = db.query(Player).join(PlayerQuest).join(Quest).filter(
            Quest.id == 8,
            PlayerQuest.status == "completed"
        ).all()
        all_players.sort(key=lambda x: x.play_time)
    elif category == "achievement_count":
        all_players = db.query(Player).all()
        player_ach_counts = []
        for p in all_players:
            ach_count = db.query(PlayerAchievement).filter_by(
                player_id=p.id, unlocked=True
            ).count()
            player_ach_counts.append((p, ach_count))
        player_ach_counts.sort(key=lambda x: x[1], reverse=True)
        all_players = [p for p, _ in player_ach_counts]
    else:
        raise HTTPException(status_code=400, detail="无效的排行榜分类")
    
    rank = 0
    player_value = 0
    for i, p in enumerate(all_players, 1):
        if p.id == player.id:
            rank = i
            if category == "level":
                player_value = p.level
            elif category == "gold":
                player_value = p.gold
            elif category == "play_time":
                player_value = p.play_time
            elif category == "speedrun":
                player_value = p.play_time
            elif category == "achievement_count":
                player_value = db.query(PlayerAchievement).filter_by(
                    player_id=player.id, unlocked=True
                ).count()
            break
    
    top_10 = []
    for i, p in enumerate(all_players[:10], 1):
        value = 0
        if category == "level":
            value = p.level
        elif category == "gold":
            value = p.gold
        elif category == "play_time":
            value = p.play_time
        elif category == "speedrun":
            value = p.play_time
        elif category == "achievement_count":
            value = db.query(PlayerAchievement).filter_by(
                player_id=p.id, unlocked=True
            ).count()
        
        top_10.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "value": value,
            "rank": i
        })
    
    return {
        "category": category,
        "my_rank": rank,
        "my_value": player_value,
        "total_players": len(all_players),
        "top_10": top_10
    }


def _update_leaderboard(db: Session, category: str, data: list):
    db.query(Leaderboard).filter_by(category=category).delete()
    
    for entry in data:
        lb = Leaderboard(
            player_id=entry["player_id"],
            nickname=entry["nickname"],
            category=category,
            value=entry["value"],
            rank=entry["rank"]
        )
        db.add(lb)
    
    db.commit()
