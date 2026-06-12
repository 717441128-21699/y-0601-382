import requests
import random

BASE = 'http://localhost:8000'
headers = {}

print('='*60)
print('测试1：技能冷却跨多场战斗 - 连续两场同冷却技能')
print('='*60)
r = requests.post(f'{BASE}/api/account/register',
    json={'username': f'test{random.randint(10000,99999)}',
          'password': '123456', 'nickname': '完整测试员'})
player_id = r.json()['id']
headers['player-id'] = str(player_id)
print(f'注册用户 player_id={player_id}, status={r.status_code}')

r = requests.post(f'{BASE}/api/account/character',
    json={'name': '冷却战士', 'class_name': '战士'}, headers=headers)
char_id = r.json()['id']
print(f'创建战士角色 char_id={char_id}')

r = requests.get(f'{BASE}/api/battle/skills/{char_id}', headers=headers)
skill_id = r.json()[0]['id']
skill_cd = r.json()[0]['cooldown']
skill_name = r.json()[0]['name']
print(f'角色技能: {skill_name}, 基础冷却={skill_cd}回合')

r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 1, 'character_id': char_id, 'skill_id': skill_id}, headers=headers)
res = r.json()
print(f'第1场战斗胜利={res["victory"]}, 战后冷却={res["cooldowns"]}')

r = requests.get(f'{BASE}/api/battle/cooldowns/{char_id}', headers=headers)
cd_before = r.json()['cooldowns']
print(f'战斗1后冷却查询: {cd_before}')

r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 1, 'character_id': char_id, 'skill_id': skill_id}, headers=headers)
res2 = r.json()
logs = res2['battle_log']
cd_msg = any(skill_name in l and '冷却' in l for l in logs)
print(f'第2场战斗胜利={res2["victory"]}, 有冷却提示={cd_msg}, 冷却={res2["cooldowns"]}')
if cd_msg:
    for l in logs:
        if '冷却' in l:
            print(f'  → {l}')

print()
print('='*60)
print('测试2：成就 - 真实行为更新进度，unlock_check检查解锁')
print('='*60)

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=headers)
d = r.json()
print(f'新号未行动时 unlock_check 解锁数={d["unlocked_count"]}')
new_ach_types = [a['condition_type'] for a in d['newly_unlocked']]
print(f'  解锁成就类型: {new_ach_types}')

r = requests.post(f'{BASE}/api/quest/accept', json={'quest_id': 1}, headers=headers)
print(f'接取任务1: {r.status_code}')
r = requests.post(f'{BASE}/api/quest/progress', json={'quest_id': 1, 'progress': 1}, headers=headers)
print(f'进度加满: {r.status_code}, can_complete={r.json()["can_complete"]}')
r = requests.post(f'{BASE}/api/quest/complete', json={'quest_id': 1}, headers=headers)
rew = r.json().get('rewards', {})
print(f'完成任务1: exp={rew.get("exp")}, gold={rew.get("gold")}')

for enemy_id in [1, 1, 1]:
    r = requests.post(f'{BASE}/api/battle/start',
        json={'enemy_id': enemy_id, 'character_id': char_id, 'skill_id': None}, headers=headers)

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=headers)
d = r.json()
names = [a['name'] for a in d['newly_unlocked']]
print(f'打怪+完成任务后 unlock_check 解锁数={d["unlocked_count"]}')
print(f'  解锁成就名: {names}')

print()
print('='*60)
print('测试3：角色战斗记录接口')
print('='*60)

r = requests.get(f'{BASE}/api/battle/records/{char_id}?limit=10', headers=headers)
d = r.json()
print(f'战斗记录总数={d["total_records"]}')
for i, rec in enumerate(d['records']):
    print(f'  #{i+1} 敌人={rec["enemy_name"]}(Lv{rec["enemy_level"]}) 胜利={rec["victory"]} '
          f'回合={rec["rounds"]} EXP={rec["exp_gained"]} 金币={rec["gold_gained"]} '
          f'技能={[s["name"] for s in rec["skills_used"]]} 掉落={len(rec["items_dropped"])}项')

print()
print('='*60)
print('测试4：角色详情返回装备加成后最终数值')
print('='*60)

r = requests.get(f'{BASE}/api/account/character/{char_id}', headers=headers)
d = r.json()
print(f'角色: {d["name"]}({d["class_name"]}) Lv{d["level"]}')
print(f'  基础数值: HP={d["base_stats"]["max_hp"]} ATK={d["base_stats"]["attack"]} DEF={d["base_stats"]["defense"]}')
print(f'  装备加成: HP={d["equipment_bonus"]["max_hp"]} ATK={d["equipment_bonus"]["attack"]} DEF={d["equipment_bonus"]["defense"]}')
print(f'  最终数值: HP={d["final_stats"]["max_hp"]} ATK={d["final_stats"]["attack"]} DEF={d["final_stats"]["defense"]}')
print(f'  已装备栏位: {list(d["equipped_items"].keys())}')

r = requests.post(f'{BASE}/api/inventory/add_item', json={'item_id': 11, 'quantity': 1}, headers=headers)
r = requests.post(f'{BASE}/api/inventory/equip?character_id={char_id}',
    json={'item_id': 11, 'slot': 'weapon'}, headers=headers)
print(f'\n装备铁剑后: status={r.status_code}')

r = requests.get(f'{BASE}/api/account/character/{char_id}', headers=headers)
d2 = r.json()
print(f'  加成后ATK: 装备前={d["final_stats"]["attack"]} → 装备后={d2["final_stats"]["attack"]}')
print(f'  装备栏位: {d2["equipped_items"]}')

r = requests.get(f'{BASE}/api/battle/simulate?enemy_id=3&character_id={char_id}', headers=headers)
pred = r.json()
print(f'\n战斗预估: ATK={pred["player"]["attack"]} HP={pred["player"]["max_hp"]} '
      f'击杀回合={pred["battle_analysis"]["turns_to_kill_enemy"]} 胜率={pred["battle_analysis"]["victory_chance"]}')

print()
print('='*60)
print('测试5：存档保存完整状态并加载恢复')
print('='*60)

r = requests.post(f'{BASE}/api/dialogue/choice',
    json={'dialogue_id': 2, 'choice_id': 1, 'branch_path': 'forest_path'}, headers=headers)
print(f'保存对话分支: {r.status_code}')

r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 2, 'character_id': char_id, 'skill_id': skill_id}, headers=headers)
after_save_cd = r.json()['cooldowns']
print(f'战前使用技能冷却={after_save_cd}')

r = requests.post(f'{BASE}/api/savegame/save', json={'slot': 5, 'name': '完整状态存档'}, headers=headers)
save_id = r.json()['save_id']
print(f'手动存档: save_id={save_id} slot={r.json()["slot"]}')

print(f'\n保存前关键状态快照:')
snapshot = {}
r = requests.get(f'{BASE}/api/account/character/{char_id}', headers=headers)
snapshot['atk'] = r.json()['final_stats']['attack']
r = requests.get(f'{BASE}/api/battle/cooldowns/{char_id}', headers=headers)
snapshot['cd'] = list(r.json()['cooldowns'].keys())
r = requests.get(f'{BASE}/api/dialogue/current_branch', headers=headers)
snapshot['branch'] = r.json().get('current_branch')
r = requests.get(f'{BASE}/api/quest/list?status=completed', headers=headers)
snapshot['completed_quests'] = len(r.json())
r = requests.get(f'{BASE}/api/battle/records/{char_id}?limit=999', headers=headers)
snapshot['battle_count'] = r.json()['total_records']
r = requests.get(f'{BASE}/api/achievement/player?unlocked=true', headers=headers)
snapshot['ach_count'] = len(r.json())
print(f'  角色ATK={snapshot["atk"]} 冷却技能数={len(snapshot["cd"])} '
      f'分支={snapshot["branch"]} 已完成任务={snapshot["completed_quests"]} '
      f'战斗数={snapshot["battle_count"]} 成就数={snapshot["ach_count"]}')

r = requests.post(f'{BASE}/api/battle/reset_cooldowns', json={'character_id': char_id}, headers=headers)
r = requests.post(f'{BASE}/api/inventory/unequip?character_id={char_id}', json={'slot': 'weapon'}, headers=headers)
r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 4, 'character_id': char_id, 'skill_id': None}, headers=headers)
print(f'\n故意改变状态：脱装备 + 清冷却 + 多打一场')

r = requests.post(f'{BASE}/api/savegame/load/{save_id}', headers=headers)
load_res = r.json()
print(f'加载存档: success={load_res["success"]}')

r = requests.get(f'{BASE}/api/account/characters', headers=headers)
chars = r.json()
char_id = chars[0]['id']
print(f'加载后第一个角色ID更新为: {char_id}')

print(f'\n加载后状态对比:')
r = requests.get(f'{BASE}/api/account/character/{char_id}', headers=headers)
restored_atk = r.json()['final_stats']['attack']
r = requests.get(f'{BASE}/api/battle/cooldowns/{char_id}', headers=headers)
restored_cd = list(r.json()['cooldowns'].keys())
r = requests.get(f'{BASE}/api/dialogue/current_branch', headers=headers)
restored_branch = r.json().get('current_branch')
r = requests.get(f'{BASE}/api/quest/list?status=completed', headers=headers)
restored_q = len(r.json())
r = requests.get(f'{BASE}/api/battle/records/{char_id}?limit=999', headers=headers)
restored_b = r.json()['total_records']
r = requests.get(f'{BASE}/api/achievement/player?unlocked=true', headers=headers)
restored_a = len(r.json())

print(f'  角色ATK: 保存={snapshot["atk"]} 恢复={restored_atk} 一致={snapshot["atk"] == restored_atk}')
print(f'  冷却技能: 保存数={len(snapshot["cd"])} 恢复数={len(restored_cd)} 一致={len(snapshot["cd"]) == len(restored_cd)}')
print(f'  对话分支: 保存={snapshot["branch"]} 恢复={restored_branch} 一致={snapshot["branch"] == restored_branch}')
print(f'  已完成任务: 保存={snapshot["completed_quests"]} 恢复={restored_q} 一致={snapshot["completed_quests"] == restored_q}')
print(f'  战斗记录数: 保存={snapshot["battle_count"]} 恢复={restored_b} 一致={snapshot["battle_count"] == restored_b}')
print(f'  成就数: 保存={snapshot["ach_count"]} 恢复={restored_a} 一致={snapshot["ach_count"] == restored_a}')

print()
print('='*60)
print('所有测试完成！')
print('='*60)
