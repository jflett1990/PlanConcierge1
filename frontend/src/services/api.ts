// API service for Plan Concierge backend integration

import { IntakeData, QuoteResult, ExplanationResponse, ApiResponse } from '../types';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

class ApiService {
  private async fetchJson<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      const data = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return data;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Submit intake data and get intake ID
  async submitIntake(intakeData: IntakeData): Promise<ApiResponse<{ intake_id: number }>> {
    return this.fetchJson<{ intake_id: number }>('/intake', {
      method: 'POST',
      body: JSON.stringify(intakeData),
    });
  }

  // Get quote preview with plan recommendations
  async getQuotePreview(intakeId: number): Promise<ApiResponse<QuoteResult>> {
    return this.fetchJson<QuoteResult>('/quote/preview', {
      method: 'POST',
      body: JSON.stringify({ intake_id: intakeId }),
    });
  }

  // Search healthcare.gov content
  async searchContent(query: string, limit = 5): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    return this.fetchJson<any>(`/content/search?${params}`);
  }

  // Get AI explanation of insurance term
  async explainTerm(term: string): Promise<ApiResponse<ExplanationResponse>> {
    const params = new URLSearchParams({ term });
    return this.fetchJson<ExplanationResponse>(`/explain/term?${params}`);
  }

  // Get AI explanation of specific plan
  async explainPlan(planId: string, clientId?: number): Promise<ApiResponse<ExplanationResponse>> {
    const params = new URLSearchParams({ plan_id: planId });
    if (clientId) {
      params.append('client_id', clientId.toString());
    }
    return this.fetchJson<ExplanationResponse>(`/explain/plan?${params}`);
  }

  // Get AI comparison of top 3 plans
  async explainTop3(planIds: string[], clientId?: number): Promise<ApiResponse<ExplanationResponse>> {
    const body: any = { plan_ids: planIds };
    if (clientId) {
      body.client_id = clientId;
    }
    
    return this.fetchJson<ExplanationResponse>('/explain/top3', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // Get available plans (for testing/preview)
  async getPlans(filters?: {
    zip_code?: string;
    county?: string;
    year?: number;
    metal?: string;
    issuer?: string;
    limit?: number;
  }): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString());
        }
      });
    }
    
    const url = params.toString() ? `/plans?${params}` : '/plans';
    return this.fetchJson<any>(url);
  }
}

export const apiService = new ApiService();