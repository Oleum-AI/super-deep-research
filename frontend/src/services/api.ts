import axios from 'axios';
import { 
  ResearchRequest, 
  ResearchSession, 
  ProviderReport, 
  MasterReport, 
  ResearchProgress,
  Provider 
} from '../types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const researchApi = {
  // Start a new research session
  startResearch: async (request: ResearchRequest): Promise<ResearchSession> => {
    const response = await api.post<ResearchSession>('/research/start', request);
    return response.data;
  },

  // Get research session status
  getResearchStatus: async (sessionId: string): Promise<ResearchProgress> => {
    const response = await api.get<ResearchProgress>(`/research/${sessionId}/status`);
    return response.data;
  },

  // Get all provider reports for a session
  getProviderReports: async (sessionId: string): Promise<ProviderReport[]> => {
    const response = await api.get<ProviderReport[]>(`/research/${sessionId}/reports`);
    return response.data;
  },

  // Generate master report
  generateMasterReport: async (
    sessionId: string, 
    mergeProvider: Provider = Provider.OPENAI
  ): Promise<MasterReport> => {
    const response = await api.post<MasterReport>(
      `/research/${sessionId}/merge`,
      { merge_provider: mergeProvider }
    );
    return response.data;
  },

  // Export report to PDF
  exportToPDF: async (sessionId: string): Promise<Blob> => {
    const response = await api.get(`/research/${sessionId}/export/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
