import requests
import json

BASE = 'http://localhost:8000'
headers = {}

print('=' * 60)
print('测试1：对话接口 - list / history / current_branch')
print('=' * 60)

import random
r = requests.post(f'{BASE}/api/account/register',
    json={'username': f'test{random.randint(1000,9999)}', 'password': '123456', 'nickname': '测试玩家'})
print(f'注册用户: {r.status_code}')
player_id = r.json()['id']
headers['player-id'] = str(player_id)

r = requests.get(f'{BASE}/api/dialogue/list?chapter=1')
print(f'对话列表: {r.status_code}, 数量={len(r.json())}')
if r.status_code == 200:
    print(f'  前2个对话ID: {[d["id"] for d in r.json()[:2]]}')

r = requests.get(f'{BASE}/api/dialogue/1')
print(f'对话详情ID=1: {r.status_code}')
if r.status_code == 200:
    print(f'  内容: {r.json()["content"][:30]}...')

r = requests.post(f'{BASE}/api/dialogue/choice',
    json={'dialogue_id': 1, 'choice_id': 1, 'branch_path': 'main_help'},
    headers=headers)
print(f'做出选择: {r.status_code}')
if r.status_code == 200:
    print(f'  结果: {r.json()["message"]}')

r = requests.get(f'{BASE}/api/dialogue/history', headers=headers)
print(f'对话历史: {r.status_code}, 数量={len(r.json())}')
if r.status_code == 200 and r.json():
    print(f'  最新记录: branch={r.json()[0]["branch_path"]}')

r = requests.get(f'{BASE}/api/dialogue/current_branch', headers=headers)
print(f'当前分支: {r.status_code}')
if r.status_code == 200:
    print(f'  current_branch={r.json()["current_branch"]}, last_choice_id={r.json()["last_choice_id"]}')

print()
print('=' * 60)
print('测试2：任务进度 - ready_to_complete 后完成任务')
print('=' * 60)

r = requests.post(f'{BASE}/api/quest/accept',
    json={'quest_id': 1}, headers=headers)
print(f'接取任务1: {r.status_code}')

r = requests.post(f'{BASE}/api/quest/progress',
    json={'quest_id': 1, 'progress': 1}, headers=headers)
print(f'增加进度: {r.status_code}')
if r.status_code == 200:
    print(f'  can_complete={r.json()["can_complete"]}')

r = requests.get(f'{BASE}/api/quest/list?status=ready_to_complete', headers=headers)
print(f'可完成任务列表: {r.status_code}, 数量={len(r.json())}')

r = requests.post(f'{BASE}/api/quest/complete',
    json={'quest_id': 1}, headers=headers)
print(f'完成任务: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  奖励: exp={data["rewards"]["exp"]}, gold={data["rewards"]["gold"]}, 道具数={len(data["rewards"]["items"])}')
    print(f'  level_ups={data.get("level_ups", [])}')
else:
    print(f'  错误: {r.text}')

print()
print('=' * 60)
print('测试3：技能冷却跨战斗生效')
print('=' * 60)

r = requests.post(f'{BASE}/api/account/character',
    json={'name': '测试战士', 'class_name': '战士'},
    headers=headers)
print(f'创建角色: {r.status_code}')
char_id = r.json()['id']
print(f'  角色ID={char_id}, class={r.json()["class_name"]}')

r = requests.get(f'{BASE}/api/battle/skills/{char_id}', headers=headers)
print(f'角色技能: {r.status_code}, 数量={len(r.json())}')
if r.status_code == 200:
    for s in r.json():
        print(f'  技能: {s["name"]}, cd={s["cooldown"]}, 当前冷却={s["current_cooldown"]}')

r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 1, 'character_id': char_id, 'skill_id': 1},
    headers=headers)
print(f'第一次战斗(用技能): {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  胜利={data["victory"]}, 冷却={data["cooldowns"]}')

r = requests.get(f'{BASE}/api/battle/cooldowns/{char_id}', headers=headers)
print(f'当前技能冷却: {r.status_code}')
if r.status_code == 200:
    print(f'  {r.json()}')

r = requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id': 1, 'character_id': char_id, 'skill_id': 1},
    headers=headers)
print(f'第二次战斗(同一技能，应冷却): {r.status_code}')
if r.status_code == 200:
    data = r.json()
    logs = data['battle_log']
    has_cd_msg = any('冷却' in log for log in logs)
    print(f'  胜利={data["victory"]}, 是否有冷却提示={has_cd_msg}')

print()
print('=' * 60)
print('测试4：装备支持指定角色')
print('=' * 60)

r = requests.post(f'{BASE}/api/account/character',
    json={'name': '测试法师', 'class_name': '法师'},
    headers=headers)
print(f'创建第二个角色(法师): {r.status_code}')
char2_id = r.json()['id']
print(f'  角色2 ID={char2_id}')

r = requests.post(f'{BASE}/api/inventory/add_item',
    json={'item_id': 11, 'quantity': 2}, headers=headers)
print(f'添加2把铁剑到背包: {r.status_code}')

r = requests.post(f'{BASE}/api/inventory/equip?character_id={char_id}',
    json={'item_id': 11, 'slot': 'weapon'}, headers=headers)
print(f'角色1装备铁剑: {r.status_code}')
if r.status_code == 200:
    print(f'  character_id={r.json()["character_id"]}, item={r.json()["item_name"]}')

r = requests.get(f'{BASE}/api/inventory/equipment?character_id={char_id}', headers=headers)
print(f'角色1装备: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  装备数={len(data["equipment"])}, 总攻击加成={data["total_stats"].get("attack", 0)}')

r = requests.get(f'{BASE}/api/inventory/equipment?character_id={char2_id}', headers=headers)
print(f'角色2装备: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  装备数={len(data["equipment"])} (应该为0)')

r = requests.post(f'{BASE}/api/inventory/equip?character_id={char2_id}',
    json={'item_id': 11, 'slot': 'weapon'}, headers=headers)
print(f'角色2装备铁剑: {r.status_code}')
if r.status_code == 200:
    print(f'  character_id={r.json()["character_id"]}, item={r.json()["item_name"]}')

r = requests.get(f'{BASE}/api/inventory/equipment?character_id={char_id}', headers=headers)
print(f'再看角色1装备数: {len(r.json()["equipment"])} (应该还是1)')

print()
print('=' * 60)
print('测试5：成就解锁检查和自动存档')
print('=' * 60)

r = requests.get(f'{BASE}/api/achievement/unlock_check', headers=headers)
print(f'成就解锁检查: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  success={data["success"]}, 新解锁={data["unlocked_count"]}')
else:
    print(f'  错误: {r.text}')

r = requests.get(f'{BASE}/api/achievement/1', headers=headers)
print(f'成就1详情: {r.status_code}')
if r.status_code == 200:
    print(f'  名称: {r.json()["achievement"]["name"]}')

r = requests.get(f'{BASE}/api/savegame/auto_save', headers=headers)
print(f'自动存档: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'  success={data["success"]}, slot={data["slot"]}, name={data["name"]}')
else:
    print(f'  错误: {r.text}')

r = requests.get(f'{BASE}/api/savegame/list', headers=headers)
print(f'存档列表: {r.status_code}, 数量={len(r.json())}')

if r.json():
    save_id = r.json()[0]['id']
    r2 = requests.get(f'{BASE}/api/savegame/{save_id}', headers=headers)
    print(f'存档{save_id}详情: {r2.status_code}')

print()
print('=' * 60)
print('所有测试完成！')
print('=' * 60)
