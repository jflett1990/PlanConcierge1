// Core domain types for Plan Concierge

export interface Agent {
  id: number;
  name: string;
  email: string;
  brand_name: string;
  logo_url?: string;
}

export interface Client {
  id: number;
  agent_id: number;
  first_name: string;
  last_name: string;
  email: string;
  dob: string; // ISO date string
  zip: string;
  county: string;
  state: string;
}

export interface Doctor {
  npi: string;
  name: string;
  specialty: string;
}

export interface Prescription {
  rxcui: string;
  name: string;
  dosage: string;
  frequency: string;
}

export interface Preferences {
  max_premium?: number;
  max_deductible?: number;
  important_benefits: string[];
  pharmacy_preference?: string;
}

export interface Intake {
  id: number;
  client_id: number;
  plan_year: number;
  household_size: number;
  ages: number[];
  income: number;
  doctors: Doctor[];
  prescriptions: Prescription[];
  prefs: Preferences;
}

export interface Plan {
  id: string;
  plan_year: number;
  issuer: string;
  name: string;
  metal: 'Bronze' | 'Silver' | 'Gold' | 'Platinum' | 'Catastrophic';
  premium_full: number;
  deductible: number;
  moop: number; // Maximum Out of Pocket
  csr_flag: boolean;
}

export interface QuoteResult {
  id: number;
  intake_id: number;
  aptc: number; // Advanced Premium Tax Credit
  csr_level: string;
}

export interface PlanFit {
  id: number;
  quote_result_id: number;
  plan_id: string;
  net_premium: number;
  doctor_hits: string[];
  rx_hits: string[];
  rationale: {
    benefits_match: string;
    cost_analysis: string;
    trade_offs: string;
  };
  fit_score: number;
}

export interface Artifact {
  id: number;
  client_id: number;
  type: 'pdf_comparison' | 'soa_stub' | 'intake_summary';
  payload?: any;
  url?: string;
  created_at: string; // ISO date string
}

// API Request/Response types
export interface CreateClientRequest {
  agent_id: number;
  first_name: string;
  last_name: string;
  email: string;
  dob: string;
  zip: string;
  county: string;
  state: string;
}

export interface CreateIntakeRequest {
  client_id: number;
  plan_year: number;
  household_size: number;
  ages: number[];
  income: number;
  doctors: Doctor[];
  prescriptions: Prescription[];
  prefs: Preferences;
}

export interface QuotePreviewRequest {
  intake_id: number;
}

export interface ExplainTop3Request {
  quote_result_id: number;
  plan_ids: string[];
}

export interface ExportPDFRequest {
  quote_result_id: number;
  plan_ids: string[];
}

export interface SOARequest {
  client_id: number;
}

// API Response types
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}