"""wolio.ai 'AI Brain' — personalization + mentor.

Works fully offline with a rule-based engine so the app is demoable with zero
keys. If OPENAI_API_KEY is set, mentor replies upgrade to a live LLM call.
"""
import os
import random
from typing import Optional

# ---------------------------------------------------------------------------
# Learning Worlds catalogue — subjects reframed as game universes.
# ---------------------------------------------------------------------------
WORLDS = [
    {
        "id": "space",
        "name": "Space World",
        "subject": "Science",
        "emoji": "🚀",
        "tagline": "Become an astronaut. Learn the universe.",
        "color": "#6C5CE7",
        "interests": ["space", "games"],
        "missions": [
            {"id": "gravity", "title": "Why do things fall?", "concept": "Gravity", "emoji": "🪐", "chapter": "Forces"},
            {"id": "mars-rover", "title": "Fix the Mars Rover", "concept": "Forces & Motion", "emoji": "🛞", "chapter": "Forces"},
            {"id": "saturn", "title": "Can Saturn really float?", "concept": "Density", "emoji": "🪐", "chapter": "Matter"},
        ],
    },
    {
        "id": "math",
        "name": "Math Mystery",
        "subject": "Math",
        "emoji": "🧮",
        "tagline": "Solve mysteries using logic.",
        "color": "#00B894",
        "interests": ["games", "cars", "sports"],
        "missions": [
            {"id": "fractions", "title": "The Pizza Heist", "concept": "Fractions", "emoji": "🍕", "chapter": "Numbers"},
            {"id": "patterns", "title": "Crack the Secret Code", "concept": "Patterns", "emoji": "🔢", "chapter": "Logic"},
            {"id": "speed", "title": "Race Day Math", "concept": "Speed & Distance", "emoji": "🏎️", "chapter": "Numbers"},
        ],
    },
    {
        "id": "story",
        "name": "Story Universe",
        "subject": "Literature",
        "emoji": "📖",
        "tagline": "Enter the story. Choose the ending.",
        "color": "#E17055",
        "interests": ["stories", "art", "animals"],
        "missions": [
            {"id": "nani-1", "title": "Nani Scientist – Episode 1", "concept": "Vocabulary", "emoji": "👵", "chapter": "Words"},
            {"id": "brave", "title": "The Brave Little Fox", "concept": "Emotions", "emoji": "🦊", "chapter": "Feelings"},
        ],
    },
    {
        "id": "time",
        "name": "Time Travel",
        "subject": "History",
        "emoji": "⏳",
        "tagline": "Travel through time. Live history.",
        "color": "#0984E3",
        "interests": ["stories", "games"],
        "missions": [
            {"id": "dino", "title": "Walk with Dinosaurs", "concept": "Prehistoric Era", "emoji": "🦕", "chapter": "Prehistory"},
            {"id": "pyramid", "title": "Build a Pyramid", "concept": "Ancient Egypt", "emoji": "🔺", "chapter": "Ancient Worlds"},
        ],
    },
]


def difficulty_tier(age_group: str) -> int:
    return {"3-5": 1, "6-8": 1, "9-12": 2, "13-16": 3, "16-18": 3}.get(age_group, 2)


def rank_worlds(interests: Optional[list]) -> list:
    """Score worlds by overlap with the kid's chosen interests."""
    interests = [i.lower() for i in (interests or [])]
    ranked = []
    for w in WORLDS:
        score = len(set(interests) & set(w["interests"]))
        ranked.append({**w, "match": score})
    ranked.sort(key=lambda w: w["match"], reverse=True)
    return ranked


def build_journey(name: str, interests: Optional[list], learning_style: Optional[str]) -> dict:
    """The 'magic moment' — generate a custom starting path."""
    ranked = rank_worlds(interests)
    top = ranked[0]
    first = top["missions"][0]
    style = (learning_style or "games")
    verb = {"games": "play", "stories": "explore", "quizzes": "challenge"}.get(style, "play")
    return {
        "headline": f"{name}, your learning universe is ready 🚀",
        "primary_world": top,
        "first_mission": {**first, "world": top["id"], "world_name": top["name"]},
        "pitch": f"We'll {verb} your way through {top['subject']} — starting with “{first['title']}”.",
        "world_order": [w["id"] for w in ranked],
    }


# ---------------------------------------------------------------------------
# Homepage engine — greeting, recommendation, quests, micro-learning.
# ---------------------------------------------------------------------------
def time_of_day(hour: int) -> str:
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def greeting(name: str, hour: int) -> dict:
    slot = time_of_day(hour)
    text = {"morning": "Good morning", "afternoon": "Hey", "evening": "Good evening"}[slot]
    emoji = {"morning": "🌅", "afternoon": "👋", "evening": "🌙"}[slot]
    return {"text": f"{text}, {name}", "emoji": emoji, "slot": slot}


# Micro-learning bites — each tagged so we can surface what the kid loves first.
QUICK_LEARN = [
    {"id": "ql-saturn", "q": "Saturn could float on water! 🪐", "go": "Why?", "subject": "Science", "tags": ["space"]},
    {"id": "ql-heart",  "q": "Your heart pumps ~1L of blood a minute ❤️", "go": "Whoa, learn", "subject": "Biology", "tags": ["animals"]},
    {"id": "ql-zero",   "q": "Zero was invented in India 🔢", "go": "Story time", "subject": "Math", "tags": ["games", "stories"]},
    {"id": "ql-octo",   "q": "Octopuses have 3 hearts 🐙", "go": "Tap to learn", "subject": "Science", "tags": ["animals"]},
    {"id": "ql-speed",  "q": "A cheetah out-accelerates a sports car 🏎️", "go": "How?", "subject": "Physics", "tags": ["cars", "sports", "animals"]},
    {"id": "ql-sky",    "q": "Why is the sky blue? 🌤️", "go": "60-sec answer", "subject": "Science", "tags": ["space", "art"]},
    {"id": "ql-music",  "q": "Every song is built from just 12 notes 🎵", "go": "Tap to learn", "subject": "Music", "tags": ["music", "art"]},
    {"id": "ql-goal",   "q": "A free kick can curve from spin ⚽", "go": "The science", "subject": "Physics", "tags": ["sports", "games"]},
]


def quick_learn_for(interests, n: int = 6) -> list:
    """Surface micro-bites that match the kid's interests first, then fill."""
    interests = set(i.lower() for i in (interests or []))
    liked = [c for c in QUICK_LEARN if interests & set(c["tags"])]
    rest = [c for c in QUICK_LEARN if c not in liked]
    ordered = liked + rest
    return [{k: v for k, v in c.items() if k != "tags"} for c in ordered[:n]]


# Daily quests — reset every 24h, lightly scaled by difficulty tier.
def daily_quest_set(tier: int = 1) -> list:
    learn_target = 1 if tier == 1 else 2
    revise_target = 2 if tier == 1 else 3
    return [
        {"task_id": "learn",  "icon": "🚀", "label": f"Complete {learn_target} mission" + ("s" if learn_target > 1 else ""),
         "target": learn_target, "reward": 40},
        {"task_id": "quick",  "icon": "⚡", "label": "Try 1 Quick Learn", "target": 1, "reward": 20},
        {"task_id": "revise", "icon": "🧠", "label": f"Revise {revise_target} concepts", "target": revise_target, "reward": 30},
    ]


def recommend_action(name: str, ranked_worlds: list, last_world: str, last_mission: str,
                     completed_titles: set, needs_revision: list, hour: int,
                     concepts_count: int) -> dict:
    """The Hero section brain: decide the single best next action.

    Signals: last_activity, weak_topics, interest_priority, time_of_day.
    """
    slot = time_of_day(hour)

    # 1) Evening + something fading from memory → nudge a revision.
    if needs_revision and (slot == "evening" or concepts_count >= 4):
        c = needs_revision[0]
        return {
            "kind": "revise",
            "icon": "🧠",
            "title": f"Quick revision: {c['title']}",
            "subtitle": f"You learned this a while ago — let's lock it back in (2 min).",
            "cta": "Revise now",
            "reason": "evening_memory_fade",
            "world_id": None, "mission_id": None,
            "color": "#34e0a1",
        }

    # 2) An in-progress world with an unfinished next mission → continue.
    target_world = next((w for w in ranked_worlds if w["id"] == last_world), None) or (ranked_worlds[0] if ranked_worlds else None)
    if target_world:
        nxt = next((m for m in target_world["missions"] if m["concept"] not in completed_titles), None)
        if nxt:
            warm = "Warm up your brain 🌅 " if slot == "morning" else ""
            return {
                "kind": "continue_mission",
                "icon": target_world["emoji"],
                "title": f"{nxt['emoji']} {nxt['title']}",
                "subtitle": f"{warm}Continue your {target_world['name']} journey.",
                "cta": "Continue",
                "reason": "interest_priority" if last_world is None else "last_activity",
                "world_id": target_world["id"], "mission_id": nxt["id"],
                "color": target_world["color"],
            }

    # 3) Everything in the top world is done → open a fresh world.
    fresh = next((w for w in ranked_worlds if any(m["concept"] not in completed_titles for m in w["missions"])), None)
    if fresh:
        m = fresh["missions"][0]
        return {
            "kind": "new_world",
            "icon": fresh["emoji"],
            "title": f"Explore {fresh['name']}",
            "subtitle": f"A whole new world is ready for you, {name}!",
            "cta": "Start",
            "reason": "breadth",
            "world_id": fresh["id"], "mission_id": m["id"],
            "color": fresh["color"],
        }

    # 4) Mastered everything we have → celebrate + quick-learn.
    return {
        "kind": "quick_learn",
        "icon": "🏆",
        "title": "You're a Wolio legend!",
        "subtitle": "You've cleared every mission. Try a Quick Learn while we craft more.",
        "cta": "Quick Learn",
        "reason": "all_done",
        "world_id": None, "mission_id": None,
        "color": "#ffce4f",
    }


def notifications(streak: int, needs_revision: list, concepts_count: int, slot: str) -> list:
    """Smart, non-spammy alerts for the bell.

    Each has a priority; we sort high→low and cap at 3 (spec: max 3 active,
    no spam). Higher priority = more time-sensitive for the child.
    """
    out = []
    if streak >= 1 and slot == "evening":
        out.append({"id": "n-streak", "type": "streak", "icon": "🔥", "priority": 3,
                    "text": f"Your {streak}-day streak is at risk! Learn something to keep it alive."})
    if needs_revision:
        c = needs_revision[0]
        out.append({"id": "n-revise", "type": "revision", "icon": "🧠", "priority": 2,
                    "text": f"You haven't revised {c['title']} — a quick refresh will help!"})
    if concepts_count == 0:
        out.append({"id": "n-first", "type": "mission", "icon": "🚀", "priority": 2,
                    "text": "Your first mission is ready — tap Continue to begin!"})
    elif concepts_count >= 3:
        out.append({"id": "n-unlock", "type": "content_unlock", "icon": "✨", "priority": 1,
                    "text": "New episode unlocked across your worlds. Go explore! 🚀"})
    out.sort(key=lambda n: n["priority"], reverse=True)
    return out[:3]   # max 3 active


# ---------------------------------------------------------------------------
# Personalized example injection — the cricket/space trick from the spec.
# ---------------------------------------------------------------------------
def flavor(interests: Optional[list]) -> str:
    interests = [i.lower() for i in (interests or [])]
    if "space" in interests:
        return "rockets and planets"
    if "sports" in interests:
        return "cricket scores and goals"
    if "cars" in interests:
        return "race cars and speed"
    if "animals" in interests:
        return "animals and the wild"
    return "your favourite adventures"


# ---------------------------------------------------------------------------
# AI Mentor — friendly, Hinglish-capable. LLM if a key exists, else rule-based.
# ---------------------------------------------------------------------------
def _tone_prefix(tone: str) -> str:
    return {
        "fun": random.choice(["Ooooh great question! ", "Haha love it! ", "Let's gooo 🚀 "]),
        "calm": random.choice(["Sure, let's take it slow. ", "Good question. "]),
        "energetic": random.choice(["YES! ", "Boom! 💥 ", "Awesome, let's crush this! "]),
    }.get(tone, "")


def _offline_reply(message: str, ctx: dict) -> str:
    name = ctx.get("name", "buddy")
    tone = ctx.get("tone", "fun")
    fl = flavor(ctx.get("interests"))
    lang = ctx.get("language", "hinglish")
    pre = _tone_prefix(tone)
    body = (
        f"So {name}, imagine this using {fl} — that makes it super easy to picture. "
        f"Want me to turn it into a quick 60-second mission or a fun story?"
    )
    if lang == "hinglish":
        body = (
            f"Toh {name}, isko {fl} se socho — bilkul aasaan ho jaata hai! "
            f"Main ise ek 60-second mission bana du ya ek mazedaar story?"
        )
    return pre + body


def mentor_reply(message: str, ctx: dict, mode: str = "fun", history=None, sensitive: bool = False) -> dict:
    """Return {'reply': str, 'source': 'llm'|'offline'}. mode: fun|quick|quiz."""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            return {"reply": _llm_reply(message, ctx, key, mode, history or [], sensitive), "source": "llm"}
        except Exception:
            pass  # graceful fallback — never break the kid's flow
    return {"reply": _offline_reply_mode(message, ctx, mode, sensitive), "source": "offline"}


def _age_flair(age_group: str, topic: str, fl: str) -> str:
    """Age-based phrasing (spec 6): playful for the young, precise for teens."""
    if age_group in ("3-5", "6-8"):
        return f"think of {topic} like a giant invisible hug from {fl} 🤗"
    if age_group in ("13-16", "16-18"):
        return f"{topic} works in a precise, science-y way — picture it through {fl}"
    return f"imagine {topic} using {fl} — that makes it click"


def _offline_reply_mode(message: str, ctx: dict, mode: str, sensitive: bool = False) -> str:
    name = ctx.get("name", "buddy")
    fl = flavor(ctx.get("interests"))
    age = ctx.get("age_group", "9-12")
    topic = message.replace("Explain", "").replace("explain", "").strip(" ?.") or "this"
    if sensitive:
        return (f"Good question, {name}. That's a real part of the world, and it's okay to wonder about it. "
                f"The simple, safe version: it's something grown-ups handle, and a trusted adult can tell you more. "
                f"Want to get back to a fun discovery? 🌟")
    if mode == "quick":
        return f"Quick version, {name}: {_age_flair(age, topic, fl)}. ⚡"
    if mode == "quiz":
        return (f"Quiz time, {name}! 🧠 Here's one about {topic}: "
                f"if you explained it using {fl}, what would the FIRST step be? "
                f"Type your guess and I'll tell you if you're right! 🎯")
    return f"Ooooh great question! So {name}, {_age_flair(age, topic, fl)}. Want a 60-sec mission or a fun story? 🚀"


def _llm_reply(message: str, ctx: dict, key: str, mode: str = "fun", history=None, sensitive: bool = False) -> str:
    from openai import OpenAI  # imported lazily; only if a key is present
    from . import safety

    client = OpenAI(api_key=key)
    system = safety.system_prompt(ctx, mode=mode, sensitive=sensitive)   # kid-safe personality
    # include the last few turns for session memory (spec: last 5)
    msgs = [{"role": "system", "content": system}]
    for h in (history or [])[-5:]:
        role = "assistant" if h.get("role") in ("bot", "assistant") else "user"
        msgs.append({"role": role, "content": str(h.get("text", ""))[:500]})
    msgs.append({"role": "user", "content": message})

    resp = client.chat.completions.create(
        model="gpt-4o-mini", messages=msgs, max_tokens=160, temperature=0.7)
    return resp.choices[0].message.content.strip()
