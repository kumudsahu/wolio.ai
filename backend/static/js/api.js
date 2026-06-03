/* Thin fetch wrapper around the FastAPI backend. */
window.API = {
  async _post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.text()) || r.statusText);
    return r.json();
  },
  async _get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(r.statusText);
    return r.json();
  },
  async _patch(path, body) {
    const r = await fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(r.statusText);
    return r.json();
  },
  characters: () => API._get("/api/characters"),
  comicsList: () => API._get("/api/comics"),
  comic: (id) => API._get(`/api/comics/${id}`),
  authSendCode: (email) => API._post("/api/auth/send-code", { email }),
  authVerify: (email, code) => API._post("/api/auth/verify", { email, code }),
  onboarding: (payload) => API._post("/api/onboarding", payload),
  me: (id) => API._get(`/api/me/${id}`),
  updatePrefs: (id, prefs) => API._patch(`/api/me/${id}`, prefs),
  homepage: (id) => API._get(`/api/homepage/${id}`),
  quickLearn: (payload) => API._post("/api/quick-learn", payload),
  missionGet: (world, mission, uid) => API._get(`/api/mission/${world}/${mission}${uid ? `?user_id=${uid}` : ""}`),
  missionFinish: (payload) => API._post("/api/mission/finish", payload),
  shop: (id) => API._get(`/api/shop/${id}`),
  buyItem: (user_id, item_id) => API._post("/api/shop/buy", { user_id, item_id }),
  achievements: (id) => API._get(`/api/achievements/${id}`),
  parentDashboard: (id) => API._get(`/api/parent/dashboard/${id}`),
  parentDna: (id) => API._get(`/api/parent/dna/${id}`),
  parentReport: (id, period) => API._get(`/api/parent/report/${id}?period=${period}`),
  parentGoals: (payload) => API._post("/api/parent/goals", payload),
  parentControls: (payload) => API._post("/api/parent/controls", payload),
  parentUpgrade: (child_id, plan) => API._post("/api/parent/upgrade", { child_id, plan }),
  parentChildren: (id) => API._get(`/api/parent/children/${id}`),
  parentAddChild: (payload) => API._post("/api/parent/add-child", payload),
  worlds: (id) => API._get(`/api/worlds${id ? `?user_id=${id}` : ""}`),
  completeMission: (user_id, world_id, mission_id) =>
    API._post("/api/missions/complete", { user_id, world_id, mission_id }),
  timeline: (id) => API._get(`/api/timeline/${id}`),
  searchBrain: (id, q) => API._get(`/api/timeline/${id}/search?q=${encodeURIComponent(q)}`),
  conceptCard: (uid, cid) => API._get(`/api/concept/${uid}/${cid}`),
  reviseConcept: (user_id, concept_id) => API._post("/api/concept/revise", { user_id, concept_id }),
  insights: (id) => API._get(`/api/insights/${id}`),
  revise: (user_id, scope) => API._post("/api/timeline/revise", { user_id, scope }),
  mentor: (payload) => API._post("/api/mentor", payload),
};
