/**
 * Trinity API client — typed wrapper around the backend REST API.
 *
 * Stores the JWT access token in Expo SecureStore on mobile,
 * and localStorage on web (handled by SecureStore's web fallback).
 */

import axios, { AxiosInstance } from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';

const API_BASE_URL = Constants.expoConfig?.extra?.apiBaseUrl ?? 'http://localhost:8000';
const TOKEN_KEY = 'trinity_access_token';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ChatResponse {
  response: string;
  crisis_detected: boolean;
  session_mode?: string;
}

export interface RelationalModel {
  relationship_id: string;
  active_patterns: Pattern[];
  unmet_needs: Need[];
  insights: Insight[];
  recent_events: Event[];
}

export interface Pattern {
  id: string;
  name: string;
  category: string;
  intensity: number;
  last_observed: string;
}

export interface Need {
  id: string;
  theme: string;
  priority: number;
  partner_tag: 'partner_a' | 'partner_b';
}

export interface Insight {
  id: string;
  framework: string;
  tag: string;
}

export interface SyncResult {
  relationship_id: string;
  signals_processed: number;
  patterns_upserted: number;
  needs_upserted: number;
  events_recorded: number;
  synced_at: string;
  errors: string[];
}

// ── Client ────────────────────────────────────────────────────────────────────

class TrinityAPIClient {
  private http: AxiosInstance;

  constructor() {
    this.http = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30_000,
      headers: { 'Content-Type': 'application/json' },
    });

    // Attach JWT on every request
    this.http.interceptors.request.use(async (config) => {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  async storeToken(token: string): Promise<void> {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
  }

  async clearToken(): Promise<void> {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
  }

  // ── Health ────────────────────────────────────────────────────────────────

  async healthCheck(): Promise<{ status: string }> {
    const { data } = await this.http.get('/health');
    return data;
  }

  // ── Agent A ───────────────────────────────────────────────────────────────

  async agentAChat(message: string, partnerName?: string): Promise<ChatResponse> {
    const { data } = await this.http.post('/v1/agent-a/chat', {
      message,
      partner_name: partnerName,
    });
    return data;
  }

  async agentAHistory(limit = 20): Promise<{ exchanges: unknown[]; total: number }> {
    const { data } = await this.http.get('/v1/agent-a/history', { params: { limit } });
    return data;
  }

  // ── Agent B ───────────────────────────────────────────────────────────────

  async agentBChat(message: string, partnerName?: string): Promise<ChatResponse> {
    const { data } = await this.http.post('/v1/agent-b/chat', {
      message,
      partner_name: partnerName,
    });
    return data;
  }

  async agentBHistory(limit = 20): Promise<{ exchanges: unknown[]; total: number }> {
    const { data } = await this.http.get('/v1/agent-b/history', { params: { limit } });
    return data;
  }

  // ── Agent R ───────────────────────────────────────────────────────────────

  async agentRChat(message: string, partnerName?: string): Promise<ChatResponse> {
    const { data } = await this.http.post('/v1/agent-r/chat', {
      message,
      partner_name: partnerName,
    });
    return data;
  }

  async agentRJoint(
    partnerAMessage?: string,
    partnerBMessage?: string,
  ): Promise<ChatResponse> {
    const { data } = await this.http.post('/v1/agent-r/joint', {
      partner_a_message: partnerAMessage,
      partner_b_message: partnerBMessage,
    });
    return data;
  }

  // ── Relationships ─────────────────────────────────────────────────────────

  async createRelationship(
    partnerAId: string,
    partnerBId: string,
    partnerAName?: string,
    partnerBName?: string,
  ): Promise<{ relationship_id: string; status: string }> {
    const { data } = await this.http.post('/v1/relationships', {
      partner_a_id: partnerAId,
      partner_b_id: partnerBId,
      partner_a_name: partnerAName,
      partner_b_name: partnerBName,
    });
    return data;
  }

  async getRelationalModel(relationshipId: string): Promise<RelationalModel> {
    const { data } = await this.http.get(`/v1/relationships/${relationshipId}/model`);
    return data;
  }

  async triggerInsightSync(relationshipId: string): Promise<SyncResult> {
    const { data } = await this.http.post(`/v1/relationships/${relationshipId}/sync`);
    return data;
  }
}

export const trinityAPI = new TrinityAPIClient();
