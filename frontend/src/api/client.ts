/**
 * API client for backend communication
 */
import axios from 'axios';
import type {
  ResearchRequest,
  ResearchSessionResponse,
  StatusResponse,
  ResearchSession,
  SynthesisRequest,
  HealthResponse,
} from '../types';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  /**
   * Check API health status
   */
  health: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  },

  /**
   * Start a new research session
   */
  startResearch: async (request: ResearchRequest): Promise<ResearchSessionResponse> => {
    const response = await apiClient.post<ResearchSessionResponse>('/research/start', request);
    return response.data;
  },

  /**
   * Get research session status
   */
  getStatus: async (sessionId: string): Promise<StatusResponse> => {
    const response = await apiClient.get<StatusResponse>(`/research/${sessionId}/status`);
    return response.data;
  },

  /**
   * Get all reports for a session
   */
  getReports: async (sessionId: string): Promise<ResearchSession> => {
    const response = await apiClient.get<ResearchSession>(`/research/${sessionId}/reports`);
    return response.data;
  },

  /**
   * Synthesize reports into master report
   */
  synthesizeReports: async (
    sessionId: string,
    request: SynthesisRequest
  ): Promise<{ session_id: string; master_report: string }> => {
    const response = await apiClient.post(`/research/${sessionId}/synthesize`, request);
    return response.data;
  },

  /**
   * Get research history
   */
  getHistory: async (limit = 50): Promise<{ sessions: ResearchSession[] }> => {
    const response = await apiClient.get('/research/history', { params: { limit } });
    return response.data;
  },
};

export default api;

