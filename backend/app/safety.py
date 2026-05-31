"""Child-Safe AI Architecture — the multi-layer safety system.

    Child input → INPUT FILTER → AI → OUTPUT FILTER → child response

Design goals (the product moat): a *guided / walled-garden* educational AI that
is safe, emotionally healthy, age-appropriate, and never dependency-forming.
Pure functions (no DB) so they're fully unit-testable; the mentor router does
the logging. This is defense-in-depth on top of the model's own guardrails AND
a real moderation API in production (see ARCHITECTURE.md).
"""
import re

# --- LAYER 1: categorized input filter -----------------------------------
# Hard-block categories → refuse + positive redirect.
_CATEGORIES = {
    "self_harm":   r"\b(kill myself|suicide|self[- ]?harm|hurt myself|cut myself|want to die|end my life|hate myself)\b",
    "violence":    r"\b(kill|murder|stab|shoot|hurt (someone|people)|make a (bomb|weapon)|gun|knife)\b",
    "sexual":      r"\b(sex|sexual|porn|nude|naked|boobs)\b",
    "drugs":       r"\b(drugs?|cocaine|weed|alcohol|cigarette|vap(e|ing)|get high)\b",
    "gambling":    r"\b(gambl(e|ing)|casino|place a bet|betting)\b",
    "hate":        r"\b(racist|hate (jews|muslims|black|white) people|terror(ism|ist))\b",
    "contact_pii": r"\b(your address|phone number|where do you live|meet me|credit card|my password|home address)\b",
}
_CATEGORY_RES = {k: re.compile(v, re.IGNORECASE) for k, v in _CATEGORIES.items()}

# Emotional distress → gentle support + point to a trusted adult (NOT a block).
_EMOTIONAL_RE = re.compile(
    r"\b(i'?m sad|i am sad|i feel (sad|lonely|alone|down|depressed)|nobody likes me|"
    r"no( one| body) loves me|i want to cry|i'?m depressed|i'?m scared|i feel bad|"
    r"i have no friends)\b", re.IGNORECASE)

# Sensitive-but-educational → allow, but answer age-appropriately, no graphic detail.
_SENSITIVE_RE = re.compile(
    r"\b(war|died?|death|dying|kidnap|divorce|earthquake|disease|virus)\b", re.IGNORECASE)

# --- LAYER 2: output filter ----------------------------------------------
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d[\d\- ]{7,}\d)\b")
# Dependency / manipulation / isolation phrases an AI must NEVER say to a child.
_MANIPULATION_RE = re.compile(
    r"(only friend|don'?t tell (your )?(parents|anyone|mom|dad)|keep (this|it) (a )?secret|"
    r"you don'?t need (anyone|your parents|friends)|i love you|trust only me|"
    r"just between us|our little secret)", re.IGNORECASE)

SAFE_REDIRECT = (
    "Hmm, let's keep our adventure about fun learning! 😊 "
    "Want to explore something cool about space, animals, or numbers instead?"
)
EMOTIONAL_REPLY = (
    "I'm really sorry you're feeling that way. 💙 Feelings like that are okay and they pass. "
    "It really helps to talk to a grown-up you trust — like a parent, teacher, or family member. "
    "Want to do something fun together meanwhile, like a quick space fact? 🌟"
)


def classify_input(text: str, restricted_topics=None) -> dict:
    """Screen a child's message → {action, category, redirect}.

    action ∈ block | emotional | sensitive | restricted | allow
    """
    if not text or not text.strip():
        return {"action": "block", "category": "empty", "redirect": "Ask me anything about your learning! 🚀"}
    if len(text) > 1000:
        return {"action": "block", "category": "too_long", "redirect": "Whoa, that's a lot! Try a shorter question 😊"}

    # parent-configured topic restrictions
    for topic in (restricted_topics or []):
        if topic and re.search(re.escape(topic), text, re.IGNORECASE):
            return {"action": "restricted", "category": f"parent:{topic}",
                    "redirect": "That topic is turned off by your parent. Let's explore something else! 🌟"}

    # emotional distress takes priority over keyword blocks (e.g. "i want to die" is self_harm, handled below first)
    for cat, rx in _CATEGORY_RES.items():
        if rx.search(text):
            return {"action": "block", "category": cat, "redirect": SAFE_REDIRECT}

    if _EMOTIONAL_RE.search(text):
        return {"action": "emotional", "category": "emotional_distress", "redirect": EMOTIONAL_REPLY}

    if _SENSITIVE_RE.search(text):
        return {"action": "sensitive", "category": "sensitive", "redirect": None}

    return {"action": "allow", "category": None, "redirect": None}


# Backwards-compatible thin wrapper (older callers / tests).
def check_input(text: str) -> dict:
    c = classify_input(text)
    return {"safe": c["action"] in ("allow", "sensitive"), "reason": c["category"], "redirect": c["redirect"]}


def sanitize_output(text: str) -> str:
    """LAYER 2: scrub model output — no links/PII, no unsafe or manipulative content."""
    if not text:
        return SAFE_REDIRECT
    text = _URL_RE.sub("", text)
    text = _EMAIL_RE.sub("", text)
    text = _PHONE_RE.sub("", text)
    if _MANIPULATION_RE.search(text):       # never allow dependency/isolation language
        return SAFE_REDIRECT
    for rx in _CATEGORY_RES.values():
        if rx.search(text):
            return SAFE_REDIRECT
    return text.strip() or SAFE_REDIRECT


# --- LAYER 3: kid-safe personality + age adaptation ----------------------
def age_style(age_group: str) -> str:
    return {
        "3-5":   "Use very simple, playful words and a cuddly real-world analogy. One short sentence.",
        "6-8":   "Use simple, playful words and a fun analogy a young kid pictures easily.",
        "9-12":  "Friendly and clear, with a relatable everyday example.",
        "13-16": "Clear and a bit more precise/scientific, still warm.",
        "16-18": "Precise and scientific, like a smart older friend.",
    }.get(age_group, "Friendly, simple, and warm.")


def system_prompt(ctx: dict, mode: str = "fun", sensitive: bool = False) -> str:
    """The controlled 'kid-safe personality' prompt (walled-garden, no dependency)."""
    interests = ", ".join(ctx.get("interests") or ["space"])
    recent = ctx.get("recent_learning")
    mode_line = {
        "fun": "Explain with a tiny playful story and one emoji.",
        "quick": "Answer in 2-3 short lines.",
        "quiz": "Don't explain — ask ONE fun quiz question and invite a guess.",
    }.get(mode, "Explain with a tiny playful story and one emoji.")
    return (
        "You are Wolio, a SAFE educational AI companion for a child. You live inside a learning "
        "app — a walled garden. Only help with school-style learning, curiosity and the child's "
        "learning universe.\n"
        "RULES (never break):\n"
        "- Always encourage curiosity and confidence.\n"
        "- Never discuss adult, violent, scary, sexual, drug, or dangerous topics.\n"
        "- Never form emotional dependency. NEVER say things like 'I'm your only friend', "
        "'don't tell your parents', 'I love you', or 'keep this secret'.\n"
        "- Never isolate the child from parents, teachers, or friends — encourage them instead.\n"
        "- If the child seems upset, gently suggest talking to a trusted grown-up.\n"
        "- No links, no web browsing, no personal-data requests.\n"
        + (f"- This is a sensitive topic — keep it gentle, factual, age-appropriate, no graphic detail.\n" if sensitive else "")
        + f"CHILD: name {ctx.get('name','friend')}, age group {ctx.get('age_group','9-12')}. "
        f"{age_style(ctx.get('age_group','9-12'))} "
        f"Language: {ctx.get('language','hinglish')} (Hinglish = casual Hindi+English mix). "
        f"Use their interests ({interests}) for examples. "
        + (f"They recently learned: {recent}. " if recent else "")
        + f"{mode_line} Keep it under 60 words, warm, positive, kid-safe."
    )
