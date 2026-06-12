from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    avatar = Column(String)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    current_chapter = Column(Integer, default=1)
    chapter_progress = Column(Integer, default=0)
    play_time = Column(Integer, default=0)
    is_online = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    characters = relationship("Character", back_populates="player")
    inventory = relationship("Inventory", back_populates="player")
    equipment = relationship("Equipment", back_populates="player")
    quests = relationship("PlayerQuest", back_populates="player")
    dialogue_choices = relationship("DialogueChoice", back_populates="player")
    save_games = relationship("SaveGame", back_populates="player")
    achievements = relationship("PlayerAchievement", back_populates="player")
    cooldowns = relationship("SkillCooldown", back_populates="player")


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    max_hp = Column(Integer, default=100)
    current_hp = Column(Integer, default=100)
    max_mp = Column(Integer, default=50)
    current_mp = Column(Integer, default=50)
    attack = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    speed = Column(Integer, default=5)
    avatar = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="characters")
    skills = relationship("CharacterSkill", back_populates="character")


class ClassData(Base):
    __tablename__ = "class_data"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, unique=True, nullable=False)
    description = Column(String)
    base_hp = Column(Integer, default=100)
    base_mp = Column(Integer, default=50)
    base_attack = Column(Integer, default=10)
    base_defense = Column(Integer, default=5)
    base_speed = Column(Integer, default=5)
    hp_per_level = Column(Integer, default=10)
    mp_per_level = Column(Integer, default=5)
    attack_per_level = Column(Integer, default=2)
    defense_per_level = Column(Integer, default=1)
    speed_per_level = Column(Integer, default=1)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, nullable=False)
    sub_type = Column(String)
    rarity = Column(String, default="common")
    price = Column(Integer, default=0)
    stats = Column(JSON, default={})
    required_level = Column(Integer, default=1)
    stackable = Column(Boolean, default=True)
    max_stack = Column(Integer, default=99)
    is_equipment = Column(Boolean, default=False)
    slot = Column(String)


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="inventory")
    item = relationship("Item")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"))
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    slot = Column(String, nullable=False)
    equipped_at = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="equipment")
    item = relationship("Item")


class Quest(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, default="main")
    chapter = Column(Integer, default=1)
    required_level = Column(Integer, default=1)
    exp_reward = Column(Integer, default=0)
    gold_reward = Column(Integer, default=0)
    item_rewards = Column(JSON, default=[])
    pre_quest_id = Column(Integer, ForeignKey("quests.id"))


class PlayerQuest(Base):
    __tablename__ = "player_quests"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False)
    status = Column(String, default="available")
    progress = Column(Integer, default=0)
    target_progress = Column(Integer, default=1)
    accepted_at = Column(DateTime)
    completed_at = Column(DateTime)
    reward_claimed = Column(Boolean, default=False)

    player = relationship("Player", back_populates="quests")
    quest = relationship("Quest")


class Dialogue(Base):
    __tablename__ = "dialogues"

    id = Column(Integer, primary_key=True, index=True)
    npc_id = Column(Integer, default=0)
    chapter = Column(Integer, default=1)
    content = Column(String, nullable=False)
    choices = Column(JSON, default=[])


class DialogueChoice(Base):
    __tablename__ = "dialogue_choices"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    dialogue_id = Column(Integer, ForeignKey("dialogues.id"), nullable=False)
    choice_id = Column(Integer, nullable=False)
    branch_path = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())

    player = relationship("Player", back_populates="dialogue_choices")


class Enemy(Base):
    __tablename__ = "enemies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    level = Column(Integer, default=1)
    max_hp = Column(Integer, default=50)
    attack = Column(Integer, default=8)
    defense = Column(Integer, default=3)
    speed = Column(Integer, default=4)
    exp_reward = Column(Integer, default=10)
    gold_reward = Column(Integer, default=5)
    loot_table = Column(JSON, default=[])
    skills = Column(JSON, default=[])


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    class_name = Column(String)
    damage = Column(Integer, default=0)
    heal = Column(Integer, default=0)
    mp_cost = Column(Integer, default=10)
    cooldown = Column(Integer, default=0)
    required_level = Column(Integer, default=1)
    effect_type = Column(String, default="damage")
    target_type = Column(String, default="single")


class CharacterSkill(Base):
    __tablename__ = "character_skills"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    level = Column(Integer, default=1)

    character = relationship("Character", back_populates="skills")
    skill = relationship("Skill")


class SkillCooldown(Base):
    __tablename__ = "skill_cooldowns"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    remaining_turns = Column(Integer, default=0)
    battle_id = Column(String)

    player = relationship("Player", back_populates="cooldowns")


class SaveGame(Base):
    __tablename__ = "save_games"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    slot = Column(Integer, nullable=False)
    name = Column(String, default="Auto Save")
    chapter = Column(Integer, default=1)
    chapter_progress = Column(Integer, default=0)
    play_time = Column(Integer, default=0)
    data = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    player = relationship("Player", back_populates="save_games")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String, default="general")
    condition_type = Column(String, nullable=False)
    condition_value = Column(Integer, default=1)
    exp_reward = Column(Integer, default=0)
    gold_reward = Column(Integer, default=0)
    item_reward = Column(JSON)
    is_rare = Column(Boolean, default=False)


class PlayerAchievement(Base):
    __tablename__ = "player_achievements"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    progress = Column(Integer, default=0)
    unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime)
    reward_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime)

    player = relationship("Player", back_populates="achievements")
    achievement = relationship("Achievement")


class Leaderboard(Base):
    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    nickname = Column(String, nullable=False)
    category = Column(String, nullable=False)
    value = Column(Integer, default=0)
    rank = Column(Integer)
    last_updated = Column(DateTime, server_default=func.now())
