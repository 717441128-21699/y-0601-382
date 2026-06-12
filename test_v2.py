import requests
import random
import time

BASE = 'http://localhost:8000'
h = {}

print('=' * 60)
print('测试1：冒险日志筛选+状态变化+回合摘要')
print('=' * 60)
r = requests.post(f'{BASE}/api/account/register', json={
    'username': f'advent{random.randint(10000,99999)}',
    'password': '123456', 'nickname': '冒险家'}, timeout=15)
pid = r.json()['id']
h['player-id'] = str(pid)
print(f'注册用户 pid={pid} status={r.status_code}')

r = requests.post(f'{BASE}/api/account/character',
    json={'name': '勇士A', 'class_name': '战士'}, headers=h)
c1 = r.json()['id']
print(f'创建角色1 勇士A cid={c1}')

r = requests.post(f'{BASE}/api/account/character',
    json={'name': '法师B', 'class_name': '法师'}, headers=h)
c2 = r.json()['id']
print(f'创建角色2 法师B cid={c2}')

for i, (cid, eid) in enumerate([(c1, 1), (c1, 2), (c2, 1), (c2, 1), (c1, 4)]):
    r = requests.post(f'{BASE}/api/battle/start',
        json={'enemy_id': eid, 'character_id': cid, 'skill_id': None}, headers=h, timeout=20)
    if r.status_code == 200:
        d = r.json()
        print(f'  战斗{i+1} 角色{cid} vs 敌{eid} 胜利={d["victory"]} 回合={d["battle_log"][-2] if len(d["battle_log"])>2 else "?"}')

print()
print('---- 查询勇士A(c1)全部战斗 ----')
r = requests.get(f'{BASE}/api/battle/records/{c1}?limit=20', headers=h, timeout=15)
d = r.json()
print(f'勇士A总战斗={d["aggregate_stats"]["total_battles"]}, '
      f'胜={d["aggregate_stats"]["wins"]} 负={d["aggregate_stats"]["losses"]}')
for rec in d['records']:
    print(f'  [{rec["timestamp"]}] vs {rec["enemy"]["name"]}(Lv{rec["enemy"]["level"]}) -> '
          f'{rec["result"]["victory"]} 回合={rec["result"]["rounds"]}')
    print(f'    等级变化: 玩家Lv{rec["stats_change"]["player_level"]["before"]}→Lv{rec["stats_change"]["player_level"]["after"]}')
    print(f'    金币变化: {rec["stats_change"]["player_gold"]["before"]}→{rec["stats_change"]["player_gold"]["after"]} '
          f'(+{rec["stats_change"]["player_gold"]["delta"]})')
    if rec['round_summary']:
        print(f'    关键回合: {rec["round_summary"][0]["summary"][:70]}')

print()
print('---- 筛选：只看胜利的 ----')
r = requests.get(f'{BASE}/api/battle/records/{c1}?victory=true&limit=20', headers=h, timeout=15)
d = r.json()
print(f'勇士A胜利战斗数={d["aggregate_stats"]["filtered_count"]}/{d["pagination"]["total"]}')

print()
print('=' * 60)
print('测试2：成就检查 - 只返回本次新解锁')
print('=' * 60)

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=15)
d1 = r.json()
names1 = [a['name'] for a in d1['newly_unlocked']]
print(f'第1次 unlock_check 解锁数={d1["unlocked_count"]} 待领奖={d1["pending_claim_count"]} 新解锁={names1}')

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=15)
d2 = r.json()
names2 = [a['name'] for a in d2['newly_unlocked']]
print(f'第2次（什么都没做）解锁数={d2["unlocked_count"]} 新解锁={names2}（应为0）')

if d1['newly_unlocked']:
    ach_id = d1['newly_unlocked'][0]['id']
    r = requests.post(f'{BASE}/api/achievement/claim', json={'achievement_id': ach_id}, headers=h, timeout=15)
    print(f'领奖 成就{ach_id}: {r.status_code}')

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=15)
d3 = r.json()
names3 = [a['name'] for a in d3['newly_unlocked']]
print(f'领奖后再查 解锁数={d3["unlocked_count"]} 已领奖={d3["claimed_count"]} 新解锁={names3}（应为0）')

print()
print('---- 再打几场解锁更多成就，再查 ----')
for _ in range(3):
    requests.post(f'{BASE}/api/battle/start',
        json={'enemy_id': 1, 'character_id': c1, 'skill_id': None}, headers=h, timeout=20)

r = requests.post(f'{BASE}/api/quest/accept', json={'quest_id': 1}, headers=h, timeout=15)
requests.post(f'{BASE}/api/quest/progress', json={'quest_id': 1, 'progress': 1}, headers=h, timeout=15)
requests.post(f'{BASE}/api/quest/complete', json={'quest_id': 1}, headers=h, timeout=15)

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=15)
d4 = r.json()
names4 = [a['name'] for a in d4['newly_unlocked']]
print(f'行动后 unlock_check 解锁数={d4["unlocked_count"]} 新解锁={names4}')

print()
print('=' * 60)
print('测试3：角色属性分配点')
print('=' * 60)

r = requests.post(f'{BASE}/api/account/add_exp', json={'exp': 500}, headers=h, timeout=15)
print(f'加500经验: {r.status_code}, 升级数={len(r.json().get("level_ups", []))}')

r = requests.get(f'{BASE}/api/account/character/{c1}', headers=h, timeout=15)
d = r.json()
sp = d['stat_points']
print(f'角色1 等级={d["level"]} 可用点数={sp} '
      f'分配攻={d["allocated_stats"]["attack"]} '
      f'最终ATK={d["final_stats"]["attack"]} '
      f'最终HP={d["final_stats"]["max_hp"]}')

if sp > 0:
    alloc_hp, alloc_atk, alloc_def = 2, 1, 1
    total = alloc_hp + alloc_atk + alloc_def
    r = requests.post(f'{BASE}/api/account/character/{c1}/allocate_stats',
        json={'max_hp': alloc_hp, 'attack': alloc_atk, 'defense': alloc_def}, headers=h, timeout=15)
    if r.status_code == 200:
        allocd = r.json()
        print(f'分配点数: 剩余={allocd["stat_points_remaining"]}, '
              f'最终HP={allocd["final_stats"]["max_hp"]}, ATK={allocd["final_stats"]["attack"]}')
    else:
        print(f'  分配失败 {r.status_code}: {r.text}')
elif sp == 0:
    print('  升级经验不足，先打多场')
    for _ in range(8):
        requests.post(f'{BASE}/api/battle/start',
            json={'enemy_id': 2, 'character_id': c1, 'skill_id': None}, headers=h, timeout=20)
    r = requests.get(f'{BASE}/api/account/character/{c1}', headers=h, timeout=15)
    sp = r.json()['stat_points']
    print(f'  打怪后可用点数={sp}')

r = requests.get(f'{BASE}/api/account/character/{c1}', headers=h, timeout=15)
d = r.json()
alloc_atk = d['allocated_stats']['attack']
alloc_hp = d['allocated_stats']['max_hp']
print(f'角色1最终: 基础ATK={d["base_stats"]["attack"]}'
      f' + 分配ATK={alloc_atk} + 装备ATK={d["equipment_bonus"]["attack"]}'
      f' = 最终ATK={d["final_stats"]["attack"]}')

r = requests.get(f'{BASE}/api/battle/simulate?enemy_id=3&character_id={c1}', headers=h, timeout=15)
if r.status_code == 200:
    pred = r.json()
    print(f'战斗预估: ATK={pred["player"]["attack"]} HP={pred["player"]["max_hp"]} '
          f'胜率={pred["battle_analysis"]["victory_chance"]}')

print()
print('=' * 60)
print('测试4：存档完整保存&加载（带装备+多角色+冷却+战斗记录+分配点）')
print('=' * 60)

r = requests.post(f'{BASE}/api/inventory/add_item', json={'item_id': 11, 'quantity': 1}, headers=h, timeout=15)
r = requests.post(f'{BASE}/api/inventory/equip?character_id={c1}',
    json={'item_id': 11, 'slot': 'weapon'}, headers=h, timeout=15)
print(f'角色1装备铁剑: {r.status_code}')

r = requests.get(f'{BASE}/api/battle/skills/{c1}', headers=h, timeout=15)
skill_cd_id = r.json()[0]['id']
print(f'角色1技能id={skill_cd_id} 基础冷却={r.json()[0]["cooldown"]}')

r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 1, 'character_id': c1, 'skill_id': skill_cd_id}, headers=h, timeout=20)
after_cd = r.json().get('cooldowns', {})
print(f'角色1用技能战后冷却={after_cd}')

snap_before = {}
r = requests.get(f'{BASE}/api/account/characters', headers=h, timeout=15)
snap_before['char_names'] = sorted([c['name'] for c in r.json()])
r = requests.get(f'{BASE}/api/account/character/{c1}', headers=h, timeout=15)
snap_before['c1_ATK'] = r.json()['final_stats']['attack']
snap_before['c1_alloc_ATK'] = r.json()['allocated_stats']['attack']
snap_before['c1_stat_points'] = r.json()['stat_points']
r = requests.get(f'{BASE}/api/inventory/equipment?character_id={c1}', headers=h, timeout=15)
snap_before['c1_eq_count'] = len(r.json()['equipment'])
r = requests.get(f'{BASE}/api/battle/cooldowns/{c1}', headers=h, timeout=15)
snap_before['c1_cd_count'] = len(r.json()['cooldowns'])
r = requests.get(f'{BASE}/api/battle/records/{c1}?limit=999', headers=h, timeout=15)
snap_before['c1_records'] = r.json()['aggregate_stats']['total_battles']
r = requests.get(f'{BASE}/api/achievement/player?unlocked=true', headers=h, timeout=15)
snap_before['achievements'] = len(r.json())

print(f'存档前快照: chars={snap_before["char_names"]} c1ATK={snap_before["c1_ATK"]} '
      f'eq={snap_before["c1_eq_count"]} cd={snap_before["c1_cd_count"]} '
      f'recs={snap_before["c1_records"]} ach={snap_before["achievements"]} '
      f'stat_points={snap_before["c1_stat_points"]} allocATK={snap_before["c1_alloc_ATK"]}')

r = requests.post(f'{BASE}/api/savegame/save',
    json={'slot': 3, 'name': '完整状态存档v2'}, headers=h, timeout=30)
save_id = r.json()['save_id']
print(f'存档完成 save_id={save_id} slot={r.json()["slot"]}')

print()
print('---- 故意破坏状态 ----')
requests.post(f'{BASE}/api/inventory/unequip?character_id={c1}', json={'slot': 'weapon'}, headers=h, timeout=15)
requests.post(f'{BASE}/api/battle/reset_cooldowns', json={'character_id': c1}, headers=h, timeout=15)
for _ in range(3):
    requests.post(f'{BASE}/api/battle/start',
        json={'enemy_id': 1, 'character_id': c1, 'skill_id': None}, headers=h, timeout=20)
    requests.post(f'{BASE}/api/battle/start',
        json={'enemy_id': 1, 'character_id': c2, 'skill_id': None}, headers=h, timeout=20)
# 加一个额外角色来影响列表
r = requests.post(f'{BASE}/api/account/character',
    json={'name': '临时角色', 'class_name': '弓箭手'}, headers=h, timeout=15)
print(f'破坏后：脱装备、清冷却、多加战斗、额外加1个临时角色')

r = requests.post(f'{BASE}/api/savegame/load/{save_id}', headers=h, timeout=30)
print(f'加载存档: {r.json()["success"]}')

r = requests.get(f'{BASE}/api/account/characters', headers=h, timeout=15)
chars_loaded = sorted([c['name'] for c in r.json()])
# 加载后用第一个同名字符串代替 c1（因为删除再重建会变id）
c1_new = next((c['id'] for c in r.json() if c['name'] == '勇士A'), None)
c2_new = next((c['id'] for c in r.json() if c['name'] == '法师B'), None)
print(f'加载后角色名={chars_loaded}, 勇士A新id={c1_new} 法师B新id={c2_new}')

snap_after = {}
r = requests.get(f'{BASE}/api/account/character/{c1_new}', headers=h, timeout=15)
snap_after['c1_ATK'] = r.json()['final_stats']['attack']
snap_after['c1_alloc_ATK'] = r.json()['allocated_stats']['attack']
snap_after['c1_stat_points'] = r.json()['stat_points']
r = requests.get(f'{BASE}/api/inventory/equipment?character_id={c1_new}', headers=h, timeout=15)
snap_after['c1_eq_count'] = len(r.json()['equipment'])
r = requests.get(f'{BASE}/api/battle/cooldowns/{c1_new}', headers=h, timeout=15)
snap_after['c1_cd_count'] = len(r.json()['cooldowns'])
r = requests.get(f'{BASE}/api/battle/records/{c1_new}?limit=999', headers=h, timeout=15)
snap_after['c1_records'] = r.json()['aggregate_stats']['total_battles']
r = requests.get(f'{BASE}/api/achievement/player?unlocked=true', headers=h, timeout=15)
snap_after['achievements'] = len(r.json())
snap_after['char_names'] = chars_loaded

print()
print('存档恢复对比表:')
print(f'  角色名:   保存={snap_before["char_names"]}')
print(f'            恢复={snap_after["char_names"]} 一致={set(snap_before["char_names"]) == set(snap_after["char_names"])}')
print(f'  勇士A ATK: 保存={snap_before["c1_ATK"]} 恢复={snap_after["c1_ATK"]} 一致={snap_before["c1_ATK"] == snap_after["c1_ATK"]}')
print(f'  勇士A分配ATK: 保存={snap_before["c1_alloc_ATK"]} 恢复={snap_after["c1_alloc_ATK"]} 一致={snap_before["c1_alloc_ATK"] == snap_after["c1_alloc_ATK"]}')
print(f'  勇士A可用点: 保存={snap_before["c1_stat_points"]} 恢复={snap_after["c1_stat_points"]} 一致={snap_before["c1_stat_points"] == snap_after["c1_stat_points"]}')
print(f'  勇士A装备数: 保存={snap_before["c1_eq_count"]} 恢复={snap_after["c1_eq_count"]} 一致={snap_before["c1_eq_count"] == snap_after["c1_eq_count"]}')
print(f'  勇士A冷却数: 保存={snap_before["c1_cd_count"]} 恢复={snap_after["c1_cd_count"]} 一致={snap_before["c1_cd_count"] == snap_after["c1_cd_count"]}')
print(f'  勇士A战斗数: 保存={snap_before["c1_records"]} 恢复={snap_after["c1_records"]} 一致={snap_before["c1_records"] == snap_after["c1_records"]}')
print(f'  玩家成就数: 保存={snap_before["achievements"]} 恢复={snap_after["achievements"]} 一致={snap_before["achievements"] == snap_after["achievements"]}')

print()
print('=' * 60)
print('全部测试完成!')
print('=' * 60)
