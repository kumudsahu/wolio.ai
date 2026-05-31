"""Reward economy (Step 5) — the single, configurable source of truth for
XP, coins, level tiers, streaks, achievements, and the avatar shop.

Everything is data-driven here so values can be balanced/A-B-tested in one
place (spec 5.12). `award()` is the one function that mutates a user's economy
state: it adds XP + coins, advances the daily streak, and reports level-ups.
"""
import json

# --- 5.1 XP values --------------------------------------------------------
XP = {
    "mission": 50,
    "quiz_correct": 10,
    "streak_bonus": 20,
    "revision": 15,
    "first_concept": 25,
}

# --- 5.5 Coin values ------------------------------------------------------
COINS = {
    "mission": 10,
    "quest": 5,
    "achievement": 20,
    "quick_learn": 2,
    "revision": 3,
    "challenge": 15,
}

# --- 5.2 Level tiers (identity progression) -------------------------------
LEVEL_TIERS = [
    {"key": "beginner",  "name": "Beginner",  "emoji": "🌱", "xp": 0,    "perk": "Your journey begins!"},
    {"key": "explorer",  "name": "Explorer",  "emoji": "🚀", "xp": 150,  "perk": "Unlocks the avatar shop"},
    {"key": "thinker",   "name": "Thinker",   "emoji": "🧠", "xp": 400,  "perk": "Unlocks Wizard avatar"},
    {"key": "innovator", "name": "Innovator", "emoji": "⚡", "xp": 800,  "perk": "Unlocks Champion avatar"},
    {"key": "master",    "name": "Master",    "emoji": "👑", "xp": 1500, "perk": "Legendary status!"},
]


def tier_index(xp: int) -> int:
    idx = 0
    for i, t in enumerate(LEVEL_TIERS):
        if xp >= t["xp"]:
            idx = i
    return idx


def tier_for(xp: int) -> dict:
    return LEVEL_TIERS[tier_index(xp)]


def next_tier(xp: int):
    i = tier_index(xp)
    if i + 1 < len(LEVEL_TIERS):
        nt = LEVEL_TIERS[i + 1]
        return {**nt, "xp_needed": max(0, nt["xp"] - xp)}
    return None


def level_block(xp: int) -> dict:
    """Everything the UI needs to draw the level/tier widget + AI nudge."""
    cur = tier_for(xp)
    nxt = next_tier(xp)
    if nxt:
        span = nxt["xp"] - cur["xp"]
        into = xp - cur["xp"]
        progress = round(into / span * 100) if span else 100
        nudge = f"You're just {nxt['xp_needed']} XP from {nxt['name']} {nxt['emoji']}!"
    else:
        progress = 100
        nudge = "You've reached the top tier — legend! 👑"
    return {
        "tier": {"key": cur["key"], "name": cur["name"], "emoji": cur["emoji"]},
        "tier_index": tier_index(xp),
        "next_tier": nxt,
        "progress": progress,
        "nudge": nudge,
    }


# --- 5.6 Avatar shop ------------------------------------------------------
# Free starter avatars (also offered in onboarding) — never need buying.
FREE_AVATARS = ["🦊", "🐯", "🐼", "🚀", "🦄", "🤖", "🐸", "🦁", "🐙", "🦖", "👾", "🐲"]

SHOP = [
    {"id": "av_alien",     "emoji": "👽",  "name": "Alien",     "cost": 40,  "tier": "explorer"},
    {"id": "av_ninja",     "emoji": "🥷",  "name": "Ninja",     "cost": 60,  "tier": "explorer"},
    {"id": "av_astro",     "emoji": "🧑‍🚀", "name": "Astronaut", "cost": 70,  "tier": "explorer"},
    {"id": "av_genie",     "emoji": "🧞",  "name": "Genie",     "cost": 90,  "tier": "explorer"},
    {"id": "av_wizard",    "emoji": "🧙",  "name": "Wizard",    "cost": 120, "tier": "thinker"},
    {"id": "av_dragon",    "emoji": "🐉",  "name": "Dragon",    "cost": 160, "tier": "thinker"},
    {"id": "av_superhero", "emoji": "🦸",  "name": "Superhero", "cost": 200, "tier": "innovator"},
    {"id": "av_crown",     "emoji": "👑",  "name": "Champion",  "cost": 300, "tier": "master"},
]


def shop_for(coins: int, xp: int, unlocked: list) -> list:
    ti = tier_index(xp)
    out = []
    for item in SHOP:
        req_i = next(i for i, t in enumerate(LEVEL_TIERS) if t["key"] == item["tier"])
        owned = item["id"] in (unlocked or [])
        tier_ok = ti >= req_i
        out.append({
            **item,
            "owned": owned,
            "tier_locked": not tier_ok,
            "tier_name": LEVEL_TIERS[req_i]["name"],
            "affordable": coins >= item["cost"],
        })
    return out


def shop_item(item_id: str):
    return next((i for i in SHOP if i["id"] == item_id), None)


# --- 5.7 Achievements -----------------------------------------------------
# check(stats) -> bool, where stats has: concepts, mastered, longest_streak,
# missions, coins_earned, tier_index, revisions.
ACHIEVEMENTS = [
    {"id": "first_mission", "icon": "🎯", "name": "First Mission",  "desc": "Complete your first mission",  "check": lambda s: s["missions"] >= 1},
    {"id": "curious",       "icon": "🔭", "name": "Curious Mind",   "desc": "Learn 5 concepts",             "check": lambda s: s["concepts"] >= 5},
    {"id": "scholar",       "icon": "📚", "name": "Scholar",        "desc": "Learn 25 concepts",            "check": lambda s: s["concepts"] >= 25},
    {"id": "centurion",     "icon": "💯", "name": "Centurion",      "desc": "Learn 100 concepts",           "check": lambda s: s["concepts"] >= 100},
    {"id": "mastermind",    "icon": "🧠", "name": "Mastermind",     "desc": "Master 5 concepts",            "check": lambda s: s["mastered"] >= 5},
    {"id": "streak_7",      "icon": "🔥", "name": "On Fire",        "desc": "Reach a 7-day streak",         "check": lambda s: s["longest_streak"] >= 7},
    {"id": "streak_30",     "icon": "☄️", "name": "Unstoppable",    "desc": "Reach a 30-day streak",        "check": lambda s: s["longest_streak"] >= 30},
    {"id": "reviser",       "icon": "🔁", "name": "Revisionist",    "desc": "Revise 10 times",              "check": lambda s: s["revisions"] >= 10},
    {"id": "rich",          "icon": "🪙", "name": "Coin Collector", "desc": "Earn 200 coins",               "check": lambda s: s["coins_earned"] >= 200},
    {"id": "explorer_tier", "icon": "🚀", "name": "Explorer",       "desc": "Reach the Explorer tier",      "check": lambda s: s["tier_index"] >= 1},
    {"id": "master_tier",   "icon": "👑", "name": "Grand Master",   "desc": "Reach the Master tier",        "check": lambda s: s["tier_index"] >= 4},
]


# --- the one mutator ------------------------------------------------------
def award(conn, user_id: int, *, xp: int = 0, coins: int = 0, reason: str = "") -> dict:
    """Add XP + coins, advance the daily streak (with bonus), report level-up.

    Returns the deltas and new totals so the UI can animate + celebrate.
    """
    row = conn.execute(
        "SELECT xp, coins, streak, longest_streak, last_active FROM users WHERE id=?",
        (user_id,),
    ).fetchone()
    old_xp = row["xp"] or 0
    old_coins = row["coins"] or 0
    streak = row["streak"] or 0
    longest = row["longest_streak"] or 0
    last_active = row["last_active"]

    today = conn.execute("SELECT date('now') d").fetchone()["d"]
    yday = conn.execute("SELECT date('now','-1 day') d").fetchone()["d"]

    streak_bonus = 0
    if last_active != today:
        # first activity today → advance or (re)start the streak
        streak = streak + 1 if last_active == yday else 1
        streak_bonus = XP["streak_bonus"]
        longest = max(longest, streak)

    total_xp_add = xp + streak_bonus
    new_xp = old_xp + total_xp_add
    new_coins = old_coins + coins

    conn.execute(
        "UPDATE users SET xp=?, coins=?, streak=?, longest_streak=?, last_active=? WHERE id=?",
        (new_xp, new_coins, streak, longest, today, user_id),
    )
    if total_xp_add:
        conn.execute("INSERT INTO ledger (user_id, kind, amount, reason) VALUES (?,?,?,?)",
                     (user_id, "xp", total_xp_add, reason or "xp"))
    if coins:
        conn.execute("INSERT INTO ledger (user_id, kind, amount, reason) VALUES (?,?,?,?)",
                     (user_id, "coin", coins, reason or "coin"))

    leveled = None
    if tier_index(new_xp) > tier_index(old_xp):
        leveled = tier_for(new_xp)

    return {
        "xp_added": total_xp_add, "streak_bonus": streak_bonus, "coins_added": coins,
        "total_xp": new_xp, "total_coins": new_coins,
        "streak": streak, "longest_streak": longest,
        "level_up": ({"name": leveled["name"], "emoji": leveled["emoji"], "perk": leveled["perk"]}
                     if leveled else None),
        "tier": tier_for(new_xp),
    }


def coins_earned_total(conn, user_id: int) -> int:
    r = conn.execute(
        "SELECT COALESCE(SUM(amount),0) s FROM ledger WHERE user_id=? AND kind='coin' AND amount>0",
        (user_id,),
    ).fetchone()
    return r["s"] or 0


def sync_achievements(conn, user_id: int, stats: dict) -> dict:
    """Insert any newly-earned achievements; return earned set + freshly-unlocked."""
    already = {r["badge_id"]: r["unlocked_at"]
               for r in conn.execute(
                   "SELECT badge_id, unlocked_at FROM achievements WHERE user_id=?", (user_id,)).fetchall()}
    newly = []
    for a in ACHIEVEMENTS:
        if a["check"](stats) and a["id"] not in already:
            conn.execute("INSERT OR IGNORE INTO achievements (user_id, badge_id) VALUES (?,?)",
                         (user_id, a["id"]))
            newly.append(a["id"])
            already[a["id"]] = "now"
    return {"earned": already, "newly": newly}
