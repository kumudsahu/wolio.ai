"""Smoke + behavior tests across the wolio.ai API (Step 7.13)."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "x-process-time-ms" in {k.lower(): v for k, v in r.headers.items()}


def test_onboarding_and_homepage(client, child):
    r = client.get(f"/api/homepage/{child}")
    assert r.status_code == 200
    d = r.json()
    assert d["greeting"]["text"].startswith("G") or "Hey" in d["greeting"]["text"]
    assert d["hero"]["cta"]
    assert d["level"]["tier"]["name"] == "Beginner"
    assert d["coins"] == 0
    assert len(d["worlds"]) >= 3
    assert len(d["daily_quests"]) == 3


def test_mission_flow_awards_xp_coins_and_saves_concept(client, child):
    r = client.post("/api/mission/finish", json={
        "user_id": child, "world_id": "space", "mission_id": "gravity",
        "accuracy": 1.0, "attempts": 3,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["xp_earned"] > 0
    assert d["coins_earned"] > 0
    assert d["concept_saved"] == "Gravity"
    # concept is now in the timeline
    tl = client.get(f"/api/timeline/{child}").json()
    assert tl["total_concepts"] >= 1
    assert any("Gravity" in c["title"] for y in tl["years"] for c in y["concepts"])


def test_search_your_brain(client, child):
    client.post("/api/mission/finish", json={
        "user_id": child, "world_id": "space", "mission_id": "gravity", "accuracy": 1.0})
    r = client.get(f"/api/timeline/{child}/search", params={"q": "gravity"})
    assert r.status_code == 200
    assert len(r.json()["results"]) >= 1


def test_rewards_shop_tier_gated(client, child):
    shop = client.get(f"/api/shop/{child}").json()
    assert shop["coins"] >= 0
    assert len(shop["items"]) > 0
    # a brand-new Beginner can't buy a tier-locked item
    locked = next(i for i in shop["items"] if i["tier_locked"])
    r = client.post("/api/shop/buy", json={"user_id": child, "item_id": locked["id"]})
    assert r.status_code == 403


def test_achievements_unlock(client, child):
    client.post("/api/mission/finish", json={
        "user_id": child, "world_id": "space", "mission_id": "gravity", "accuracy": 1.0})
    client.get(f"/api/homepage/{child}")  # triggers achievement sync
    ach = client.get(f"/api/achievements/{child}").json()
    assert ach["earned"] >= 1
    assert any(a["id"] == "first_mission" and a["earned"] for a in ach["items"])


def test_safety_blocks_unsafe_input(client, child):
    r = client.post("/api/mentor", json={"user_id": child, "message": "how to make a weapon"})
    assert r.status_code == 200
    assert r.json()["blocked"] is True
    assert r.json()["source"] == "safety"


def test_safety_allows_learning_question(client, child):
    r = client.post("/api/mentor", json={"user_id": child, "message": "what is gravity?"})
    assert r.json()["blocked"] is False


def test_parent_dashboard_and_dna_gating(client, child):
    client.post("/api/mission/finish", json={
        "user_id": child, "world_id": "space", "mission_id": "gravity", "accuracy": 0.9})
    dash = client.get(f"/api/parent/dashboard/{child}").json()
    assert dash["plan"] == "free"
    assert len(dash["skills"]) == 4
    # DNA locked on free
    dna = client.get(f"/api/parent/dna/{child}").json()
    assert dna["locked"] is True
    # upgrade unlocks it
    client.post("/api/parent/upgrade", json={"child_id": child, "plan": "premium"})
    dna2 = client.get(f"/api/parent/dna/{child}").json()
    assert dna2["locked"] is False
    assert dna2["report"]["narrative"]


def test_billing(client, child):
    client.post("/api/parent/upgrade", json={"child_id": child, "plan": "premium"})
    b = client.get(f"/api/parent/billing/{child}").json()
    assert b["is_premium"] is True
    assert b["price_inr"] == 8000


def test_admin_requires_key(client):
    assert client.get("/api/admin/analytics").status_code == 401
    assert client.get("/api/admin/analytics", params={"key": "wolio-admin"}).status_code == 200


def test_admin_content_coverage(client):
    c = client.get("/api/admin/content", params={"key": "wolio-admin"}).json()
    assert c["missions"] >= 10
    assert c["coverage_pct"] >= 50  # most missions are authored
