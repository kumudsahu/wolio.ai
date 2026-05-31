"""Rewards economy API (Step 5) — shop, purchases, and achievements."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn, jload, jdump
from .. import economy

router = APIRouter(prefix="/api", tags=["rewards"])


@router.get("/shop/{user_id}")
def get_shop(user_id: int):
    conn = get_conn()
    try:
        u = conn.execute("SELECT xp, coins, unlocked, avatar FROM users WHERE id=?", (user_id,)).fetchone()
        if not u:
            raise HTTPException(404, "User not found")
    finally:
        conn.close()
    unlocked = jload(u["unlocked"], [])
    avatar = jload(u["avatar"], {})
    return {
        "coins": u["coins"] or 0,
        "equipped": avatar.get("emoji"),
        "items": economy.shop_for(u["coins"] or 0, u["xp"] or 0, unlocked),
    }


class BuyIn(BaseModel):
    user_id: int
    item_id: str


@router.post("/shop/buy")
def buy(data: BuyIn):
    item = economy.shop_item(data.item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    conn = get_conn()
    try:
        u = conn.execute("SELECT xp, coins, unlocked, avatar FROM users WHERE id=?", (data.user_id,)).fetchone()
        if not u:
            raise HTTPException(404, "User not found")
        unlocked = jload(u["unlocked"], [])
        if data.item_id in unlocked:
            raise HTTPException(400, "Already owned")
        # tier gate
        req_i = next(i for i, t in enumerate(economy.LEVEL_TIERS) if t["key"] == item["tier"])
        if economy.tier_index(u["xp"] or 0) < req_i:
            raise HTTPException(403, f"Reach {economy.LEVEL_TIERS[req_i]['name']} first")
        if (u["coins"] or 0) < item["cost"]:
            raise HTTPException(402, "Not enough coins")

        unlocked.append(data.item_id)
        # spend coins via the ledger and equip the new look
        economy.award(conn, data.user_id, coins=-item["cost"], reason=f"buy:{data.item_id}")
        avatar = jload(u["avatar"], {})
        avatar["emoji"] = item["emoji"]
        conn.execute("UPDATE users SET unlocked=?, avatar=? WHERE id=?",
                     (jdump(unlocked), jdump(avatar), data.user_id))
        conn.commit()
        new_coins = conn.execute("SELECT coins FROM users WHERE id=?", (data.user_id,)).fetchone()["coins"]
    finally:
        conn.close()
    return {"ok": True, "equipped": item["emoji"], "coins": new_coins, "owned": data.item_id}


@router.get("/achievements/{user_id}")
def achievements(user_id: int):
    conn = get_conn()
    try:
        u = conn.execute("SELECT xp FROM users WHERE id=?", (user_id,)).fetchone()
        if not u:
            raise HTTPException(404, "User not found")
        earned = {r["badge_id"]: r["unlocked_at"]
                  for r in conn.execute(
                      "SELECT badge_id, unlocked_at FROM achievements WHERE user_id=?", (user_id,)).fetchall()}
    finally:
        conn.close()
    items = [{
        "id": a["id"], "icon": a["icon"], "name": a["name"], "desc": a["desc"],
        "earned": a["id"] in earned, "unlocked_at": earned.get(a["id"]),
    } for a in economy.ACHIEVEMENTS]
    return {
        "total": len(items),
        "earned": sum(1 for i in items if i["earned"]),
        "items": items,
    }
