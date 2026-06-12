from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Player, Inventory, Equipment, Item
from schemas import ItemAdd, ItemRemove, EquipmentEquip, EquipmentUnequip, InventoryResponse
from routers.account import get_current_player
from game_utils import add_item_to_inventory, remove_item_from_inventory, get_equipment_stats

router = APIRouter(prefix="/api/inventory", tags=["背包装备"])


@router.get("/items", response_model=list[InventoryResponse])
def get_inventory(
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    inventory_items = []
    for inv in player.inventory:
        item = db.query(Item).filter_by(id=inv.item_id).first()
        if item:
            inventory_items.append({
                "id": inv.id,
                "item_id": inv.item_id,
                "item_name": item.name,
                "item_type": item.type,
                "quantity": inv.quantity,
                "stats": item.stats
            })
    return inventory_items


@router.post("/add_item")
def add_item(
    data: ItemAdd,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    try:
        inv = add_item_to_inventory(db, player.id, data.item_id, data.quantity)
        db.commit()
        item = db.query(Item).filter_by(id=data.item_id).first()
        return {
            "success": True,
            "item_id": data.item_id,
            "item_name": item.name if item else "未知物品",
            "quantity_added": data.quantity,
            "current_quantity": inv.quantity
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/remove_item")
def remove_item(
    data: ItemRemove,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    success = remove_item_from_inventory(db, player.id, data.item_id, data.quantity)
    if not success:
        raise HTTPException(status_code=400, detail="物品数量不足")
    
    db.commit()
    item = db.query(Item).filter_by(id=data.item_id).first()
    return {
        "success": True,
        "item_id": data.item_id,
        "item_name": item.name if item else "未知物品",
        "quantity_removed": data.quantity
    }


@router.get("/equipment")
def get_equipment(
    character_id: int = 0,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if character_id == 0:
        if len(player.characters) == 0:
            return {"equipment": [], "stats": {}}
        character_id = player.characters[0].id
    
    equipment_list = []
    equipment = db.query(Equipment).filter_by(
        player_id=player.id, character_id=character_id
    ).all()
    
    for eq in equipment:
        item = db.query(Item).filter_by(id=eq.item_id).first()
        if item:
            equipment_list.append({
                "id": eq.id,
                "slot": eq.slot,
                "item_id": eq.item_id,
                "item_name": item.name,
                "stats": item.stats,
                "equipped_at": eq.equipped_at
            })
    
    stats = get_equipment_stats(db, player.id, character_id)
    
    return {
        "equipment": equipment_list,
        "total_stats": stats
    }


@router.post("/equip")
def equip_item(
    data: EquipmentEquip,
    character_id: int = 0,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if len(player.characters) == 0:
        raise HTTPException(status_code=400, detail="请先创建角色")
    
    if character_id == 0:
        character_id = player.characters[0].id
    else:
        from models import Character
        char = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
        if not char:
            raise HTTPException(status_code=404, detail="角色不存在或不属于当前玩家")
    
    inv = db.query(Inventory).filter_by(
        player_id=player.id, item_id=data.item_id
    ).first()
    if not inv or inv.quantity < 1:
        raise HTTPException(status_code=400, detail="背包中没有该物品")
    
    item = db.query(Item).filter_by(id=data.item_id).first()
    if not item or not item.is_equipment:
        raise HTTPException(status_code=400, detail="该物品不能装备")
    
    if item.slot != data.slot:
        raise HTTPException(status_code=400, detail=f"该物品只能装备在 {item.slot} 槽位")
    
    current_equip = db.query(Equipment).filter_by(
        player_id=player.id, character_id=character_id, slot=data.slot
    ).first()
    if current_equip:
        add_item_to_inventory(db, player.id, current_equip.item_id, 1)
        db.delete(current_equip)
    
    remove_item_from_inventory(db, player.id, data.item_id, 1)
    
    new_equip = Equipment(
        player_id=player.id,
        character_id=character_id,
        item_id=data.item_id,
        slot=data.slot
    )
    db.add(new_equip)
    db.commit()
    
    return {
        "success": True,
        "character_id": character_id,
        "slot": data.slot,
        "item_id": data.item_id,
        "item_name": item.name,
        "message": f"成功装备 {item.name}"
    }


@router.post("/unequip")
def unequip_item(
    data: EquipmentUnequip,
    character_id: int = 0,
    player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    if len(player.characters) == 0:
        raise HTTPException(status_code=400, detail="请先创建角色")
    
    if character_id == 0:
        character_id = player.characters[0].id
    else:
        from models import Character
        char = db.query(Character).filter_by(id=character_id, player_id=player.id).first()
        if not char:
            raise HTTPException(status_code=404, detail="角色不存在或不属于当前玩家")
    
    equip = db.query(Equipment).filter_by(
        player_id=player.id, character_id=character_id, slot=data.slot
    ).first()
    if not equip:
        raise HTTPException(status_code=400, detail=f"槽位 {data.slot} 没有装备")
    
    item = db.query(Item).filter_by(id=equip.item_id).first()
    add_item_to_inventory(db, player.id, equip.item_id, 1)
    db.delete(equip)
    db.commit()
    
    return {
        "success": True,
        "character_id": character_id,
        "slot": data.slot,
        "item_id": equip.item_id,
        "item_name": item.name if item else "未知物品",
        "message": f"成功卸下 {item.name if item else '装备'}"
    }


@router.get("/items/all")
def get_all_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return [{
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "type": item.type,
        "rarity": item.rarity,
        "price": item.price,
        "stats": item.stats,
        "is_equipment": item.is_equipment,
        "slot": item.slot
    } for item in items]
