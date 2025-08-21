# Plan Concierge - Agent-First ACA/Medicare Plan Comparison Platform

## Project Overview
A lightweight SaaS tool for insurance agents that simplifies ACA and Medicare plan comparison. The system pulls official plan data, checks doctors/prescriptions, explains tradeoffs in plain English using AI, and exports client-ready PDFs.

## Project Architecture

### Technology Stack
- **Frontend**: React with Vite + TypeScript
- **Backend**: Flask (Python) with Flask-RESTX for API documentation
- **Storage**: In-memory Python dicts/lists for MVP (designed for easy migration to PostgreSQL)
- **Cache**: Simple dict cache (upgrade to Redis later)
- **LLM Layer**: OpenAI GPT with custom tool bindings
- **PDF Export**: WeasyPrint (HTML → PDF)

### Project Structure
```
plan-concierge/
├── frontend/          # React app (Vite + TypeScript)
├── backend/           # Flask API with Flask-RESTX
├── shared/            # TypeScript types + JSON schemas
├── package.json       # Frontend dependencies
├── requirements.txt   # Backend dependencies
└── README.md         # Development instructions
```

### Data Model (In-Memory MVP)
- Agent: {id, name, email, brand_name, logo_url}
- Client: {id, agent_id, first_name, last_name, email, dob, zip, county, state}
- Intake: {id, client_id, plan_year, household_size, ages[], income, doctors[], prescriptions[], prefs{}}
- Plan: {id, plan_year, issuer, name, metal, premium_full, deductible, moop, csr_flag}
- QuoteResult: {id, intake_id, aptc, csr_level}
- PlanFit: {id, quote_result_id, plan_id, net_premium, doctor_hits[], rx_hits[], rationale{}, fit_score}
- Artifact: {id, client_id, type, payload/url, created_at}

## API Surface (MVP)
- POST /intake → create intake
- GET /plans → list normalized ACA plans
- POST /quote/preview → compute APTC + CSR + fit scores
- POST /explain/top3 → GPT summary
- POST /export/pdf → generate/download PDF
- POST /soa → generate/store SOA stub
- GET /clients/:id/artifacts → list artifacts

## User Preferences
- Follow ordered, step-by-step instructions
- Wait for confirmation before proceeding to next phase
- Focus on MVP functionality with clean upgrade paths

## Recent Changes
- 2024-12-21: Initial project structure created
- Project configured for Replit-compatible tech stack
- In-memory storage designed for easy PostgreSQL migration

## Development Phase
Currently in: Initial Setup Phase
Next: Awaiting specific feature implementation instructions