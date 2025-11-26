const API_BASE_URL = "http://localhost:8000";

export interface IndividualReport {
  id: number;
  provider: string;
  report_text: string;
}

export interface MasterReport {
  id: number;
  report_text: string;
}

export enum JobStatus {
  PENDING = "PENDING",
  PROCESSING = "PROCESSING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
}

export interface ResearchJob {
  id: number;
  query: string;
  status: JobStatus;
  individual_reports: IndividualReport[];
  master_report?: MasterReport;
}

export async function createResearchJob(query: string): Promise<ResearchJob> {
  const response = await fetch(`${API_BASE_URL}/api/research`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    throw new Error("Failed to create research job");
  }
  return response.json();
}

export async function getResearchJob(jobId: number): Promise<ResearchJob> {
  const response = await fetch(`${API_BASE_URL}/api/research/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to get research job");
  }
  return response.json();
}

export async function synthesizeReports(jobId: number, provider: string): Promise<MasterReport> {
  const response = await fetch(`${API_BASE_URL}/api/synthesize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_id: jobId, provider }),
  });
  if (!response.ok) {
    throw new Error("Failed to synthesize reports");
  }
  return response.json();
}
