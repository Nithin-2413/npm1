// API Service for QA Automation Backend
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

export interface StartRunRequest {
  flow_id?: string;
  variables?: Record<string, any>;
  natural_language_input?: string;
  test_env_id?: string;
}

export interface RunStatusResponse {
  run_id: string;
  flow_id?: string;
  flow_name?: string;
  status: string;
  started_at: string;
  finished_at?: string;
  variables_used?: Record<string, any>;
  error_summary?: string;
  progress?: {
    current_step: number;
    total_steps: number;
    percentage: number;
  };
}

export interface FlowSummary {
  id: string;
  name: string;
  category: string;
  description: string;
  required_params: string[];
  optional_params: string[];
  estimated_duration_seconds: number;
}

export interface FlowDetail extends FlowSummary {
  defaults: Record<string, any>;
  steps: Array<{
    step: number;
    description: string;
    action: string;
    [key: string]: any;
  }>;
}

export interface Secret {
  id: string;
  env_id: string;
  test_env: string;
  release_branch?: string;
  url: string;
  username?: string;
  created_at: string;
}

export interface TestRun {
  run_id: string;
  flow_id: string;
  flow_name: string;
  status: string;
  started_at: string;
  finished_at?: string;
  duration_seconds?: number;
  error_summary?: string;
  test_env_id?: string;
}

export interface ReportSummary {
  period_days: number;
  from_date: string;
  to_date: string;
  overall: {
    total_runs: number;
    passed: number;
    failed: number;
    cancelled: number;
    pass_rate: number;
  };
  flows: Array<{
    flow_id: string;
    flow_name: string;
    total_runs: number;
    passed: number;
    failed: number;
    pass_rate: number;
    average_duration_seconds: number;
    is_flaky: boolean;
  }>;
  flaky_flows: Array<any>;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_URL;
  }

  // Test Runs
  async startRun(request: StartRunRequest): Promise<{ run_id: string; status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/runs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start test run');
    }
    
    return response.json();
  }

  async listRuns(options?: { status?: string; flow_id?: string; limit?: number; skip?: number }): Promise<{ runs: TestRun[]; total: number }> {
    const params = new URLSearchParams();
    if (options?.status) params.append('status', options.status);
    if (options?.flow_id) params.append('flow_id', options.flow_id);
    if (options?.limit) params.append('limit', String(options.limit));
    if (options?.skip) params.append('skip', String(options.skip));
    
    const response = await fetch(`${this.baseUrl}/runs?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch runs');
    }
    
    return response.json();
  }

  async getRunStatus(runId: string): Promise<RunStatusResponse> {
    const response = await fetch(`${this.baseUrl}/runs/${runId}/status`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch run status');
    }
    
    return response.json();
  }

  async getRunLogs(runId: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/runs/${runId}/logs`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch run logs');
    }
    
    return response.json();
  }

  async cancelRun(runId: string): Promise<{ run_id: string; status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/runs/${runId}/cancel`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('Failed to cancel run');
    }
    
    return response.json();
  }

  // Server-Sent Events for real-time logs
  streamRunLogs(runId: string, onMessage: (event: any) => void, onError?: (error: Error) => void): EventSource {
    const eventSource = new EventSource(`${this.baseUrl}/runs/${runId}/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      if (onError) {
        onError(new Error('Stream connection error'));
      }
      eventSource.close();
    };
    
    return eventSource;
  }

  // Flows
  async listFlows(): Promise<FlowSummary[]> {
    const response = await fetch(`${this.baseUrl}/flows`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch flows');
    }
    
    return response.json();
  }

  async getFlow(flowId: string): Promise<FlowDetail> {
    const response = await fetch(`${this.baseUrl}/flows/${flowId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch flow details');
    }
    
    return response.json();
  }

  async createFlow(flow: Partial<FlowDetail>): Promise<{ flow_id: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/flows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(flow),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create flow');
    }
    
    return response.json();
  }

  async updateFlow(flowId: string, flow: Partial<FlowDetail>): Promise<{ flow_id: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/flows/${flowId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(flow),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update flow');
    }
    
    return response.json();
  }

  async deleteFlow(flowId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/flows/${flowId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete flow');
    }
  }

  // Secrets (Test Environments)
  async createSecret(secret: { test_env: string; release_branch?: string; url: string; username?: string; password?: string }): Promise<Secret> {
    const response = await fetch(`${this.baseUrl}/secrets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(secret),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create secret');
    }
    
    return response.json();
  }

  async listSecrets(): Promise<Secret[]> {
    const response = await fetch(`${this.baseUrl}/secrets`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch secrets');
    }
    
    return response.json();
  }

  async getSecret(id: string): Promise<Secret> {
    const response = await fetch(`${this.baseUrl}/secrets/${id}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch secret');
    }
    
    return response.json();
  }

  async updateSecret(id: string, secret: { test_env: string; release_branch?: string; url: string; username?: string; password?: string }): Promise<Secret> {
    const response = await fetch(`${this.baseUrl}/secrets/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(secret),
    });
    
    if (!response.ok) {
      throw new Error('Failed to update secret');
    }
    
    return response.json();
  }

  async deleteSecret(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/secrets/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete secret');
    }
  }

  // Reports
  async getReportsSummary(days: number = 7): Promise<ReportSummary> {
    const response = await fetch(`${this.baseUrl}/reports/summary?days=${days}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch reports summary');
    }
    
    return response.json();
  }

  async getRunHistory(options?: { limit?: number; offset?: number; flow_id?: string; status?: string; from_date?: string; to_date?: string }): Promise<{ total: number; runs: TestRun[] }> {
    const params = new URLSearchParams();
    if (options?.limit) params.append('limit', String(options.limit));
    if (options?.offset) params.append('offset', String(options.offset));
    if (options?.flow_id) params.append('flow_id', options.flow_id);
    if (options?.status) params.append('status', options.status);
    if (options?.from_date) params.append('from_date', options.from_date);
    if (options?.to_date) params.append('to_date', options.to_date);
    
    const response = await fetch(`${this.baseUrl}/reports/runs?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch run history');
    }
    
    return response.json();
  }

  async exportRun(runId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/reports/runs/${runId}/export`);
    
    if (!response.ok) {
      throw new Error('Failed to export run');
    }
    
    return response.json();
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string; services: Record<string, { status: string; message: string }> }> {
    const response = await fetch(`${this.baseUrl}/health`);
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    
    return response.json();
  }
}

export const apiService = new ApiService();
