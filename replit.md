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
- 2025-08-21: Created proper frontend/backend separation structure
- Implemented Python classes in backend/models.py with CRUD helpers for all entities
- Added Flask-RESTX API with initial routes: POST /intake and GET /clients/<id>/artifacts
- Created comprehensive unit tests for models and API endpoints
- Implemented plans API at GET /plans with mock ACA data loading and comprehensive filtering
- Added filters: zip code, county, year, metal level, issuer with location-based filtering
- Implemented quote API at POST /quote/preview with sophisticated APTC calculations
- Added FPL tables, SLCSP premium data, and CSR eligibility determination
- Implemented out-of-pocket risk scoring and plan fit analysis
- Created provider/formulary integration module with mock adapters for network and drug coverage
- Enhanced quote API with provider network and formulary checking, fit score adjustments
- Created healthcare.gov content ingestion worker with search functionality
- Added /content/search endpoint for glossary and content lookup with relevance scoring
- Built LLM tool binding system with OpenAI function calling integration
- Added AI explanation endpoints: /explain/term, /explain/plan, /explain/top3 with structured JSON output
- All unit tests pass: 6 models + 4 API + 11 plans + 9 quote + 11 provider/formulary + 11 hcgov + 14 LLM = 66 total tests
- Server running successfully on port 5000 with API documentation at /api/docs/
- Frontend development started with React components: IntakeWizard (multi-step form), Results (plan table), and ConciergeSidebar (AI explanations)
- API route conflicts resolved - root route now properly serves frontend while maintaining API documentation access
- PDF export functionality implemented with WeasyPrint backend and frontend download button
- Complete PDF generation pipeline: HTML template → CSS styling → PDF file → secure download

## Development Phase
Currently in: Complete Harris County TX Testing
Next: Deployment ready with comprehensive workflow verification

## Testing Results
- Harris County TX fixtures: Family of 2 (ages 35, 33), income $42k
- 5 mock Silver plans with APTC/CSR calculations and fit scoring
- Complete workflow: Intake → Quote Preview → AI Top-3 → PDF Export
- OpenAI integration: Real GPT-4o explanations with structured citations
- All assertions pass: citations present, disclaimers included, valid PDF generation
- API endpoints functional: /api/intake, /api/quote/preview, /api/export/pdf, /api/explain/top3
- PDF export system: Professional templates with WeasyPrint conversion and secure downloads