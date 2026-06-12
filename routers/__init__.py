from .account import router as account_router, get_current_player
from .inventory import router as inventory_router
from .quest import router as quest_router, dialogue_router
from .battle import router as battle_router
from .savegame import router as savegame_router
from .leaderboard import router as leaderboard_router, achievement_router

__all__ = [
    "account_router",
    "inventory_router",
    "quest_router",
    "dialogue_router",
    "battle_router",
    "savegame_router",
    "leaderboard_router",
    "achievement_router",
    "get_current_player"
]
