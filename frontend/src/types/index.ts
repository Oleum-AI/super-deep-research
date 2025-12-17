export interface ProviderSettings {
  model: string; // Selected model name for this provider
  maxTokens: number;
}

export interface ResearchRequest {
  topic: string;
  providers: Provider[];
  providerSettings?: Record<string, ProviderSettings>;
}

export interface ResearchSession {
  id: string;
  topic: string;
  status: ResearchStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ProviderReport {
  id: number;
  provider: Provider;
  content?: string;
  thinking?: string; // LLM reasoning/metadata shown separately
  status: ResearchStatus;
  errorMessage?: string;
  createdAt: string;
}

export interface MasterReport {
  id: number;
  content: string;
  thinking?: string; // LLM reasoning/metadata shown separately
  createdAt: string;
}

export interface ResearchProgress {
  sessionId: string;
  overallStatus: ResearchStatus;
  providers: Record<
    string,
    {
      status: ResearchStatus;
      hasContent: boolean;
      error?: string;
    }
  >;
}

export interface WebSocketMessage {
  type: string;
  sessionId: string;
  provider?: string;
  status?: string;
  content?: string;
  error?: string;
  progress?: number;
}

export enum Provider {
  OPENAI = "openai",
  ANTHROPIC = "anthropic",
  XAI = "xai",
}

export enum ResearchStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  FAILED = "failed",
  MERGED = "merged",
}

// Model configuration types
export interface ModelConfig {
  name: string;
  display_name: string;
  description: string;
  max_output_tokens: number;
  max_input_tokens: number;
  modalities: string[];
  is_default: boolean;
}

export interface ProviderConfig {
  name: string;
  description: string;
  color: string;
}

export interface ProviderModels {
  provider: ProviderConfig;
  models: ModelConfig[];
}

export type ModelsResponse = Record<string, ProviderModels>;
