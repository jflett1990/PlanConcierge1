# Plan Concierge

Agent-first ACA/Medicare plan comparison platform with AI-powered explanations and PDF export capabilities.

## Project Structure

```
plan-concierge/
├── frontend/          # React app (Vite + TypeScript)
│   ├── src/           # React components and logic
│   ├── package.json   # Frontend dependencies
│   └── vite.config.ts # Vite configuration
├── backend/           # Flask API with Flask-RESTX
│   ├── app.py         # Flask app initialization
│   ├── main.py        # Entry point
│   ├── models.py      # Data models
│   └── requirements.txt # Backend dependencies
├── shared/            # TypeScript types + JSON schemas
│   ├── types.ts       # Shared TypeScript interfaces
│   └── schemas.json   # JSON validation schemas
└── README.md          # This file
```

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (for production)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The Flask API will run on http://localhost:5000

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The React app will run on http://localhost:3000

### API Documentation
When the backend is running, visit http://localhost:5000/api/docs/ for interactive API documentation.

## Features

- **Smart Intake Forms**: Collects client information, doctors, prescriptions, and preferences
- **Plan Lookup & Comparison**: Integrates with official plan data sources
- **AI-Powered Explanations**: Uses OpenAI to explain plan differences in plain English
- **PDF Export**: Generates client-ready comparison documents
- **Compliance Tracking**: Maintains audit trails and SOA documentation

## Data Storage

**MVP**: In-memory storage using Python dictionaries for rapid development
**Production**: Designed for easy migration to PostgreSQL

## Environment Variables

- `OPENAI_API_KEY`: Required for AI-powered explanations
- `DATABASE_URL`: PostgreSQL connection string (production)
- `SESSION_SECRET`: Flask session encryption key

## Development Guidelines

1. **Frontend**: All React components should use TypeScript and reference shared types
2. **Backend**: Follow Flask-RESTX patterns for API documentation
3. **Shared**: Update both `types.ts` and `schemas.json` when adding new data structures
4. **Testing**: Use authentic data sources; avoid mock data in production paths

## API Endpoints

### Core APIs (Implemented)
- `POST /intake` - Create intake form
- `GET /clients/{id}/artifacts` - List client documents
- `GET /plans` - List available plans with filters (zip, county, year, metal, issuer)
- `POST /quote/preview` - Generate quote with APTC/CSR calculations and plan pricing

### Planned APIs
- `POST /explain/top3` - AI explanation of top plan options
- `POST /export/pdf` - Generate PDF comparison
- `POST /soa` - Create Statement of Advice stub

## Plans API Usage

```bash
# Get all plans
GET /plans

# Filter by location
GET /plans?zip=94102
GET /plans?county=San Francisco

# Filter by plan attributes  
GET /plans?year=2024
GET /plans?metal=Silver
GET /plans?issuer=Blue Shield

# Combine filters
GET /plans?zip=94102&metal=Bronze&year=2024
```

## Quote API Usage

```bash
# Generate quote with APTC calculations
POST /quote/preview
{
  "intake_id": 1
}

# Returns:
{
  "success": true,
  "data": {
    "quote_result_id": 1,
    "aptc": 295.56,
    "csr_level": "70%",
    "slcsp_premium": 720.56,
    "income_fpl_ratio": 2.94,
    "plans": [
      {
        "plan_id": "11512CA0040003",
        "issuer": "Blue Shield of California",
        "name": "Blue Shield Gold 80 HMO",
        "metal": "Gold",
        "premium_full": 489.80,
        "net_premium": 194.24,
        "deductible": 1500,
        "moop": 8700,
        "oop_risk_score": 45.23,
        "csr_flag": false
      }
    ]
  }
}
```

## Testing

```bash
# Run all tests
cd backend && python -m unittest discover tests/

# Run specific test files
cd backend && python -m unittest tests.test_models -v
cd backend && python -m unittest tests.test_plans_api -v  
cd backend && python -m unittest tests.test_quote_api -v

# Current test coverage:
# - Models: 6 tests covering CRUD operations
# - API endpoints: 4 tests covering intake and artifacts
# - Plans API: 11 tests covering filtering and data loading  
# - Quote API: 9 tests covering APTC calculations and quote generation
# Total: 30 tests passing
```