/**
 * API Service Layer
 *
 * Centralised Axios instance and all API call functions.
 * Every function returns the Axios promise for consumption
 * by Redux thunks or components.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 30000, // 30s — LLM calls can be slow
});

// ── Interactions ─────────────────────────────────────────────

/** Log a new interaction from free-text note */
export const logInteraction = (note) =>
  api.post("/interactions/log", { note });

/** Edit an existing interaction */
export const editInteraction = (interactionId, editRequest) =>
  api.put(`/interactions/${interactionId}`, { edit_request: editRequest });

/** Get HCP interaction history */
export const getHCPHistory = (hcpId, limit = 10) =>
  api.get(`/interactions/hcp/${hcpId}`, { params: { limit } });

/** Generate AI follow-up suggestions */
export const suggestFollowUp = (interactionId) =>
  api.post(`/interactions/${interactionId}/suggest-followup`);


// ── HCPs ─────────────────────────────────────────────────────

/** Search HCPs by name or specialty */
export const searchHCPs = (query) =>
  api.get("/hcps/search", { params: { q: query } });

// ── Chat ─────────────────────────────────────────────────────

/** Send a message to the LangGraph agent */
export const sendChatMessage = (message) =>
  api.post("/chat", { message });

// ── Health ───────────────────────────────────────────────────

/** Health check */
export const healthCheck = () => axios.get(`${API_BASE.replace("/api", "")}/health`);

export default api;
