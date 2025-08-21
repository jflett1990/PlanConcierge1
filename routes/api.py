import json
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from services.plan_service import PlanService
from services.gpt_service import GPTService
from services.pdf_service import PDFService
from models import *

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

plan_service = PlanService()
gpt_service = GPTService()
pdf_service = PDFService()

@api_bp.route('/intake', methods=['POST'])
def create_intake():
    """Create new intake from client data"""
    try:
        data = request.get_json()
        logger.debug(f"Creating intake with data: {data}")
        
        # Create or get client
        client_id = get_next_id(clients_store)
        client = Client(
            id=client_id,
            agent_id="1",  # Default agent for MVP
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            dob=data['dob'],
            zip_code=data['zip_code'],
            county=data['county'],
            state=data['state']
        )
        clients_store[client_id] = client
        
        # Create doctors list
        doctors = []
        for doc in data.get('doctors', []):
            doctors.append(Doctor(
                npi=doc.get('npi', ''),
                name=doc['name'],
                specialty=doc.get('specialty', '')
            ))
        
        # Create prescriptions list  
        prescriptions = []
        for rx in data.get('prescriptions', []):
            prescriptions.append(Prescription(
                name=rx['name'],
                dosage=rx.get('dosage', ''),
                quantity=rx.get('quantity', 30)
            ))
        
        # Create preferences
        prefs = Preferences(
            max_premium=data.get('preferences', {}).get('max_premium'),
            prefer_low_deductible=data.get('preferences', {}).get('prefer_low_deductible', False),
            prefer_broad_network=data.get('preferences', {}).get('prefer_broad_network', True)
        )
        
        # Create intake
        intake_id = get_next_id(intakes_store)
        intake = Intake(
            id=intake_id,
            client_id=client_id,
            plan_year=data['plan_year'],
            household_size=data['household_size'],
            ages=data['ages'],
            annual_income=data['annual_income'],
            doctors=doctors,
            prescriptions=prescriptions,
            preferences=prefs
        )
        intakes_store[intake_id] = intake
        
        return jsonify({
            'intake_id': intake_id,
            'client_id': client_id,
            'status': 'created'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating intake: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/plans')
def get_plans():
    """Get available plans for given parameters"""
    try:
        zip_code = request.args.get('zip')
        county = request.args.get('county')
        plan_year = int(request.args.get('plan_year', 2024))
        
        plans = plan_service.get_plans_by_location(zip_code, county, plan_year)
        
        return jsonify({
            'plans': [plan.__dict__ for plan in plans],
            'count': len(plans)
        })
        
    except Exception as e:
        logger.error(f"Error fetching plans: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/quote/preview', methods=['POST'])
def quote_preview():
    """Compute APTC, CSR and plan fits for an intake"""
    try:
        data = request.get_json()
        intake_id = data['intake_id']
        
        intake = intakes_store.get(intake_id)
        if not intake:
            return jsonify({'error': 'Intake not found'}), 404
            
        client = clients_store.get(intake.client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get available plans
        plans = plan_service.get_plans_by_location(
            client.zip_code, 
            client.county, 
            intake.plan_year
        )
        
        # Calculate APTC and CSR
        aptc, csr_level = plan_service.calculate_aptc_csr(
            intake.annual_income,
            intake.household_size,
            intake.ages
        )
        
        # Create quote result
        quote_result_id = get_next_id(quote_results_store)
        quote_result = QuoteResult(
            id=quote_result_id,
            intake_id=intake_id,
            aptc=aptc,
            csr_level=csr_level
        )
        quote_results_store[quote_result_id] = quote_result
        
        # Calculate plan fits
        plan_fits = []
        for plan in plans:
            plan_fit = plan_service.calculate_plan_fit(
                plan, intake, quote_result
            )
            plan_fits_store[plan_fit.id] = plan_fit
            plan_fits.append(plan_fit)
        
        # Sort by fit score and get top 3
        top_3_fits = sorted(plan_fits, key=lambda x: x.fit_score, reverse=True)[:3]
        
        return jsonify({
            'quote_result_id': quote_result_id,
            'aptc': aptc,
            'csr_level': csr_level,
            'top_3_plans': [
                {
                    'plan_fit': fit.__dict__,
                    'plan': next(p for p in plans if p.id == fit.plan_id).__dict__
                }
                for fit in top_3_fits
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in quote preview: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/explain/top3', methods=['POST'])
def explain_top3():
    """Generate GPT explanation for top 3 plans"""
    try:
        data = request.get_json()
        quote_result_id = data['quote_result_id']
        
        quote_result = quote_results_store.get(quote_result_id)
        if not quote_result:
            return jsonify({'error': 'Quote result not found'}), 404
            
        intake = intakes_store.get(quote_result.intake_id)
        client = clients_store.get(intake.client_id)
        
        # Get top 3 plan fits
        all_fits = filter_by_field(plan_fits_store, 'quote_result_id', quote_result_id)
        top_3_fits = sorted(all_fits, key=lambda x: x.fit_score, reverse=True)[:3]
        
        # Get corresponding plans
        top_3_plans = []
        for fit in top_3_fits:
            plan = plans_store.get(fit.plan_id)
            if plan:
                top_3_plans.append({'plan': plan, 'fit': fit})
        
        # Generate explanation using GPT
        explanation = gpt_service.explain_plan_recommendations(
            client, intake, quote_result, top_3_plans
        )
        
        return jsonify({
            'explanation': explanation,
            'quote_result_id': quote_result_id
        })
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/export/pdf', methods=['POST'])
def export_pdf():
    """Generate and return PDF for top 3 recommendations"""
    try:
        data = request.get_json()
        quote_result_id = data['quote_result_id']
        explanation = data.get('explanation', '')
        
        quote_result = quote_results_store.get(quote_result_id)
        if not quote_result:
            return jsonify({'error': 'Quote result not found'}), 404
            
        intake = intakes_store.get(quote_result.intake_id)
        client = clients_store.get(intake.client_id)
        
        # Get top 3 plan fits and plans
        all_fits = filter_by_field(plan_fits_store, 'quote_result_id', quote_result_id)
        top_3_fits = sorted(all_fits, key=lambda x: x.fit_score, reverse=True)[:3]
        
        top_3_data = []
        for fit in top_3_fits:
            plan = plans_store.get(fit.plan_id)
            if plan:
                top_3_data.append({'plan': plan, 'fit': fit})
        
        # Generate PDF
        pdf_content = pdf_service.generate_recommendation_pdf(
            client, intake, quote_result, top_3_data, explanation
        )
        
        # Save as artifact
        artifact_id = get_next_id(artifacts_store)
        artifact = Artifact(
            id=artifact_id,
            client_id=client.id,
            type='pdf',
            payload=f'recommendation_{quote_result_id}.pdf'
        )
        artifacts_store[artifact_id] = artifact
        
        return pdf_content, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename=recommendation_{client.last_name}_{quote_result_id}.pdf'
        }
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/soa', methods=['POST'])
def generate_soa():
    """Generate Statement of Advice"""
    try:
        data = request.get_json()
        quote_result_id = data['quote_result_id']
        
        quote_result = quote_results_store.get(quote_result_id)
        if not quote_result:
            return jsonify({'error': 'Quote result not found'}), 404
            
        intake = intakes_store.get(quote_result.intake_id)
        client = clients_store.get(intake.client_id)
        
        # Create SOA artifact
        soa_data = {
            'client': client.__dict__,
            'intake': intake.__dict__,
            'quote_result': quote_result.__dict__,
            'timestamp': datetime.now().isoformat(),
            'agent_id': client.agent_id,
            'compliance_notes': [
                "Networks and formularies change. Verify at enrollment.",
                "Premium Tax Credits are subject to income verification.",
                "This is a preliminary recommendation based on information provided."
            ]
        }
        
        artifact_id = get_next_id(artifacts_store)
        artifact = Artifact(
            id=artifact_id,
            client_id=client.id,
            type='soa',
            payload=json.dumps(soa_data, default=str)
        )
        artifacts_store[artifact_id] = artifact
        
        return jsonify({
            'soa_id': artifact_id,
            'status': 'generated',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating SOA: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/clients/<client_id>/artifacts')
def get_client_artifacts(client_id):
    """Get all artifacts for a client"""
    try:
        artifacts = filter_by_field(artifacts_store, 'client_id', client_id)
        
        return jsonify({
            'artifacts': [art.__dict__ for art in artifacts],
            'count': len(artifacts)
        })
        
    except Exception as e:
        logger.error(f"Error fetching artifacts: {str(e)}")
        return jsonify({'error': str(e)}), 400
