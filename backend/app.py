import os
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from models import (
    Client, Intake, Artifact, Doctor, Prescription, Preferences
)
from api.plans import create_plans_api
from api.quote import create_quote_api
from api.compliance import api as compliance_api

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Initialize Flask-RESTX API with custom prefix to avoid root route conflict
api = Api(app, 
          version='1.0', 
          title='Plan Concierge API',
          description='ACA/Medicare Plan Comparison API',
          doc='/api/docs/',
          prefix='/api',
          add_specs=False)

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

# Root route to serve frontend demo
@app.route('/')
def serve_frontend():
    """Serve the frontend demo page"""
    from flask import send_file
    import os
    
    # Serve the frontend demo HTML
    demo_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'demo.html')
    if os.path.exists(demo_path):
        return send_file(demo_path)
    
    # Fallback to API status
    return jsonify({
        "message": "Plan Concierge API",
        "version": "1.0.0",
        "status": "running",
        "frontend": "Demo not found",
        "api_docs": "/api/docs/"
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

# PDF Export endpoint
@api.route('/export/pdf')
class PDFExportResource(Resource):
    @api.doc('export_pdf')
    @api.expect(api.model('PDFExportRequest', {
        'client_id': fields.Integer(required=True, description='Client ID'),
        'plans': fields.List(fields.Raw, required=True, description='Plan data to include'),
        'quote_data': fields.Raw(required=True, description='Quote results'),
        'explanation': fields.Raw(description='AI explanation content')
    }))
    def post(self):
        """Export plan comparison as PDF"""
        try:
            import tempfile
            import os
            from weasyprint import HTML, CSS
            from flask import send_file, url_for
            import uuid
            from datetime import datetime
            
            data = request.get_json()
            client_id = data.get('client_id')
            plans = data.get('plans', [])
            quote_data = data.get('quote_data', {})
            explanation = data.get('explanation', {})
            
            if not client_id or not plans:
                return {
                    'success': False,
                    'error': 'Client ID and plans data are required'
                }, 400
            
            # Get client info
            client = Client.get(client_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Client not found'
                }, 404
            
            # Generate HTML content
            html_content = generate_pdf_html(client, plans, quote_data, explanation)
            
            # Create temporary PDF file
            pdf_filename = f"plan_comparison_{client_id}_{uuid.uuid4().hex[:8]}.pdf"
            tmp_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            pdf_path = os.path.join(tmp_dir, pdf_filename)
            
            # Generate PDF with WeasyPrint
            html_doc = HTML(string=html_content)
            css_styles = CSS(string=get_pdf_styles())
            html_doc.write_pdf(pdf_path, stylesheets=[css_styles])
            
            # Save artifact record
            artifact = Artifact.create(
                client_id=client_id,
                type='pdf_comparison',
                url=f'/download/pdf/{pdf_filename}',
                payload={'plans_count': len(plans), 'generated_at': datetime.now().isoformat()}
            )
            
            return {
                'success': True,
                'data': {
                    'download_url': f'/download/pdf/{pdf_filename}',
                    'filename': pdf_filename,
                    'artifact_id': artifact.id
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }, 500

# PDF Download endpoint
@app.route('/download/pdf/<filename>')
def download_pdf(filename):
    """Download generated PDF file"""
    try:
        import os
        from flask import send_file, abort
        
        tmp_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp')
        pdf_path = os.path.join(tmp_dir, filename)
        
        if not os.path.exists(pdf_path):
            abort(404)
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        abort(500)

def generate_pdf_html(client, plans, quote_data, explanation):
    """Generate HTML content for PDF export"""
    from datetime import datetime
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Health Plan Comparison - {client.first_name} {client.last_name}</title>
    </head>
    <body>
        <div class="header">
            <h1>Health Plan Comparison Report</h1>
            <div class="client-info">
                <h2>Prepared for: {client.first_name} {client.last_name}</h2>
                <p><strong>Location:</strong> {client.zip}, {client.state}</p>
                <p><strong>Report Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
        </div>
        
        <div class="summary">
            <h2>Plan Comparison Summary</h2>
            <p>Based on your household information and preferences, we've identified the following health plan options:</p>
        </div>
        
        <div class="plans-table">
            <h2>Recommended Plans</h2>
            <table>
                <thead>
                    <tr>
                        <th>Plan Name</th>
                        <th>Issuer</th>
                        <th>Metal Level</th>
                        <th>Net Premium</th>
                        <th>Deductible</th>
                        <th>Max Out-of-Pocket</th>
                        <th>Fit Score</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, plan in enumerate(plans[:10]):  # Limit to top 10 plans
        fit_score = plan.get('fit_score', 'N/A')
        net_premium = plan.get('net_premium', plan.get('premium_full', 0))
        
        html += f"""
                    <tr class="{'top-plan' if i < 3 else ''}">
                        <td>{plan.get('name', 'N/A')}</td>
                        <td>{plan.get('issuer', 'N/A')}</td>
                        <td>{plan.get('metal', 'N/A')}</td>
                        <td>${net_premium:.2f}/month</td>
                        <td>${plan.get('deductible', 0):,.0f}</td>
                        <td>${plan.get('moop', 0):,.0f}</td>
                        <td>{fit_score}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    """
    
    # Add explanation if provided
    if explanation and explanation.get('data'):
        exp_data = explanation['data']
        html += f"""
        <div class="explanation">
            <h2>{exp_data.get('title', 'Plan Analysis')}</h2>
        """
        
        for section in exp_data.get('sections', []):
            html += f"""
            <div class="section">
                <h3>{section.get('heading', '')}</h3>
                <p>{section.get('body', '')}</p>
            </div>
            """
        
        # Add citations
        citations = exp_data.get('citations', [])
        if citations:
            html += """
            <div class="citations">
                <h3>Sources</h3>
                <ul>
            """
            for citation in citations:
                html += f"""
                    <li><a href="{citation.get('url', '')}">{citation.get('title', '')}</a></li>
                """
            html += """
                </ul>
            </div>
            """
        
        html += "</div>"
    
    # Add important disclaimers
    html += """
        <div class="disclaimer">
            <h2>Important Information</h2>
            <ul>
                <li><strong>Enrollment Verification:</strong> Please verify all plan details, networks, and formularies at enrollment as they may change.</li>
                <li><strong>Premium Changes:</strong> Premiums and benefits may change annually during open enrollment.</li>
                <li><strong>Network Access:</strong> Always confirm your providers and prescriptions are covered before enrolling.</li>
                <li><strong>Professional Advice:</strong> This comparison is for informational purposes. Consult with licensed insurance professionals for personalized advice.</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by Plan Concierge | {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
    </body>
    </html>
    """
    
    return html

def get_pdf_styles():
    """Return CSS styles for PDF generation"""
    return """
    @page {
        size: A4;
        margin: 1in;
        @top-right {
            content: "Page " counter(page) " of " counter(pages);
        }
    }
    
    body {
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.4;
        color: #333;
    }
    
    .header {
        border-bottom: 2px solid #007bff;
        margin-bottom: 20px;
        padding-bottom: 15px;
    }
    
    .header h1 {
        color: #007bff;
        margin: 0 0 10px 0;
        font-size: 24px;
    }
    
    .client-info h2 {
        margin: 10px 0 5px 0;
        font-size: 18px;
        color: #495057;
    }
    
    .client-info p {
        margin: 3px 0;
        color: #666;
    }
    
    .summary, .explanation {
        margin: 20px 0;
    }
    
    .summary h2, .explanation h2 {
        color: #007bff;
        border-bottom: 1px solid #dee2e6;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    
    .plans-table {
        margin: 20px 0;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    
    th {
        background-color: #f8f9fa;
        font-weight: bold;
        color: #495057;
    }
    
    .top-plan {
        background-color: #fff3cd;
    }
    
    .section {
        margin: 15px 0;
    }
    
    .section h3 {
        color: #0056b3;
        margin: 10px 0 5px 0;
    }
    
    .disclaimer {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 15px;
        margin: 20px 0;
    }
    
    .disclaimer h2 {
        color: #dc3545;
        margin-top: 0;
    }
    
    .disclaimer ul {
        margin: 10px 0;
        padding-left: 20px;
    }
    
    .disclaimer li {
        margin: 5px 0;
    }
    
    .citations ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    .citations li {
        margin: 5px 0;
    }
    
    .footer {
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid #dee2e6;
        text-align: center;
        color: #666;
        font-size: 10px;
    }
    """

# Register APIs
create_plans_api(api)
create_quote_api(api)
api.add_namespace(compliance_api, path='/compliance')