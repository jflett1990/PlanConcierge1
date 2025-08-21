// Core data types for Plan Concierge frontend

export interface IntakeData {
  // Household information
  household_size: number;
  ages: number[];
  
  // Financial information
  income: number;
  
  // Location information
  zip: string;
  county?: string;
  state?: string;
  
  // Healthcare providers
  doctors: Doctor[];
  
  // Prescriptions
  prescriptions: Prescription[];
  
  // Preferences
  preferences: Preferences;
}

export interface Doctor {
  npi: string;
  name: string;
  specialty?: string;
  practice_name?: string;
}

export interface Prescription {
  rxcui: string;
  name: string;
  dosage: string;
  frequency: string;
}

export interface Preferences {
  prefer_low_premium: boolean;
  prefer_low_deductible: boolean;
  prefer_broad_network: boolean;
  prefer_brand_drugs: boolean;
  important_features: string[];
}

export interface Plan {
  id: string;
  plan_year: number;
  issuer: string;
  name: string;
  metal: string;
  premium_full: number;
  deductible: number;
  moop: number;
  csr_flag: boolean;
}

export interface QuoteResult {
  aptc: number;
  csr_level: string;
  plan_fits: PlanFit[];
}

export interface PlanFit {
  plan: Plan;
  net_premium: number;
  fit_score: number;
  rationale: {
    cost_score: number;
    network_score: number;
    rx_score: number;
    preference_score: number;
    total_oop_risk: number;
  };
  provider_summary?: {
    in_network_count: number;
    total_count: number;
    coverage_rate: number;
  };
  rx_summary?: {
    covered_count: number;
    total_count: number;
    coverage_rate: number;
    avg_tier: number;
  };
}

export interface ExplanationResponse {
  title: string;
  sections: {
    heading: string;
    body: string;
  }[];
  citations: {
    title: string;
    url: string;
  }[];
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}