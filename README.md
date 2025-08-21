# Plan Concierge - Agent-First ACA/Medicare Plan Comparison Platform

A sophisticated AI-powered ACA/Medicare plan comparison platform designed to simplify complex insurance selections through intelligent technology and comprehensive data analysis.

## 🎯 Project Overview

Plan Concierge is a lightweight SaaS tool for insurance agents that streamlines the entire plan recommendation process:

- **Smart Intake Forms**: Capture client needs with guided workflows
- **Automated Plan Lookup**: Pull and compare official ACA/Medicare plan data
- **AI-Powered Explanations**: OpenAI GPT-4o integration with "James's Plan Concierge" persona
- **Compliance-Ready PDF Exports**: Professional reports with required citations and disclaimers
- **Automated Compliance Tracking**: Real-time monitoring of regulatory requirements

## 🚀 Features

### Core Functionality
- **Multi-step Intake Wizard**: Guided data collection for clients
- **Plan Comparison Engine**: Advanced filtering and fit scoring
- **Provider Network Integration**: Doctor and prescription checking
- **AI Explanations**: Plain English plan summaries and recommendations
- **PDF Export System**: Professional client-ready documents

### Compliance Dashboard
- **Real-time Compliance Monitoring**: Track 8+ regulatory requirements
- **Automated Rule Checking**: Documentation and deadline monitoring
- **Interactive Dashboard**: Professional interface with scoring metrics
- **Alert System**: Priority-based notification system

### Technical Features
- **OpenAI Integration**: GPT-4o with structured function calling
- **Healthcare.gov Content**: Integrated glossary and educational content
- **APTC/CSR Calculations**: Accurate tax credit and cost-sharing computations
- **Professional UI**: Bootstrap-based responsive design

## 🏗️ Architecture

### Technology Stack
- **Frontend**: React with Vite + TypeScript
- **Backend**: Flask (Python) with Flask-RESTX for API documentation
- **Storage**: In-memory Python dicts/lists for MVP (PostgreSQL-ready)
- **Cache**: Simple dict cache (Redis upgrade path)
- **LLM Layer**: OpenAI GPT with custom tool bindings
- **PDF Export**: WeasyPrint (HTML → PDF)

### Project Structure
```
plan-concierge/
├── frontend/          # React app (Vite + TypeScript)
├── backend/           # Flask API with Flask-RESTX
├── shared/            # TypeScript types + JSON schemas
├── package.json       # Frontend dependencies
├── pyproject.toml     # Backend dependencies
└── README.md         # This file
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- OpenAI API Key

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
PLAN_YEAR=2025
DATABASE_URL=postgresql://... (optional for PostgreSQL)
```

### Quick Start
1. **Clone the repository**
   ```bash
   git clone https://github.com/jflett1990/plan-concierge.git
   cd plan-concierge
   ```

2. **Install dependencies**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies
   npm install
   ```

3. **Set environment variables**
   ```bash
   export OPENAI_API_KEY="your_key_here"
   export PLAN_YEAR="2025"
   ```

4. **Start the development server**
   ```bash
   # Start Flask backend
   gunicorn --bind 0.0.0.0:5000 --reload main:app
   
   # In another terminal, start frontend (if using React dev server)
   npm run dev
   ```

5. **Access the application**
   - Main app: http://localhost:5000
   - API documentation: http://localhost:5000/api/docs/
   - Frontend demo: http://localhost:5000/frontend/src/demo.html

## 📊 API Documentation

### Core Endpoints
- `POST /api/intake` - Create client intake
- `GET /api/plans` - List available plans with filtering
- `POST /api/quote/preview` - Generate APTC/CSR quotes
- `POST /api/explain/top3` - AI-powered plan comparisons
- `POST /api/export/pdf` - Generate client PDF reports

### Compliance Endpoints
- `GET /api/compliance/dashboard` - Compliance summary
- `GET /api/compliance/rules` - List regulatory rules
- `POST /api/compliance/checks/run` - Execute compliance checks
- `GET /api/compliance/alerts` - Active compliance alerts

Visit `/api/docs/` for interactive API documentation.

## 🧪 Testing

### Run All Tests
```bash
cd backend
python -m pytest test_*.py -v
```

### Test Coverage
- **Models**: 6 tests (Agent, Client, Intake, Plan, etc.)
- **API Endpoints**: 4 tests (intake, artifacts, etc.)
- **Plans System**: 11 tests (filtering, location, etc.)
- **Quote Engine**: 9 tests (APTC, CSR, fit scoring)
- **Provider Integration**: 11 tests (network, formulary)
- **Healthcare.gov Content**: 11 tests (search, relevance)
- **LLM Tools**: 14 tests (OpenAI integration, explanations)
- **Compliance System**: 15+ tests (rules, checks, dashboard)

**Total: 80+ comprehensive tests**

## 🎯 Demo Workflows

### Harris County, TX Example
Test the complete workflow with realistic data:
1. Family of 2 (ages 35, 33), income $42k
2. 5 mock Silver plans with APTC/CSR calculations
3. Complete workflow: Intake → Quote → AI Explanations → PDF Export

### Compliance Tracking
Monitor regulatory compliance in real-time:
1. 8 implemented compliance rules
2. Automated checking for documentation requirements
3. Deadline monitoring and alert system
4. Professional dashboard interface

## 🚀 Deployment

### Replit Deployment
This project is optimized for Replit deployment:
1. Push to GitHub
2. Import to Replit
3. Set environment variables
4. Deploy with Replit Deployments

### Manual Deployment
1. **Set up production environment**
2. **Configure database** (PostgreSQL recommended)
3. **Set environment variables**
4. **Deploy with gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## 📋 Development Status

### ✅ Completed Features
- Complete backend API with Flask-RESTX
- Frontend demo with React components
- OpenAI GPT-4o integration with structured citations
- PDF export system with professional templates
- Compliance tracking dashboard with 8 regulatory rules
- Comprehensive test suite (80+ tests)
- API documentation and demo workflows

### 🔄 Next Steps
- PostgreSQL database migration
- Production deployment optimization
- Enhanced compliance rule coverage
- Advanced analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For support and questions:
1. Check the API documentation at `/api/docs/`
2. Review the test files for usage examples
3. Check the compliance dashboard for regulatory guidance

---

**Plan Concierge** - Simplifying ACA/Medicare plan selection through intelligent automation.