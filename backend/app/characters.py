"""The Curio-Verse — wolio.ai's original character cast + comic episodes.

This is owned IP (see CHARACTERS.md). Data-driven so designers/writers can add
characters and comic episodes without touching app logic.
"""

CHARACTERS = [
    {
        "id": "wolio", "name": "Wolio", "emoji": "🤖", "color": "#7c5cff",
        "role": "Your AI buddy & guide", "world": None,
        "tagline": "Let's gooo! 🚀",
        "traits": ["Curious", "Upbeat", "Loyal"],
        "bio": "A pocket-sized robot built by the kids of the Curio-Verse to help "
               "anyone who's curious. Wolio powers up on questions and treats YOU as the hero.",
    },
    {
        "id": "astra", "name": "Astra Nova", "emoji": "🚀", "color": "#6C5CE7",
        "role": "Guardian of Space World", "world": "space",
        "tagline": "To the stars and back!",
        "traits": ["Fearless", "Warm", "Explorer"],
        "bio": "A young explorer who drifted off course on her first solo flight — and "
               "turned being lost into the greatest adventure, mapping every planet.",
    },
    {
        "id": "digit", "name": "Detective Digit", "emoji": "🦉", "color": "#00B894",
        "role": "Guardian of Math Mystery", "world": "math",
        "tagline": "Every mystery hides a number.",
        "traits": ["Witty", "Sharp", "Calm"],
        "bio": "The Curio-Verse's greatest detective owl. Cracks vault codes, pizza heists "
               "and race-day riddles using the power of maths.",
    },
    {
        "id": "pip", "name": "Pip", "emoji": "🦊", "color": "#E17055",
        "role": "Guardian of Story Universe", "world": "story",
        "tagline": "Brave isn't loud.",
        "traits": ["Gentle", "Brave", "Big-hearted"],
        "bio": "A little fox who was once afraid of the dark forest of stories — now lights "
               "the way for others, learning new words and feelings on every page.",
    },
    {
        "id": "chip", "name": "Chip", "emoji": "⏳", "color": "#0984E3",
        "role": "Guardian of Time Travel", "world": "time",
        "tagline": "Yesterday's a story, tomorrow's a quest.",
        "traits": ["Playful", "Wise", "Speedy"],
        "bio": "A glowing hourglass-sprite who keeps the timeline and whisks curious kids "
               "off to meet dinosaurs and build pyramids.",
    },
    {
        "id": "nani", "name": "Nani Vora", "emoji": "👵", "color": "#fd79a8",
        "role": "The Inventor", "world": None,
        "tagline": "Beta, let's experiment!",
        "traits": ["Brilliant", "Warm", "Hands-on"],
        "bio": "Runs the Curio-Lab where all the worlds connect. She believes every single "
               "child is a scientist waiting to discover something.",
    },
    {
        "id": "muddle", "name": "Muddle", "emoji": "🌫️", "color": "#636e72",
        "role": "The Confusion Gremlin", "world": None, "villain": True,
        "tagline": "Eh, why bother learning?",
        "traits": ["Silly", "Lazy", "Harmless"],
        "bio": "A goofy fog-blob who fogs up a topic so no one has to think. He's always "
               "dispelled the moment a child learns something — which makes YOU the hero.",
    },
]

_BY_ID = {c["id"]: c for c in CHARACTERS}


def character(cid):
    return _BY_ID.get(cid)


# --- Comic episodes (panel-by-panel, emoji-driven) ------------------------
# Each panel: scene (backdrop emoji), speaker (character id or None=narration), text.
COMICS = [
    {
        "id": "fog-over-fraction-falls",
        "title": "The Fog Over Fraction Falls",
        "cover": "🌫️", "world": "math", "stars": ["digit", "pip", "muddle"],
        "blurb": "Muddle fogs up Fraction Falls — can Digit and Pip clear it?",
        "panels": [
            {"scene": "🏞️", "speaker": None, "text": "At Fraction Falls, the water always splits into perfect halves and quarters…"},
            {"scene": "🌫️", "speaker": "muddle", "text": "Heh heh… let's fog it ALL up. Then nobody has to think! Eh, why bother?"},
            {"scene": "🦊", "speaker": "pip", "text": "Oh no — I can't tell half from a quarter anymore! It's all muddled!"},
            {"scene": "🦉", "speaker": "digit", "text": "Steady, Pip. Every mystery hides a number. A pizza cut in two… each piece is one-half. 🍕"},
            {"scene": "🍕", "speaker": "pip", "text": "So if we cut it again… four pieces… each is one-quarter?!"},
            {"scene": "🦉", "speaker": "digit", "text": "Exactly. Two quarters make a half. You just solved it!"},
            {"scene": "🌫️", "speaker": "muddle", "text": "Noooo! Someone LEARNED something! I'm fading… *poof*"},
            {"scene": "🌈", "speaker": "pip", "text": "The fog's gone! Fraction Falls is sparkling again. Brave isn't loud — it's curious!"},
        ],
        "moral": "Fractions are just equal pieces of a whole. Two quarters = one half.",
    },
    {
        "id": "why-the-apple-fell",
        "title": "Astra and the Falling Apple",
        "cover": "🍎", "world": "space", "stars": ["astra", "wolio", "nani"],
        "blurb": "Astra learns the secret pull that brings everything down.",
        "panels": [
            {"scene": "🌳", "speaker": "astra", "text": "Wolio! An apple just fell on my helmet. Why does everything fall DOWN?"},
            {"scene": "🤖", "speaker": "wolio", "text": "Great question! Let's gooo to Nani's lab and find out! 🚀"},
            {"scene": "🔬", "speaker": "nani", "text": "Beta, it's gravity — an invisible pull every planet has, tugging things toward it."},
            {"scene": "🌙", "speaker": "nani", "text": "On the Moon the pull is weaker — you'd bounce like a feather!"},
            {"scene": "🪐", "speaker": "astra", "text": "And on Jupiter it'd pull so hard I could barely stand! So THAT'S why I fell fast on Mars."},
            {"scene": "🤖", "speaker": "wolio", "text": "Think of gravity like an invisible hug from the ground. 🧲"},
            {"scene": "🌟", "speaker": "astra", "text": "Curiosity wins again. To the stars and back!"},
        ],
        "moral": "Gravity is the pull that brings things down — bigger worlds pull harder.",
    },
]

_COMIC_BY_ID = {c["id"]: c for c in COMICS}


def comic(cid):
    return _COMIC_BY_ID.get(cid)
