from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PlayerCreate(BaseModel):
    username: str
    password: str
    nickname: str


class PlayerLogin(BaseModel):
    username: str
    password: str


class PlayerResponse(BaseModel):
    id: int
    username: str
    nickname: str
    avatar: Optional[str] = None
    level: int
    exp: int
    gold: int
    created_at: datetime

    class Config:
        from_attributes = True


class CharacterCreate(BaseModel):
    name: str
    class_name: str


class CharacterResponse(BaseModel):
    id: int
    player_id: int
    name: str
    class_name: str
    level: int
    exp: int
    max_hp: int
    current_hp: int
    max_mp: int
    current_mp: int
    attack: int
    defense: int
    speed: int
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class AttributeUpdate(BaseModel):
    exp: Optional[int] = None
    gold: Optional[int] = None


class ItemAdd(BaseModel):
    item_id: int
    quantity: int = 1


class ItemRemove(BaseModel):
    item_id: int
    quantity: int = 1


class EquipmentEquip(BaseModel):
    item_id: int
    slot: str


class EquipmentUnequip(BaseModel):
    slot: str


class InventoryResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    item_type: str
    quantity: int
    stats: Optional[Dict[str, Any]] = None


class QuestAccept(BaseModel):
    quest_id: int


class QuestComplete(BaseModel):
    quest_id: int


class QuestResponse(BaseModel):
    id: int
    quest_id: int
    quest_name: str
    status: str
    progress: int
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DialogueChoice(BaseModel):
    dialogue_id: int
    choice_id: int
    branch_path: str


class DialogueResponse(BaseModel):
    id: int
    dialogue_id: int
    choice_id: int
    branch_path: str
    timestamp: datetime


class BattleRequest(BaseModel):
    enemy_id: int
    character_id: int
    skill_id: Optional[int] = None


class BattleResponse(BaseModel):
    victory: bool
    exp_gained: int
    gold_gained: int
    items_gained: List[Dict[str, Any]]
    player_hp: int
    enemy_hp: int
    battle_log: List[str]
    cooldowns: Dict[str, int]


class SkillResponse(BaseModel):
    id: int
    name: str
    description: str
    damage: int
    mp_cost: int
    cooldown: int
    current_cooldown: int


class SaveGameCreate(BaseModel):
    slot: int
    name: Optional[str] = None


class SaveGameResponse(BaseModel):
    id: int
    player_id: int
    slot: int
    name: str
    chapter: int
    play_time: int
    created_at: datetime
    data: Dict[str, Any]


class ChapterProgress(BaseModel):
    chapter: int
    progress: int


class AchievementResponse(BaseModel):
    id: int
    achievement_id: int
    name: str
    description: str
    unlocked_at: datetime
    reward_claimed: bool


class LeaderboardEntry(BaseModel):
    player_id: int
    nickname: str
    level: int
    value: int
    rank: int


class ClaimRewardRequest(BaseModel):
    achievement_id: int


class ClaimRewardResponse(BaseModel):
    success: bool
    reward: Dict[str, Any]
    message: str
