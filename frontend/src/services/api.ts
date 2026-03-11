/**
 * Trinity API client.
 * Wraps Axios with JWT auth injection and base URL configuration.
 */
import axios from "axios";

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL: BASE_URL });

// Inject Bearer token on every request
api.interceptors.request.use((config) => {
  // TODO: read token from SecureStore (expo-secure-store)
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────────

export const register = (email: string, password: string, displayName: string) =>
  api.post("/sessions/auth/register", { email, password, display_name: displayName });

export const login = (email: string, password: string) =>
  api.post("/sessions/auth/login", { email, password });

// ── Sessions ──────────────────────────────────────────────────────────────────

export type SessionType = "solo_a" | "solo_b" | "joint";

export const createSession = (sessionType: SessionType) =>
  api.post("/sessions/", { session_type: sessionType });

export const closeSession = (sessionId: string) =>
  api.post(`/sessions/${sessionId}/close`);

// ── Agent A ───────────────────────────────────────────────────────────────────

export const chatAgentA = (sessionId: string, message: string) =>
  api.post("/agent-a/chat", { session_id: sessionId, message });

// ── Agent B ───────────────────────────────────────────────────────────────────

export const chatAgentB = (sessionId: string, message: string) =>
  api.post("/agent-b/chat", { session_id: sessionId, message });

// ── Agent R ───────────────────────────────────────────────────────────────────

export const chatAgentR = (sessionId: string, message: string) =>
  api.post("/agent-r/chat", { session_id: sessionId, message });

export const jointSession = (sessionId: string, message: string) =>
  api.post("/agent-r/joint", { session_id: sessionId, message });

// ── Couples ───────────────────────────────────────────────────────────────────

export const createInvite = () => api.post("/sessions/invite");

export const acceptInvite = (inviteCode: string) =>
  api.post("/sessions/invite/accept", { invite_code: inviteCode });
