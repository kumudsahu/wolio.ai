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
            {"id": "gravity", "title": "Why do things fall?", "concept": "Gravity", "emoji": "🪐"},
            {"id": "mars-rover", "title": "Fix the Mars Rover", "concept": "Forces & Motion", "emoji": "🛞"},
            {"id": "saturn", "title": "Can Saturn really float?", "concept": "Density", "emoji": "🪐"},
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
            {"id": "fractions", "title": "The Pizza Heist", "concept": "Fractions", "emoji": "🍕"},
            {"id": "patterns", "title": "Crack the Secret Code", "concept": "Patterns", "emoji": "🔢"},
            {"id": "speed", "title": "Race Day Math", "concept": "Speed & Distance", "emoji": "🏎️"},
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
            {"id": "nani-1", "title": "Nani Scientist – Episode 1", "concept": "Vocabulary", "emoji": "👵"},
            {"id": "brave", "title": "The Brave Little Fox", "concept": "Emotions", "emoji": "🦊"},
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
            {"id": "dino", "title": "Walk with Dinosaurs", "concept": "Prehistoric Era", "emoji": "🦕"},
            {"id": "pyramid", "title": "Build a Pyramid", "concept": "Ancient Egypt", "emoji": "🔺"},
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


def mentor_reply(message: str, ctx: dict) -> dict:
    """Return {'reply': str, 'source': 'llm'|'offline'}."""
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            return {"reply": _llm_reply(message, ctx, key), "source": "llm"}
        except Exception:
            pass  # graceful fallback — never break the kid's flow
    return {"reply": _offline_reply(message, ctx), "source": "offline"}


def _llm_reply(message: str, ctx: dict, key: str) -> str:
    from openai import OpenAI  # imported lazily; only if a key is present

    client = OpenAI(api_key=key)
    system = (
        f"You are Wolio, a fun AI mentor for a child named {ctx.get('name','friend')}, "
        f"age group {ctx.get('age_group','9-12')}. Talk like an excited friend, NOT a teacher. "
        f"Tone: {ctx.get('tone','fun')}. Language: {ctx.get('language','hinglish')} "
        f"(Hinglish = casual Hindi+English mix). Use the child's interests "
        f"({', '.join(ctx.get('interests') or ['space'])}) for every example. "
        f"Keep replies under 60 words, warm, with one emoji."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": message}],
        max_tokens=160,
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()
