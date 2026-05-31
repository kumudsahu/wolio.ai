"""Child-safety layer (Step 7.10) — keep every AI interaction kid-safe.

Pure functions (no DB) so they're trivially unit-testable. The mentor router
runs check_input() before generating a reply and sanitize_output() after,
logging anything blocked as a 'safety' event for the admin dashboard.

This is defense-in-depth on top of the model's own guardrails — it does NOT
replace a real moderation API in production (documented in ARCHITECTURE.md).
"""
import re

# Topics a kids' tutor should never engage — redirect gently instead.
_BLOCK_PATTERNS = [
    r"\b(kill|murder|suicide|self[- ]?harm|die|death)\b",
    r"\b(gun|knife|weapon|bomb|drugs?|alcohol|cigarette|vap(e|ing))\b",
    r"\b(sex|sexual|porn|nude|naked)\b",
    r"\b(hate|racist|terror)\b",
    r"\b(address|phone number|where do you live|meet me|credit card|password)\b",
]
_BLOCK_RE = re.compile("|".join(_BLOCK_PATTERNS), re.IGNORECASE)

# Strip anything that could lead a child off-platform or leak PII (7.10: no
# external links, no ads). Applied to model output.
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d[\d\- ]{7,}\d)\b")

SAFE_REDIRECT = (
    "Hmm, let's keep our adventure about fun learning! 😊 "
    "Want to explore a cool fact about space, animals, or numbers instead?"
)


def check_input(text: str) -> dict:
    """Screen a child's message. Returns {safe, reason, redirect}."""
    if not text or not text.strip():
        return {"safe": False, "reason": "empty", "redirect": "Ask me anything about your learning! 🚀"}
    if len(text) > 1000:
        return {"safe": False, "reason": "too_long", "redirect": "Whoa, that's a lot! Try a shorter question 😊"}
    m = _BLOCK_RE.search(text)
    if m:
        return {"safe": False, "reason": f"blocked_topic:{m.group(0).lower()}", "redirect": SAFE_REDIRECT}
    return {"safe": True, "reason": None, "redirect": None}


def sanitize_output(text: str) -> str:
    """Scrub model output: no links, no emails/phones, no unsafe content."""
    if not text:
        return SAFE_REDIRECT
    text = _URL_RE.sub("", text)
    text = _EMAIL_RE.sub("", text)
    text = _PHONE_RE.sub("", text)
    if _BLOCK_RE.search(text):
        return SAFE_REDIRECT
    return text.strip() or SAFE_REDIRECT
