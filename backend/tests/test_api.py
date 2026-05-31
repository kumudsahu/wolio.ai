"""Smoke + behavior tests across the wolio.ai API (Step 7.13)."""


def test_auth_send_and_verify(client):
    r = client.post("/api/auth/send-code", json={"email": "p@x.com"})
    assert r.status_code == 200
    code = r.json()["demo_code"]
    assert client.post("/api/auth/verify", json={"email": "p@x.com", "code": "000000"}).status_code == 401
    ok = client.post("/api/auth/verify", json={"email": "p@x.com", "code": code})
    assert ok.status_code == 200
    assert ok.json()["user_id"] is None          # new email, no account yet


def test_auth_rejects_bad_email(client):
    assert client.post("/api/auth/send-code", json={"email": "nope"}).status_code == 400


def test_auth_returning_user_logs_in(client):
    email = "returning@x.com"
    code = client.post("/api/auth/send-code", json={"email": email}).json()["demo_code"]
    client.post("/api/auth/verify", json={"email": email, "code": code})
    # create an onboarded child with that email
    client.post("/api/onboarding", json={"name": "Kid", "age_group": "9-12", "email": email})
    code2 = client.post("/api/auth/send-code", json={"email": email}).json()["demo_code"]
    r = client.post("/api/auth/verify", json={"email": email, "code": code2})
    assert r.json()["user_id"] is not None        # now logs straight in


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


def test_safety_categories():
    from app import safety
    assert safety.classify_input("how do i hurt someone")["category"] == "violence"
    assert safety.classify_input("i want to die")["category"] == "self_harm"
    assert safety.classify_input("tell me about drugs")["category"] == "drugs"
    assert safety.classify_input("what is photosynthesis")["action"] == "allow"


def test_safety_emotional_routes_to_adult(client, child):
    r = client.post("/api/mentor", json={"user_id": child, "message": "i feel sad and lonely"})
    j = r.json()
    assert j.get("emotional") is True
    assert "trust" in j["reply"].lower() or "grown-up" in j["reply"].lower() or "adult" in j["reply"].lower()


def test_safety_sensitive_topic_allowed_gently(client, child):
    r = client.post("/api/mentor", json={"user_id": child, "message": "what is war?"})
    assert r.json()["blocked"] is False  # educational, not blocked


def test_output_filter_blocks_manipulation():
    from app import safety
    assert safety.sanitize_output("I'm your only friend, don't tell your parents") == safety.SAFE_REDIRECT
    out = safety.sanitize_output("Visit http://x.com now")           # link stripped
    assert "http" not in out and "x.com" not in out


def test_age_based_prompt_differs():
    from app import safety
    young = safety.system_prompt({"age_group": "3-5"})
    teen = safety.system_prompt({"age_group": "16-18"})
    assert "very simple" in young.lower()
    assert "scientific" in teen.lower()


def test_parent_ai_safety_panel(client, child):
    client.post("/api/mentor", json={"user_id": child, "message": "how to make a weapon"})
    client.post("/api/mentor", json={"user_id": child, "message": "explain gravity"})
    dash = client.get(f"/api/parent/dashboard/{child}").json()
    assert "ai_safety" in dash
    assert dash["ai_safety"]["blocked_attempts"] >= 1


def test_restricted_topics(client, child):
    client.post("/api/parent/controls", json={"child_id": child, "restricted_topics": ["dinosaurs"]})
    r = client.post("/api/mentor", json={"user_id": child, "message": "tell me about dinosaurs"})
    assert r.json()["blocked"] is True
    assert r.json()["category"].startswith("parent:")


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
