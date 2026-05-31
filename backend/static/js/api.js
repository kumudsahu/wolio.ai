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
  onboarding: (payload) => API._post("/api/onboarding", payload),
  me: (id) => API._get(`/api/me/${id}`),
  updatePrefs: (id, prefs) => API._patch(`/api/me/${id}`, prefs),
  homepage: (id) => API._get(`/api/homepage/${id}`),
  quickLearn: (payload) => API._post("/api/quick-learn", payload),
  missionGet: (world, mission, uid) => API._get(`/api/mission/${world}/${mission}${uid ? `?user_id=${uid}` : ""}`),
  missionFinish: (payload) => API._post("/api/mission/finish", payload),
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
