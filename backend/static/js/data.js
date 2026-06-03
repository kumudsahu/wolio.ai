/* Static client-side data for onboarding + home flavor. */
window.DATA = {
  ages: [
    { id: "3-5",   label: "3–5",   sub: "Tiny explorer" },
    { id: "6-8",   label: "6–8",   sub: "Curious kid" },
    { id: "9-12",  label: "9–12",  sub: "Young genius" },
    { id: "13-16", label: "13–16", sub: "Future maker" },
    { id: "16-18", label: "16–18", sub: "Almost pro" },
  ],
  languages: [
    { id: "english",  label: "English",  emoji: "🇬🇧" },
    { id: "hinglish", label: "Hinglish", emoji: "😎" },
    { id: "hindi",    label: "हिंदी",     emoji: "🇮🇳" },
  ],
  interests: [
    { id: "space",   label: "Space",   emoji: "🚀" },
    { id: "animals", label: "Animals", emoji: "🐯" },
    { id: "cars",    label: "Cars",    emoji: "🏎️" },
    { id: "stories", label: "Stories", emoji: "📚" },
    { id: "games",   label: "Games",   emoji: "🎮" },
    { id: "art",     label: "Art",     emoji: "🎨" },
    { id: "sports",  label: "Sports",  emoji: "⚽" },
    { id: "music",   label: "Music",   emoji: "🎵" },
  ],
  styles: [
    { id: "games",   label: "Games",   emoji: "🎮", sub: "Play & win" },
    { id: "stories", label: "Stories", emoji: "📖", sub: "Adventures" },
    { id: "quizzes", label: "Quizzes", emoji: "🧠", sub: "Challenges" },
  ],
  tones: [
    { id: "fun",       label: "Fun",       emoji: "😜" },
    { id: "calm",      label: "Calm",      emoji: "😌" },
    { id: "energetic", label: "Energetic", emoji: "⚡" },
  ],
  avatars: ["🦊", "🐯", "🐼", "🚀", "🦄", "🤖", "🐸", "🦁", "🐙", "🦖", "👾", "🐲"],
  // Curio-Verse cast — kids pick a character as their avatar (ties users to the IP)
  crewAvatars: [
    { emoji: "🤖", name: "Wolio", img: "/static/img/wolio.svg" },
    { emoji: "🚀", name: "Astra", img: "/static/img/astra.svg" },
    { emoji: "🦉", name: "Digit", img: "/static/img/digit.svg" },
    { emoji: "🦊", name: "Pip",   img: "/static/img/pip.svg" },
    { emoji: "⏳", name: "Chip",  img: "/static/img/chip.svg" },
    { emoji: "👵", name: "Nani",  img: "/static/img/nani.svg" },
    { emoji: "🌫️", name: "Muddle", img: "/static/img/muddle.svg" },
  ],
  behavior: [
    {
      id: "visual", icon: "🎨", q: "Pick the one you like the most!",
      options: [{ t: "🌈 Bright & colorful", v: "visual" }, { t: "🧩 Puzzles & shapes", v: "logical" }, { t: "📖 A good story", v: "narrative" }],
    },
    {
      id: "logic", icon: "🧩", q: "What comes next?  🔴 🔵 🔴 🔵 __",
      options: [{ t: "🔴 Red", v: "correct" }, { t: "🔵 Blue", v: "wrong" }, { t: "🟢 Green", v: "wrong" }],
    },
    {
      id: "story", icon: "🦊", q: "The fox finds a locked door. What does it do?",
      options: [{ t: "🔑 Look for a key", v: "explorer" }, { t: "💥 Break it open", v: "bold" }, { t: "🤔 Ask a friend", v: "social" }],
    },
  ],
  quickLearn: [
    { q: "Saturn could float on water! 🪐", go: "Why?", subject: "Science" },
    { q: "Your heart beats ~1L of blood a minute ❤️", go: "Whoa, learn", subject: "Biology" },
    { q: "Zero was invented in India 🔢", go: "Story time", subject: "Math" },
    { q: "Octopuses have 3 hearts 🐙", go: "Tap to learn", subject: "Science" },
  ],
  quests: [
    { icon: "🚀", t: "Complete 2 missions", x: "+40 XP", id: "q1" },
    { icon: "🧠", t: "Revise 3 concepts", x: "+30 XP", id: "q2" },
    { icon: "🧮", t: "Play 1 math game", x: "+20 XP", id: "q3" },
  ],
};
