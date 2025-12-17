import axios from "axios";
import {
  ResearchRequest,
  ResearchSession,
  ProviderReport,
  MasterReport,
  ResearchProgress,
  Provider,
  ModelsResponse,
} from "../types";

const API_BASE_URL = "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const researchApi = {
  // Start a new research session
  startResearch: async (request: ResearchRequest): Promise<ResearchSession> => {
    // Convert frontend providerSettings to backend format
    const providerSettings = request.providerSettings
      ? Object.fromEntries(
          Object.entries(request.providerSettings).map(([key, value]) => [
            key,
            { model: value.model, max_tokens: value.maxTokens },
          ])
        )
      : undefined;

    const payload = {
      topic: request.topic,
      providers: request.providers,
      provider_settings: providerSettings,
    };
    const response = await api.post<any>("/research/start", payload);
    return {
      id: response.data.id,
      topic: response.data.topic,
      status: response.data.status,
      createdAt: response.data.created_at,
      updatedAt: response.data.updated_at,
    };
  },

  // Get research session status
  getResearchStatus: async (sessionId: string): Promise<ResearchProgress> => {
    const response = await api.get<any>(`/research/${sessionId}/status`);
    return {
      sessionId: response.data.session_id,
      overallStatus: response.data.overall_status,
      providers: response.data.providers,
    };
  },

  // Get all provider reports for a session
  getProviderReports: async (sessionId: string): Promise<ProviderReport[]> => {
    const response = await api.get<any[]>(`/research/${sessionId}/reports`);
    return response.data.map((report) => ({
      id: report.id,
      provider: report.provider,
      content: report.content,
      thinking: report.thinking, // LLM reasoning/metadata
      status: report.status,
      errorMessage: report.error_message,
      createdAt: report.created_at,
    }));
  },

  // Generate master report
  generateMasterReport: async (
    sessionId: string,
    mergeProvider: Provider = Provider.OPENAI
  ): Promise<MasterReport> => {
    const response = await api.post<any>(`/research/${sessionId}/merge`, {
      merge_provider: mergeProvider,
    });
    return {
      id: response.data.id,
      content: response.data.content,
      thinking: response.data.thinking, // LLM reasoning/metadata
      createdAt: response.data.created_at,
    };
  },

  // Export report to PDF
  exportToPDF: async (sessionId: string): Promise<Blob> => {
    const response = await api.get(`/research/${sessionId}/export/pdf`, {
      responseType: "blob",
    });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get("/health");
    return response.data;
  },

  // Get available models
  getModels: async (): Promise<ModelsResponse> => {
    const response = await api.get<ModelsResponse>("/models");
    return response.data;
  },
};

export default api;
