import requests, random, json, sys

BASE = 'http://localhost:8000'
h = {}

def prnt(s):
    print(s); sys.stdout.flush()

prnt('='*60)
prnt('快速综合测试（4项功能）')
prnt('='*60)
r = requests.post(f'{BASE}/api/account/register', json={
    'username': f'q{random.randint(10000,99999)}',
    'password': '123456', 'nickname': '快测'}, timeout=20)
h['player-id'] = str(r.json()['id'])
prnt(f'注册OK pid={r.json()["id"]}')

# 角色
c1 = requests.post(f'{BASE}/api/account/character',
    json={'name':'战1','class_name':'战士'}, headers=h, timeout=15).json()['id']
c2 = requests.post(f'{BASE}/api/account/character',
    json={'name':'法2','class_name':'法师'}, headers=h, timeout=15).json()['id']
prnt(f'角色c1={c1} c2={c2}')

# 需求1 + 需求4准备：先打几架升级得分配点
for eid in [1, 1, 2, 1, 2, 3]:
    requests.post(f'{BASE}/api/battle/start',
        json={'enemy_id':eid,'character_id':c1,'skill_id':None}, headers=h, timeout=30)
prnt('战斗热身完成')

# 需求3-成就：先查 unlock_check 第1次
r1 = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=20).json()
prnt(f'[需求3] unlock#1 解锁数={r1["unlocked_count"]} 待领奖={r1["pending_claim_count"]} 新解锁={[a["name"] for a in r1["newly_unlocked"][:3]]}')

# 再查 unlock_check 第2次
r2 = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=20).json()
prnt(f'[需求3] unlock#2 解锁数={r2["unlocked_count"]}（应该=0）')

# 领奖再查
if r1['newly_unlocked']:
    achid = r1['newly_unlocked'][0]['id']
    requests.post(f'{BASE}/api/achievement/claim', json={'achievement_id':achid}, headers=h, timeout=20)
r3 = requests.get(f'{BASE}/api/achievement/unlock_check', headers=h, timeout=20).json()
prnt(f'[需求3] 领奖后unlock 新解锁数={r3["unlocked_count"]}（=0） 已领奖={r3["claimed_count"]}（>=1）')

prnt(' ')
prnt('[需求4] 属性分配点')
d = requests.get(f'{BASE}/api/account/character/{c1}', headers=h, timeout=20).json()
sp = d['stat_points']
prnt(f'  等级={d["level"]} 可用点={sp} 分配前ATK={d["final_stats"]["attack"]}')
if sp > 0:
    ok = requests.post(f'{BASE}/api/account/character/{c1}/allocate_stats',
        json={'max_hp': min(2,sp), 'attack': min(2,max(0,sp-2)),
              'defense': min(1,max(0,sp-4))}, headers=h, timeout=20)
    if ok.status_code==200:
        d2 = ok.json()
        prnt(f'  分配后 剩余点={d2["stat_points_remaining"]} 最终ATK={d2["final_stats"]["attack"]} 最终HP={d2["final_stats"]["max_hp"]}')
    else:
        prnt(f'  分配失败 {ok.status_code}: {ok.text[:200]}')
else:
    prnt('  点数不足跳过')

# 确认战斗预估也带分配点
d3 = requests.get(f'{BASE}/api/battle/simulate?enemy_id=2&character_id={c1}', headers=h, timeout=20).json()
prnt(f'  战斗预估ATK={d3["player"]["attack"]} HP={d3["player"]["max_hp"]}（应与角色详情一致）')

prnt(' ')
prnt('[需求1] 冒险日志')
d = requests.get(f'{BASE}/api/battle/records/{c1}?limit=100', headers=h, timeout=20).json()
prnt(f'  勇士A总战斗数={d["aggregate_stats"]["total_battles"]} '
      f'胜率={d["aggregate_stats"]["win_rate"]} '
      f'累计EXP={d["aggregate_stats"]["total_exp"]} 累计金币={d["aggregate_stats"]["total_gold"]}')
if d['records']:
    r0 = d['records'][0]
    prnt(f'  最新一场: {r0["enemy"]["name"]}({r0["result"]["victory"]}) 回合={r0["result"]["rounds"]} '
          f'金币变化 {r0["stats_change"]["player_gold"]["before"]}→{r0["stats_change"]["player_gold"]["after"]} '
          f'(+{r0["stats_change"]["player_gold"]["delta"]}) '
          f'关键回合: {r0["round_summary"][0]["summary"][:50] if r0["round_summary"] else ""}')

# 只看胜利筛选
dwin = requests.get(f'{BASE}/api/battle/records/{c1}?victory=true&limit=100', headers=h, timeout=20).json()
prnt(f'  只看胜利: {dwin["aggregate_stats"]["filtered_count"]} 场 / 总 {dwin["pagination"]["total"]} 场')

# 只看 Lv>=3 的敌人
dlv = requests.get(f'{BASE}/api/battle/records/{c1}?min_level=3&limit=100', headers=h, timeout=20).json()
prnt(f'  Lv>=3敌人: {dlv["aggregate_stats"]["filtered_count"]} 场')

prnt(' ')
prnt('[需求2] 带装备/冷却/多角色存档保存恢复')
# 装备
requests.post(f'{BASE}/api/inventory/add_item', json={'item_id':11,'quantity':1}, headers=h, timeout=15)
requests.post(f'{BASE}/api/inventory/equip?character_id={c1}',
    json={'item_id':11,'slot':'weapon'}, headers=h, timeout=15)
prnt('  装备铁剑→勇士A OK')

# 冷却
skills = requests.get(f'{BASE}/api/battle/skills/{c1}', headers=h, timeout=15).json()
skid = skills[0]['id']
requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id':1,'character_id':c1,'skill_id':skid}, headers=h, timeout=30)
cd1 = requests.get(f'{BASE}/api/battle/cooldowns/{c1}', headers=h, timeout=15).json()['cooldowns']
prnt(f'  勇士A技能战后冷却: {cd1}')

# 分配点确认
info1 = requests.get(f'{BASE}/api/account/character/{c1}', headers=h, timeout=15).json()
snap = {
    'chars': sorted([c['name'] for c in requests.get(f'{BASE}/api/account/characters', headers=h, timeout=15).json()]),
    'c1ATK': info1['final_stats']['attack'],
    'c1AllocATK': info1['allocated_stats']['attack'],
    'c1SP': info1['stat_points'],
    'c1EqCnt': len(requests.get(f'{BASE}/api/inventory/equipment?character_id={c1}', headers=h, timeout=15).json()['equipment']),
    'c1CDCnt': len(cd1),
    'c1RecCnt': requests.get(f'{BASE}/api/battle/records/{c1}?limit=9999', headers=h, timeout=15).json()['aggregate_stats']['total_battles'],
    'achCnt': len(requests.get(f'{BASE}/api/achievement/player?unlocked=true', headers=h, timeout=15).json()),
}
prnt(f'  存档前快照: chars={snap["chars"]} ATK={snap["c1ATK"]} allocATK={snap["c1AllocATK"]} '
      f'sp={snap["c1SP"]} eq={snap["c1EqCnt"]} cd={snap["c1CDCnt"]} rec={snap["c1RecCnt"]} ach={snap["achCnt"]}')

sv = requests.post(f'{BASE}/api/savegame/save', json={'slot':7,'name':'综合测存档'}, headers=h, timeout=60).json()
sv_id = sv['save_id']
prnt(f'  存档完成 id={sv_id}')

# 破坏状态
requests.post(f'{BASE}/api/inventory/unequip?character_id={c1}', json={'slot':'weapon'}, headers=h, timeout=15)
requests.post(f'{BASE}/api/battle/reset_cooldowns', json={'character_id':c1}, headers=h, timeout=15)
requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id':1,'character_id':c1,'skill_id':None}, headers=h, timeout=30)
requests.post(f'{BASE}/api/battle/start',
    json={'enemy_id':1,'character_id':c2,'skill_id':None}, headers=h, timeout=30)
requests.post(f'{BASE}/api/account/character',
    json={'name':'临时X','class_name':'弓箭手'}, headers=h, timeout=15)
prnt('  故意破坏：脱装备、清冷却、多打2场、加临时角色')

requests.post(f'{BASE}/api/savegame/load/{sv_id}', headers=h, timeout=90)
prnt('  加载存档完成')

chars_after = requests.get(f'{BASE}/api/account/characters', headers=h, timeout=15).json()
c1_new = next(c['id'] for c in chars_after if c['name']=='战1')
c2_new = next(c['id'] for c in chars_after if c['name']=='法2')
info2 = requests.get(f'{BASE}/api/account/character/{c1_new}', headers=h, timeout=15).json()
after = {
    'chars': sorted([c['name'] for c in chars_after]),
    'c1ATK': info2['final_stats']['attack'],
    'c1AllocATK': info2['allocated_stats']['attack'],
    'c1SP': info2['stat_points'],
    'c1EqCnt': len(requests.get(f'{BASE}/api/inventory/equipment?character_id={c1_new}', headers=h, timeout=15).json()['equipment']),
    'c1CDCnt': len(requests.get(f'{BASE}/api/battle/cooldowns/{c1_new}', headers=h, timeout=15).json()['cooldowns']),
    'c1RecCnt': requests.get(f'{BASE}/api/battle/records/{c1_new}?limit=9999', headers=h, timeout=15).json()['aggregate_stats']['total_battles'],
    'achCnt': len(requests.get(f'{BASE}/api/achievement/player?unlocked=true', headers=h, timeout=15).json()),
}

prnt('  加载后对比：')
for k in ['chars','c1ATK','c1AllocATK','c1SP','c1EqCnt','c1CDCnt','c1RecCnt','achCnt']:
    same = snap[k] == after[k]
    sym = '✅' if same else '❌'
    prnt(f'    {sym} {k}: 保存={snap[k]} 恢复={after[k]} 一致={same}')

prnt(' ')
prnt('='*60)
prnt('全部完成')
prnt('='*60)
