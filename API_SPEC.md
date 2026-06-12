# 角色扮演游戏后端服务 API 文档

## 服务信息
- **服务名称**: 角色扮演游戏后端服务
- **版本**: 1.0.0
- **基础地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs (Swagger UI)
- **数据库**: SQLite (game.db)

## 认证方式
所有需要登录的接口需在请求头中携带 `player-id: <玩家ID>`

---

## 1. 账号角色模块 (Account)

### 1.1 注册账号
- **接口**: `POST /api/account/register`
- **请求体**:
  ```json
  {
    "username": "string",
    "password": "string",
    "nickname": "string"
  }
  ```
- **返回**: 玩家信息

### 1.2 登录
- **接口**: `POST /api/account/login`
- **请求体**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **返回**: `player_id` 用于后续接口认证

### 1.3 登出
- **接口**: `POST /api/account/logout`
- **认证**: 需要

### 1.4 获取/更新个人信息
- **获取**: `GET /api/account/profile`
- **更新**: `PUT /api/account/profile`
- **更新请求体**:
  ```json
  {
    "nickname": "可选",
    "avatar": "可选"
  }
  ```

### 1.5 创建角色
- **接口**: `POST /api/account/character`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "name": "角色名",
    "class_name": "战士/法师/弓箭手/刺客"
  }
  ```

### 1.6 获取角色列表
- **接口**: `GET /api/account/characters`
- **认证**: 需要

### 1.7 获取角色详情
- **接口**: `GET /api/account/character/{character_id}`
- **认证**: 需要

### 1.8 更新角色头像
- **接口**: `PUT /api/account/character/{character_id}/avatar`
- **认证**: 需要

---

## 2. 属性成长模块 (Attribute)

### 2.1 查询升级所需经验
- **接口**: `GET /api/account/exp_required?level=1`

### 2.2 增加经验
- **接口**: `POST /api/account/add_exp`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "exp": 100
  }
  ```

### 2.3 增减金币
- **接口**: `POST /api/account/add_gold`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "gold": 100
  }
  ```
- **说明**: 负数为扣除金币

---

## 3. 背包装备模块 (Inventory)

### 3.1 获取背包物品
- **接口**: `GET /api/inventory/items`
- **认证**: 需要

### 3.2 添加物品
- **接口**: `POST /api/inventory/add_item`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "item_id": 1,
    "quantity": 1
  }
  ```

### 3.3 移除物品
- **接口**: `POST /api/inventory/remove_item`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "item_id": 1,
    "quantity": 1
  }
  ```

### 3.4 获取装备
- **接口**: `GET /api/inventory/equipment?character_id=0`
- **认证**: 需要

### 3.5 装备物品
- **接口**: `POST /api/inventory/equip`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "item_id": 11,
    "slot": "weapon"
  }
  ```
- **槽位**: weapon, armor, shield, accessory

### 3.6 卸下装备
- **接口**: `POST /api/inventory/unequip`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "slot": "weapon"
  }
  ```

### 3.7 获取所有物品列表
- **接口**: `GET /api/inventory/items/all`

---

## 4. 任务状态模块 (Quest)

### 4.1 获取可接任务
- **接口**: `GET /api/quest/available`
- **认证**: 需要

### 4.2 获取玩家任务列表
- **接口**: `GET /api/quest/list?status=in_progress`
- **认证**: 需要
- **状态**: available, in_progress, ready_to_complete, completed

### 4.3 接取任务
- **接口**: `POST /api/quest/accept`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "quest_id": 1
  }
  ```

### 4.4 完成任务
- **接口**: `POST /api/quest/complete`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "quest_id": 1
  }
  ```

### 4.5 更新任务进度
- **接口**: `POST /api/quest/progress`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "quest_id": 1,
    "progress": 1
  }
  ```

---

## 5. 对话选择模块 (Dialogue)

### 5.1 获取对话详情
- **接口**: `GET /api/dialogue/{dialogue_id}`

### 5.2 获取章节对话列表
- **接口**: `GET /api/dialogue/list?chapter=1`

### 5.3 做出对话选择
- **接口**: `POST /api/dialogue/choice`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "dialogue_id": 1,
    "choice_id": 1,
    "branch_path": "main_help"
  }
  ```

### 5.4 获取对话历史
- **接口**: `GET /api/dialogue/history`
- **认证**: 需要

### 5.5 获取当前分支
- **接口**: `GET /api/dialogue/current_branch`
- **认证**: 需要

---

## 6. 战斗结算模块 (Battle)

### 6.1 获取敌人列表
- **接口**: `GET /api/battle/enemies?level=1`

### 6.2 获取敌人详情
- **接口**: `GET /api/battle/enemy/{enemy_id}`

### 6.3 获取角色技能
- **接口**: `GET /api/battle/skills/{character_id}`
- **认证**: 需要

### 6.4 开始战斗
- **接口**: `POST /api/battle/start`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "enemy_id": 1,
    "character_id": 1,
    "skill_id": 1
  }
  ```
- **返回**: 战斗结果、经验、金币、掉落物品、战斗日志、冷却时间

### 6.5 战斗模拟
- **接口**: `GET /api/battle/simulate?enemy_id=1&character_id=1&skill_id=1`
- **认证**: 需要

### 6.6 恢复生命值
- **接口**: `POST /api/battle/restore_hp`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "character_id": 1,
    "amount": 0
  }
  ```
- **说明**: amount=0 时恢复全部

### 6.7 获取技能冷却
- **接口**: `GET /api/battle/cooldowns/{character_id}`
- **认证**: 需要

### 6.8 重置技能冷却
- **接口**: `POST /api/battle/reset_cooldowns`
- **认证**: 需要

---

## 7. 存档读取模块 (SaveGame)

### 7.1 保存游戏
- **接口**: `POST /api/savegame/save`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "slot": 1,
    "name": "自定义存档名"
  }
  ```
- **槽位**: 0-9，0为自动存档

### 7.2 获取存档列表
- **接口**: `GET /api/savegame/list`
- **认证**: 需要

### 7.3 获取存档详情
- **接口**: `GET /api/savegame/{save_id}`
- **认证**: 需要

### 7.4 加载存档
- **接口**: `POST /api/savegame/load/{save_id}`
- **认证**: 需要

### 7.5 删除存档
- **接口**: `DELETE /api/savegame/{save_id}`
- **认证**: 需要

### 7.6 更新章节进度
- **接口**: `PUT /api/savegame/chapter_progress`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "chapter": 2,
    "progress": 5
  }
  ```

### 7.7 增加游戏时长
- **接口**: `GET /api/savegame/play_time/add?seconds=60`
- **认证**: 需要

### 7.8 快速存档
- **接口**: `GET /api/savegame/auto_save`
- **认证**: 需要

---

## 8. 排行榜模块 (Leaderboard)

### 8.1 等级排行榜
- **接口**: `GET /api/leaderboard/level?limit=100`

### 8.2 金币排行榜
- **接口**: `GET /api/leaderboard/gold?limit=100`

### 8.3 游戏时长排行榜
- **接口**: `GET /api/leaderboard/play_time?limit=100`

### 8.4 速通排行榜
- **接口**: `GET /api/leaderboard/speedrun?limit=100`

### 8.5 成就数量排行榜
- **接口**: `GET /api/leaderboard/achievement_count?limit=100`

### 8.6 查询玩家排名
- **接口**: `GET /api/leaderboard/query?category=level`
- **认证**: 需要
- **分类**: level, gold, play_time, speedrun, achievement_count

---

## 9. 成就系统 (Achievement)

### 9.1 获取所有成就
- **接口**: `GET /api/achievement/all`

### 9.2 获取玩家成就
- **接口**: `GET /api/achievement/player?unlocked=true`
- **认证**: 需要

### 9.3 获取成就详情
- **接口**: `GET /api/achievement/{achievement_id}`
- **认证**: 需要

### 9.4 领取成就奖励
- **接口**: `POST /api/achievement/claim`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "achievement_id": 1
  }
  ```
- **限制**: 已领取的奖励不能重复领取

### 9.5 检查成就解锁
- **接口**: `GET /api/achievement/unlock_check`
- **认证**: 需要

---

## 数据结构说明

### 职业 (Class)
| 职业 | 特点 | 初始属性 |
|------|------|----------|
| 战士 | 高血量高防御 | HP:150, MP:30, 攻击:12, 防御:8, 速度:4 |
| 法师 | 高魔法伤害 | HP:80, MP:100, 攻击:6, 防御:3, 速度:5 |
| 弓箭手 | 高攻速高暴击 | HP:100, MP:60, 攻击:14, 防御:4, 速度:8 |
| 刺客 | 高爆发高闪避 | HP:90, MP:50, 攻击:16, 防御:3, 速度:10 |

### 物品稀有度
- common (普通)
- uncommon (优秀)
- rare (稀有)

### 物品类型
- consumable (消耗品)
- equipment (装备)
- material (材料)

### 装备槽位
- weapon (武器)
- armor (护甲)
- shield (盾牌)
- accessory (饰品)

### 任务类型
- main (主线任务)
- side (支线任务)

### 成就类型
- level (等级成就)
- combat (战斗成就)
- wealth (财富成就)
- quest (任务成就)
- boss (BOSS击杀)
- speedrun (速通成就)
- completion (完成度成就)

---

## 快速开始

### 1. 注册账号
```bash
curl -X POST http://localhost:8000/api/account/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456","nickname":"测试玩家"}'
```

### 2. 登录获取 player_id
```bash
curl -X POST http://localhost:8000/api/account/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
```

### 3. 创建角色
```bash
curl -X POST http://localhost:8000/api/account/character \
  -H "Content-Type: application/json" \
  -H "player-id: 1" \
  -d '{"name":"勇者","class_name":"战士"}'
```

### 4. 开始战斗
```bash
curl -X POST http://localhost:8000/api/battle/start \
  -H "Content-Type: application/json" \
  -H "player-id: 1" \
  -d '{"enemy_id":1,"character_id":1,"skill_id":1}'
```
