"""Mission content — the authored 'playbooks' that power the Learning World System.

Each mission runs a fixed flow:
    Story Intro → Exploration → Game → Quiz → AI Explanation → Reward → Memory Save

Content is script-driven (plain data) so designers can add missions without code.
Games reuse a small set of engines: slider | match | order | choose.
Any mission without an authored playbook falls back to a generated one so the
whole catalogue is always playable.
"""

# --- mastery → level mapping (3.4 Level System) ---------------------------
LEVELS = [(0, "Discovery"), (26, "Understanding"), (51, "Application"), (81, "Mastery")]


def level_label(mastery: int) -> str:
    label = LEVELS[0][1]
    for threshold, name in LEVELS:
        if mastery >= threshold:
            label = name
    return label


def level_index(mastery: int) -> int:
    idx = 0
    for i, (threshold, _) in enumerate(LEVELS):
        if mastery >= threshold:
            idx = i
    return idx


# --- authored playbooks, keyed by "world/mission" -------------------------
PLAYBOOKS = {
    "space/gravity": {
        "scene": "🪐",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "Your spaceship just crash-landed on Mars! 😱"},
            {"who": "Wolio", "emoji": "🤖", "text": "It fell SO fast. Why do things fall at all? Let's find out!"},
        ],
        "exploration": {
            "prompt": "Tap each world to feel how hard it pulls you down 👇",
            "items": [
                {"emoji": "🌙", "label": "Moon", "fact": "The Moon pulls gently — you'd bounce like a feather!"},
                {"emoji": "🌍", "label": "Earth", "fact": "Earth pulls at 9.8 m/s² — normal, like home."},
                {"emoji": "🪐", "label": "Jupiter", "fact": "Jupiter pulls SO hard you could barely stand up!"},
            ],
        },
        "game": {
            "type": "match", "prompt": "Match each world to how its gravity feels:",
            "pairs": [
                {"l": "🌙 Moon", "r": "Super floaty"},
                {"l": "🌍 Earth", "r": "Just normal"},
                {"l": "🪐 Jupiter", "r": "Crushing heavy"},
            ],
            "success": "You felt gravity change across worlds! 🌌",
        },
        "quiz": [
            {"q": "What makes an apple fall from a tree?", "options": ["Gravity", "Wind", "Magic"],
             "answer": 0, "hint": "It's the invisible pull from the ground.", "explain": "Gravity pulls every object down toward the ground."},
            {"q": "Where would you weigh the LEAST?", "options": ["On the Moon", "On Earth", "On Jupiter"],
             "answer": 0, "hint": "Smaller, lighter worlds pull less.", "explain": "The Moon's gravity is about 1/6 of Earth's — you'd feel super light!"},
            {"q": "Why did your ship fall fast on Mars?", "options": ["Gravity pulled it down", "It was sleepy", "The wind pushed it"],
             "answer": 0, "hint": "Same reason apples fall.", "explain": "Mars has gravity too, so it pulled your ship straight down."},
        ],
        "explanation": {"analogy": "Think of gravity like an invisible magnet inside every planet, pulling everything toward it 🧲",
                        "recap": "Gravity = the pull that brings things down. Bigger worlds pull harder."},
    },

    "space/mars-rover": {
        "scene": "🛞",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "The Mars rover is STUCK in the sand! 🛞"},
            {"who": "Wolio", "emoji": "🤖", "text": "To move it we need a force — a push or a pull. Let's engineer it!"},
        ],
        "exploration": {
            "prompt": "Tap each action to see the force at work 👇",
            "items": [
                {"emoji": "👉", "label": "Push", "fact": "A push moves things away from you."},
                {"emoji": "🫳", "label": "Pull", "fact": "A pull brings things toward you."},
                {"emoji": "🛑", "label": "Friction", "fact": "Friction is a force that slows things down."},
            ],
        },
        "game": {
            "type": "slider", "prompt": "Apply just enough force to free the rover 🛞", "emoji": "🛞",
            "min": 0, "max": 100, "target": 70, "tol": 12, "unit": "N",
            "low": "Too gentle — still stuck in the sand.", "high": "Too much — the rover flipped over!",
            "success": "Perfect force — the rover rolls free! 🎉",
        },
        "quiz": [
            {"q": "A force is best described as a…", "options": ["Push or a pull", "Color", "Sound"],
             "answer": 0, "hint": "It's how we move things.", "explain": "A force is simply a push or a pull on an object."},
            {"q": "What force slows a sliding rover down?", "options": ["Friction", "Gravity up", "Light"],
             "answer": 0, "hint": "It happens when surfaces rub.", "explain": "Friction acts between surfaces and slows motion."},
            {"q": "More force on the rover usually means…", "options": ["It speeds up more", "It stops", "It shrinks"],
             "answer": 0, "hint": "Bigger push, bigger change.", "explain": "A bigger force creates a bigger change in motion."},
        ],
        "explanation": {"analogy": "A force is like a high-five to an object — push hard and it moves more 👋",
                        "recap": "Forces (pushes & pulls) start, stop, and change how things move."},
    },

    "space/saturn": {
        "scene": "🪐",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "Wild fact: if you had a bathtub big enough, Saturn would FLOAT! 🛁"},
            {"who": "Wolio", "emoji": "🤖", "text": "How can a giant planet float? The secret is density. Let's explore!"},
        ],
        "exploration": {
            "prompt": "Tap each object — will it float or sink? 👇",
            "items": [
                {"emoji": "🪵", "label": "Cork", "fact": "Cork is light for its size — it floats!"},
                {"emoji": "🪨", "label": "Rock", "fact": "A rock is packed tight and heavy — it sinks."},
                {"emoji": "🪐", "label": "Saturn", "fact": "Saturn is mostly gas — lighter than water, so it floats!"},
            ],
        },
        "game": {
            "type": "match", "prompt": "Sort each thing: does it float or sink in water?",
            "pairs": [
                {"l": "🪵 Cork", "r": "Floats"},
                {"l": "🪨 Rock", "r": "Sinks"},
                {"l": "🪐 Saturn", "r": "Floats"},
            ],
            "success": "You cracked the density code! 🌊",
        },
        "quiz": [
            {"q": "Things float when they are…", "options": ["Less dense than water", "Very colorful", "Very big"],
             "answer": 0, "hint": "It's about weight for the size.", "explain": "If something is less dense than water, it floats."},
            {"q": "Why would Saturn float?", "options": ["It's mostly light gas", "It's made of rock", "It's hot"],
             "answer": 0, "hint": "What is Saturn made of?", "explain": "Saturn is mostly gas, making it less dense than water."},
            {"q": "Density means how…", "options": ["Tightly packed something is", "Tall something is", "Loud something is"],
             "answer": 0, "hint": "Packed tight vs. loose.", "explain": "Density is how much stuff is packed into a space."},
        ],
        "explanation": {"analogy": "Density is like a backpack: same size, but a feather-filled one floats and a rock-filled one sinks 🎒",
                        "recap": "Less dense than water → floats. More dense → sinks."},
    },

    "math/fractions": {
        "scene": "🍕",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "Someone raided the pizza! 🍕 A sneaky slice thief struck!"},
            {"who": "Wolio", "emoji": "🤖", "text": "To catch them we need fractions — pieces of a whole. Let's slice it up!"},
        ],
        "exploration": {
            "prompt": "Tap each pizza to see its fraction 👇",
            "items": [
                {"emoji": "🍕", "label": "Whole", "fact": "A whole pizza = 1 (or 4/4)."},
                {"emoji": "🍕", "label": "Half", "fact": "Cut once = two halves, each is 1/2."},
                {"emoji": "🍕", "label": "Quarter", "fact": "Cut into 4 = quarters, each is 1/4."},
            ],
        },
        "game": {
            "type": "match", "prompt": "Match each fraction to how much pizza it is:",
            "pairs": [
                {"l": "1/2", "r": "Half the pizza"},
                {"l": "1/4", "r": "One of four slices"},
                {"l": "3/4", "r": "Three of four slices"},
            ],
            "success": "Fraction detective skills unlocked! 🕵️",
        },
        "quiz": [
            {"q": "You ate 2 of 4 slices. That's the same as…", "options": ["1/2", "1/4", "3/4"],
             "answer": 0, "hint": "2 out of 4 simplifies.", "explain": "2/4 = 1/2 — half the pizza."},
            {"q": "Which is BIGGER?", "options": ["1/2", "1/3", "1/4"],
             "answer": 0, "hint": "Fewer pieces = bigger pieces.", "explain": "1/2 is the biggest — the fewer the slices, the larger each one."},
            {"q": "The bottom number of a fraction tells you…", "options": ["Total equal pieces", "Your age", "The flavor"],
             "answer": 0, "hint": "How many pieces in all.", "explain": "The bottom (denominator) = total equal pieces in the whole."},
        ],
        "explanation": {"analogy": "A fraction is just pizza math: top = slices you grabbed, bottom = total slices 🍕",
                        "recap": "Fractions describe parts of a whole. Fewer pieces means bigger pieces."},
    },

    "math/patterns": {
        "scene": "🔢",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "A locked vault blocks our path! 🔐"},
            {"who": "Wolio", "emoji": "🤖", "text": "The code is hidden in a pattern. Spot the rule and we're in!"},
        ],
        "exploration": {
            "prompt": "Tap each sequence to reveal its hidden rule 👇",
            "items": [
                {"emoji": "🔴", "label": "🔴🔵🔴🔵", "fact": "Rule: red, blue, repeat!"},
                {"emoji": "2️⃣", "label": "2, 4, 6, 8", "fact": "Rule: add 2 each time."},
                {"emoji": "⭐", "label": "1, 2, 4, 8", "fact": "Rule: double each time!"},
            ],
        },
        "game": {
            "type": "choose", "prompt": "Crack the code! What comes next?  🔴 🔵 🔴 🔵 __",
            "options": [
                {"t": "🔴 Red", "ok": True, "fx": "Yes! The red-blue rule repeats."},
                {"t": "🔵 Blue", "ok": False, "fx": "Close — but it just had a blue."},
                {"t": "🟢 Green", "ok": False, "fx": "Green isn't part of this pattern."},
            ],
            "success": "Vault unlocked! 🔓",
        },
        "quiz": [
            {"q": "What comes next?  2, 4, 6, 8, __", "options": ["10", "9", "12"],
             "answer": 0, "hint": "Add 2 each time.", "explain": "The rule is +2, so 8 + 2 = 10."},
            {"q": "What comes next?  5, 10, 15, __", "options": ["20", "16", "25"],
             "answer": 0, "hint": "Count by fives.", "explain": "The rule is +5, so 15 + 5 = 20."},
            {"q": "What comes next?  1, 2, 4, 8, __", "options": ["16", "10", "12"],
             "answer": 0, "hint": "Each number doubles.", "explain": "The rule is ×2, so 8 × 2 = 16."},
        ],
        "explanation": {"analogy": "A pattern is a secret rule on repeat — find the rule and you can predict the future 🔁",
                        "recap": "Patterns follow a rule. Spot the rule to know what's next."},
    },

    "math/speed": {
        "scene": "🏎️",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "It's race day and YOU are the engineer! 🏁"},
            {"who": "Wolio", "emoji": "🤖", "text": "To win we need speed math: speed = distance ÷ time. Let's tune the car!"},
        ],
        "exploration": {
            "prompt": "Tap each racer to see their speed 👇",
            "items": [
                {"emoji": "🐢", "label": "Tortoise", "fact": "Slow and steady: 1 m every second."},
                {"emoji": "🚗", "label": "City car", "fact": "Zippy: about 15 m every second."},
                {"emoji": "🏎️", "label": "Race car", "fact": "Blazing: 80+ m every second!"},
            ],
        },
        "game": {
            "type": "slider", "prompt": "Set your speed to finish 100 m in exactly 5 s 🏁", "emoji": "🏎️",
            "min": 0, "max": 40, "target": 20, "tol": 3, "unit": "m/s",
            "low": "Too slow — you won't finish in time!", "high": "Too fast — you overshot the math!",
            "success": "Bang on! 100 m ÷ 5 s = 20 m/s. You win! 🏆",
        },
        "quiz": [
            {"q": "Speed is calculated as…", "options": ["Distance ÷ time", "Distance × color", "Time ÷ weight"],
             "answer": 0, "hint": "How far over how long.", "explain": "Speed = distance ÷ time."},
            {"q": "Two cars go the same distance. The faster one takes…", "options": ["Less time", "More time", "The same time"],
             "answer": 0, "hint": "Faster = quicker.", "explain": "More speed means less time for the same distance."},
            {"q": "Go 100 m in 10 s. Your speed is…", "options": ["10 m/s", "1000 m/s", "1 m/s"],
             "answer": 0, "hint": "100 ÷ 10.", "explain": "100 m ÷ 10 s = 10 m/s."},
        ],
        "explanation": {"analogy": "Speed is just 'how much ground per tick of the clock' — distance shared out over time ⏱️",
                        "recap": "Speed = distance ÷ time. Faster means less time for the same distance."},
    },

    "story/nani-1": {
        "scene": "👵",
        "story": [
            {"who": "Nani", "emoji": "👵", "text": "Beta, today we explore BIG words for little scientists! 🔬"},
            {"who": "Nani", "emoji": "👵", "text": "Collect words like treasures — they unlock new ideas."},
        ],
        "exploration": {
            "prompt": "Tap each word to learn its meaning 👇",
            "items": [
                {"emoji": "🤔", "label": "Curious", "fact": "Curious = wanting to learn or know more."},
                {"emoji": "🧪", "label": "Experiment", "fact": "Experiment = a test to find something out."},
                {"emoji": "💡", "label": "Discover", "fact": "Discover = to find something new."},
            ],
        },
        "game": {
            "type": "match", "prompt": "Match each word to its meaning:",
            "pairs": [
                {"l": "Curious", "r": "Wanting to know more"},
                {"l": "Experiment", "r": "A test to find out"},
                {"l": "Discover", "r": "To find something new"},
            ],
            "success": "Three new word-treasures collected! 💎",
        },
        "quiz": [
            {"q": "A 'curious' kid is one who…", "options": ["Loves to ask & learn", "Is always sleepy", "Hates questions"],
             "answer": 0, "hint": "Think question marks.", "explain": "Curious means eager to learn and ask questions."},
            {"q": "You 'discover' something when you…", "options": ["Find something new", "Lose it", "Break it"],
             "answer": 0, "hint": "New for the first time.", "explain": "To discover is to find something for the first time."},
            {"q": "An 'experiment' is a…", "options": ["Test to learn", "Type of food", "Color"],
             "answer": 0, "hint": "Scientists do these.", "explain": "An experiment is a careful test to find something out."},
        ],
        "explanation": {"analogy": "New words are like keys 🔑 — every one you collect unlocks a new door of ideas.",
                        "recap": "Curious = eager to learn · Experiment = a test · Discover = to find something new."},
    },

    "story/brave": {
        "scene": "🦊",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "Meet Pip the little fox 🦊 — alone in a dark, spooky forest."},
            {"who": "Pip", "emoji": "🦊", "text": "I'm scared… but I want to find my way home. What should I do?"},
        ],
        "exploration": {
            "prompt": "Tap each feeling to understand it 👇",
            "items": [
                {"emoji": "😨", "label": "Scared", "fact": "Scared = feeling afraid something bad might happen."},
                {"emoji": "🦁", "label": "Brave", "fact": "Brave = doing the right thing even when scared."},
                {"emoji": "😊", "label": "Proud", "fact": "Proud = a happy feeling after doing something hard."},
            ],
        },
        "game": {
            "type": "choose", "prompt": "Pip reaches a dark cave on the path home. What's the BRAVE choice?",
            "options": [
                {"t": "🔦 Take a breath and walk through carefully", "ok": True, "fx": "That's real bravery — scared but trying!"},
                {"t": "😭 Give up and cry", "ok": False, "fx": "It's okay to feel scared, but let's try together."},
                {"t": "🏃 Run away forever", "ok": False, "fx": "Running won't get Pip home — courage will."},
            ],
            "success": "Pip found courage and made it through! 🌟",
        },
        "quiz": [
            {"q": "Being brave means…", "options": ["Doing right even when scared", "Never feeling fear", "Being the biggest"],
             "answer": 0, "hint": "Fear can still be there.", "explain": "Bravery is acting rightly even when you feel afraid."},
            {"q": "Pip felt scared in the dark. That feeling is…", "options": ["Totally normal", "Wrong", "Silly"],
             "answer": 0, "hint": "Everyone feels it sometimes.", "explain": "Feeling scared is normal — what matters is what you do next."},
            {"q": "After being brave, Pip felt…", "options": ["Proud", "Bored", "Hungry"],
             "answer": 0, "hint": "A happy after-feeling.", "explain": "Doing something hard often leaves you feeling proud."},
        ],
        "explanation": {"analogy": "Bravery isn't having no fear — it's like a tiny light 🔦 you carry through the dark anyway.",
                        "recap": "Feeling scared is okay. Bravery = doing the right thing despite the fear."},
    },

    "time/dino": {
        "scene": "🦕",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "Hop in the time machine — destination: 100 million years ago! ⏳"},
            {"who": "Wolio", "emoji": "🤖", "text": "Welcome to the age of dinosaurs. Let's meet the locals! 🦖"},
        ],
        "exploration": {
            "prompt": "Tap each dinosaur to learn about it 👇",
            "items": [
                {"emoji": "🦖", "label": "T-Rex", "fact": "T-Rex was a huge meat-eater with tiny arms."},
                {"emoji": "🦕", "label": "Brachiosaurus", "fact": "A gentle giant that ate plants up high."},
                {"emoji": "🦏", "label": "Triceratops", "fact": "Had 3 horns and a big bony frill."},
            ],
        },
        "game": {
            "type": "match", "prompt": "Match each dinosaur to its trait:",
            "pairs": [
                {"l": "🦖 T-Rex", "r": "Meat eater"},
                {"l": "🦕 Brachiosaurus", "r": "Plant eater"},
                {"l": "🦏 Triceratops", "r": "Three horns"},
            ],
            "success": "You're a real paleontologist now! 🦴",
        },
        "quiz": [
            {"q": "Dinosaurs lived…", "options": ["Millions of years ago", "Last week", "In the future"],
             "answer": 0, "hint": "Long, long before people.", "explain": "Dinosaurs lived millions of years before humans existed."},
            {"q": "A T-Rex mainly ate…", "options": ["Meat", "Leaves", "Ice cream"],
             "answer": 0, "hint": "Those sharp teeth!", "explain": "T-Rex was a carnivore — a meat eater."},
            {"q": "Many scientists think dinosaurs vanished after a…", "options": ["Giant asteroid hit", "Big nap", "Rainy day"],
             "answer": 0, "hint": "Something fell from space.", "explain": "A massive asteroid impact likely caused their extinction."},
        ],
        "explanation": {"analogy": "Picture Earth's history as one school year — dinosaurs ruled for months, humans showed up in the last minute 🦖",
                        "recap": "Dinosaurs ruled Earth for ~165 million years, long before humans."},
    },

    "time/pyramid": {
        "scene": "🔺",
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": "Ancient Egypt, 4,500 years ago — the pharaoh needs a pyramid! 🏺"},
            {"who": "Wolio", "emoji": "🤖", "text": "You're the chief builder. Stack it strong and tall!"},
        ],
        "exploration": {
            "prompt": "Tap each part of the pyramid plan 👇",
            "items": [
                {"emoji": "🟫", "label": "Base", "fact": "The base is widest — it holds all the weight."},
                {"emoji": "🧱", "label": "Blocks", "fact": "Made of huge heavy stone blocks."},
                {"emoji": "🔺", "label": "Top", "fact": "The peak is the smallest, pointing to the sky."},
            ],
        },
        "game": {
            "type": "order", "prompt": "Stack the pyramid from bottom to top (tap in order):",
            "items": [
                {"emoji": "🟫", "label": "Wide base"},
                {"emoji": "🧱", "label": "Middle layer"},
                {"emoji": "🔺", "label": "Tiny top"},
            ],
            "success": "A perfectly balanced pyramid! 🏗️",
        },
        "quiz": [
            {"q": "The famous pyramids are in…", "options": ["Egypt", "Antarctica", "The ocean"],
             "answer": 0, "hint": "A desert country in Africa.", "explain": "The great pyramids were built in ancient Egypt."},
            {"q": "Pyramids were built mainly as…", "options": ["Tombs for pharaohs", "Swimming pools", "Schools"],
             "answer": 0, "hint": "For kings, after life.", "explain": "They were grand tombs for pharaohs (Egyptian kings)."},
            {"q": "Which part of a pyramid is widest?", "options": ["The base", "The top", "The middle"],
             "answer": 0, "hint": "It must hold the weight.", "explain": "The base is widest so it can support everything above."},
        ],
        "explanation": {"analogy": "A pyramid is like a stack of building blocks — widest on the bottom so it never topples 🧱",
                        "recap": "Pyramids were giant stone tombs built ~4,500 years ago for Egypt's pharaohs."},
    },
}


def get_playbook(world_id: str, mission: dict) -> dict:
    """Return the authored playbook, or a generated one so every mission plays."""
    key = f"{world_id}/{mission['id']}"
    if key in PLAYBOOKS:
        return PLAYBOOKS[key]
    return _generic_playbook(mission)


def _generic_playbook(mission: dict) -> dict:
    concept = mission.get("concept", "this idea")
    title = mission.get("title", "Mission")
    emoji = mission.get("emoji", "✨")
    return {
        "scene": emoji,
        "story": [
            {"who": "Wolio", "emoji": "🤖", "text": f"New adventure: {title}! {emoji}"},
            {"who": "Wolio", "emoji": "🤖", "text": f"Today we unlock the idea of {concept}. Let's go!"},
        ],
        "exploration": {
            "prompt": f"Tap to explore {concept} 👇",
            "items": [
                {"emoji": "🔍", "label": "Look", "fact": f"{concept} shows up all around us."},
                {"emoji": "💡", "label": "Think", "fact": f"Understanding {concept} helps solve real problems."},
                {"emoji": "🎯", "label": "Try", "fact": f"Practice makes {concept} easy!"},
            ],
        },
        "game": {
            "type": "choose", "prompt": f"Ready to master {concept}?",
            "options": [
                {"t": "🚀 Let's do it!", "ok": True, "fx": "That's the spirit!"},
                {"t": "🤔 Tell me more first", "ok": True, "fx": "Curiosity — love it!"},
            ],
            "success": f"You're ready for {concept}! 🌟",
        },
        "quiz": [
            {"q": f"Learning about {concept} is…", "options": ["Fun and useful", "Boring", "Impossible"],
             "answer": 0, "hint": "You're already doing great!", "explain": f"{concept} is everywhere and fun to learn."},
        ],
        "explanation": {"analogy": f"Every big idea like {concept} starts with one curious question 💭",
                        "recap": f"You explored {concept} through a story, a game, and a quiz."},
    }
