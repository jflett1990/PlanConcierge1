import os
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from models import (
    Client, Intake, Artifact, Doctor, Prescription, Preferences
)
from api.plans import create_plans_api
from api.quote import create_quote_api

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Initialize Flask-RESTX API
api = Api(app, 
          version='1.0', 
          title='Plan Concierge API',
          description='ACA/Medicare Plan Comparison API',
          doc='/api/docs/')

# Define API models for documentation
doctor_model = api.model('Doctor', {
    'npi': fields.String(required=True, description='NPI number'),
    'name': fields.String(required=True, description='Doctor name'),
    'specialty': fields.String(required=True, description='Medical specialty')
})

prescription_model = api.model('Prescription', {
    'rxcui': fields.String(required=True, description='RxCUI code'),
    'name': fields.String(required=True, description='Prescription name'),
    'dosage': fields.String(required=True, description='Dosage'),
    'frequency': fields.String(required=True, description='Frequency')
})

preferences_model = api.model('Preferences', {
    'max_premium': fields.Float(description='Maximum premium'),
    'max_deductible': fields.Float(description='Maximum deductible'),
    'important_benefits': fields.List(fields.String, description='Important benefits'),
    'pharmacy_preference': fields.String(description='Preferred pharmacy')
})

intake_model = api.model('Intake', {
    'client_id': fields.Integer(required=True, description='Client ID'),
    'plan_year': fields.Integer(required=True, description='Plan year'),
    'household_size': fields.Integer(required=True, description='Household size'),
    'ages': fields.List(fields.Integer, required=True, description='Ages of household members'),
    'income': fields.Float(required=True, description='Annual income'),
    'doctors': fields.List(fields.Nested(doctor_model), description='Current doctors'),
    'prescriptions': fields.List(fields.Nested(prescription_model), description='Current prescriptions'),
    'prefs': fields.Nested(preferences_model, description='Preferences')
})

# Routes
@api.route('/intake')
class IntakeResource(Resource):
    @api.expect(intake_model)
    @api.doc('create_intake')
    def post(self):
        """Create a new intake form"""
        try:
            data = request.get_json()
            
            # Parse doctors
            doctors = [Doctor(**doc) for doc in data.get('doctors', [])]
            
            # Parse prescriptions
            prescriptions = [Prescription(**rx) for rx in data.get('prescriptions', [])]
            
            # Parse preferences
            prefs_data = data.get('prefs', {})
            prefs = Preferences(**prefs_data)
            
            # Create intake
            intake = Intake.create(
                client_id=data['client_id'],
                plan_year=data['plan_year'],
                household_size=data['household_size'],
                ages=data['ages'],
                income=data['income'],
                doctors=doctors,
                prescriptions=prescriptions,
                prefs=prefs
            )
            
            return {
                'success': True,
                'data': {
                    'id': intake.id,
                    'client_id': intake.client_id,
                    'plan_year': intake.plan_year,
                    'household_size': intake.household_size,
                    'ages': intake.ages,
                    'income': intake.income
                }
            }, 201
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 400

@api.route('/clients/<int:client_id>/artifacts')
class ClientArtifactsResource(Resource):
    @api.doc('list_client_artifacts')
    def get(self, client_id):
        """Get all artifacts for a client"""
        try:
            # Verify client exists
            client = Client.get(client_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Client not found'
                }, 404
            
            # Get client artifacts
            artifacts = Artifact.list_by_client(client_id)
            
            artifacts_data = []
            for artifact in artifacts:
                artifacts_data.append({
                    'id': artifact.id,
                    'type': artifact.type,
                    'url': artifact.url,
                    'created_at': artifact.created_at
                })
            
            return {
                'success': True,
                'data': artifacts_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

# Add API status route 
@app.route('/status')
def status():
    from flask import jsonify
    return jsonify({
        "message": "Plan Concierge API",
        "version": "1.0.0",
        "endpoints": {
            "plans": "/plans",
            "quote": "/quote/preview", 
            "intake": "/intake",
            "content_search": "/content/search?q=premium",
            "explain_term": "/explain/term?term=deductible",
            "explain_plan": "/explain/plan?plan_id=11512CA0040001",
            "explain_top3": "/explain/top3",
            "api_docs": "/api/docs/"
        },
        "status": "running"
    })

# Content search endpoint
@api.route('/content/search')
class ContentSearchResource(Resource):
    @api.doc('search_content')
    @api.param('q', 'Search query', required=True)
    @api.param('limit', 'Maximum results (default: 10)', type='integer', default=10)
    def get(self):
        """Search healthcare.gov content and glossary"""
        try:
            from worker.hcgov_ingest import get_ingestor
            
            query = request.args.get('q', '').strip()
            if not query:
                return {
                    'success': False,
                    'error': 'Query parameter "q" is required'
                }, 400
            
            limit = request.args.get('limit', 10)
            try:
                limit = int(limit)
                if limit <= 0 or limit > 100:
                    limit = 10
            except (ValueError, TypeError):
                limit = 10
            
            # Get ingestor and search content
            ingestor = get_ingestor()
            results = ingestor.search_content(query, limit)
            
            # Format results for response
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'text': result.get('match_snippet', result.get('text', '')),
                    'type': result.get('type', ''),
                    'source': result.get('source', ''),
                    'relevance_score': result.get('relevance_score', 0)
                })
            
            # Get content stats
            stats = ingestor.get_content_stats()
            
            return {
                'success': True,
                'data': {
                    'query': query,
                    'results': formatted_results,
                    'total_results': len(formatted_results),
                    'stats': stats
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

# LLM explanation endpoints
@api.route('/explain/term')
class ExplainTermResource(Resource):
    @api.doc('explain_term')
    @api.param('term', 'Insurance term to explain', required=True)
    def get(self):
        """Get AI explanation of insurance term using healthcare.gov sources"""
        try:
            from llm.tools import define_term
            
            term = request.args.get('term', '').strip()
            if not term:
                return {
                    'success': False,
                    'error': 'Term parameter is required'
                }, 400
            
            result = define_term(term)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['response'],
                    'tool_calls_made': result.get('tool_calls_made', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }, 500
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/explain/plan')
class ExplainPlanResource(Resource):
    @api.doc('explain_plan')
    @api.param('plan_id', 'Plan ID to explain', required=True)
    @api.param('client_id', 'Client ID for context (optional)', required=False)
    def get(self):
        """Get AI explanation of specific plan with client context"""
        try:
            from llm.tools import explain_plan
            from models import Client, Intake
            
            plan_id = request.args.get('plan_id', '').strip()
            if not plan_id:
                return {
                    'success': False,
                    'error': 'Plan ID parameter is required'
                }, 400
            
            # Get client context if provided
            client_context = None
            client_id = request.args.get('client_id')
            if client_id:
                try:
                    client = Client.get(int(client_id))
                    if client:
                        # Get latest intake for client
                        intakes = Intake.list_by_client(client.id)
                        latest_intake = intakes[0] if intakes else None
                        
                        client_context = {
                            'age': client.age if hasattr(client, 'age') else None,
                            'location': f"{client.zip}, {client.state}",
                            'county': client.county,
                            'income': latest_intake.income if latest_intake else None,
                            'household_size': latest_intake.household_size if latest_intake else None,
                            'has_doctors': len(latest_intake.doctors) > 0 if latest_intake else False,
                            'has_prescriptions': len(latest_intake.prescriptions) > 0 if latest_intake else False
                        }
                except (ValueError, AttributeError):
                    pass  # Invalid client_id, continue without context
            
            result = explain_plan(plan_id, client_context)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['response'],
                    'tool_calls_made': result.get('tool_calls_made', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }, 500
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

@api.route('/explain/top3')
class ExplainTop3Resource(Resource):
    @api.doc('explain_top3')
    @api.expect(api.model('Top3Request', {
        'plan_ids': fields.List(fields.String, required=True, description='List of top 3 plan IDs'),
        'client_id': fields.Integer(description='Client ID for context (optional)')
    }))
    def post(self):
        """Get AI summary comparison of top 3 plans"""
        try:
            from llm.tools import summarize_top3_plans
            from models import Client, Intake
            
            data = request.get_json()
            plan_ids = data.get('plan_ids', [])
            
            if not plan_ids or len(plan_ids) != 3:
                return {
                    'success': False,
                    'error': 'Exactly 3 plan IDs are required'
                }, 400
            
            # Get client context if provided
            client_context = None
            client_id = data.get('client_id')
            if client_id:
                try:
                    client = Client.get(client_id)
                    if client:
                        intakes = Intake.list_by_client(client.id)
                        latest_intake = intakes[0] if intakes else None
                        
                        client_context = {
                            'age': client.age if hasattr(client, 'age') else None,
                            'location': f"{client.zip}, {client.state}",
                            'county': client.county,
                            'income': latest_intake.income if latest_intake else None,
                            'household_size': latest_intake.household_size if latest_intake else None,
                            'has_doctors': len(latest_intake.doctors) > 0 if latest_intake else False,
                            'has_prescriptions': len(latest_intake.prescriptions) > 0 if latest_intake else False
                        }
                except (ValueError, AttributeError):
                    pass
            
            result = summarize_top3_plans(plan_ids, client_context)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['response'],
                    'tool_calls_made': result.get('tool_calls_made', 0)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }, 500
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

# Register APIs
create_plans_api(api)
create_quote_api(api)