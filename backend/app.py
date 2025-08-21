import os
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from models import (
    Client, Intake, Artifact, Doctor, Prescription, Preferences
)
from api.plans import create_plans_api

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

# Register plans API
create_plans_api(api)