export interface ResearchRequest {
  topic: string;
  providers: Provider[];
  maxTokens?: number;
  includeWebSearch?: boolean;
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
  status: ResearchStatus;
  errorMessage?: string;
  createdAt: string;
}

export interface MasterReport {
  id: number;
  content: string;
  createdAt: string;
}

export interface ResearchProgress {
  sessionId: string;
  overallStatus: ResearchStatus;
  providers: Record<string, {
    status: ResearchStatus;
    hasContent: boolean;
    error?: string;
  }>;
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
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  XAI = 'xai',
}

export enum ResearchStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  MERGED = 'merged',
}
