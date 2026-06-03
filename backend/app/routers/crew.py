"""The Curio-Verse crew + comics API."""
from fastapi import APIRouter, HTTPException

from ..characters import CHARACTERS, COMICS, character, comic

router = APIRouter(prefix="/api", tags=["crew"])


@router.get("/characters")
def list_characters():
    return {"characters": CHARACTERS}


@router.get("/characters/{cid}")
def get_character(cid: str):
    c = character(cid)
    if not c:
        raise HTTPException(404, "Character not found")
    return c


@router.get("/comics")
def list_comics():
    # lightweight list (no panels) for the shelf
    return {"comics": [{k: v for k, v in c.items() if k != "panels"} for c in COMICS]}


@router.get("/comics/{cid}")
def get_comic(cid: str):
    c = comic(cid)
    if not c:
        raise HTTPException(404, "Comic not found")
    # attach resolved speaker info to each panel for the reader
    panels = []
    for p in c["panels"]:
        ch = character(p["speaker"]) if p.get("speaker") else None
        panels.append({**p,
                       "speaker_name": ch["name"] if ch else None,
                       "speaker_emoji": ch["emoji"] if ch else None,
                       "speaker_color": ch["color"] if ch else None})
    return {**c, "panels": panels}
