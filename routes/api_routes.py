"""API routes for external integrations and AJAX calls"""
from flask import Blueprint, request, jsonify
from models import Client, Intake, storage
from services.plan_service import generate_plan_comparison
from services.gpt_service import generate_plan_explanation
from services.mock_data import get_mock_plans

api_bp = Blueprint('api', __name__)

@api_bp.route('/intake', methods=['POST'])
def api_create_intake():
    """API endpoint to create intake"""
    try:
        data = request.json
        
        # Create or get client
        client = Client.create(
            agent_id=data['agent_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            dob=data['dob'],
            zip_code=data['zip_code'],
            county=data['county'],
            state=data['state']
        )
        
        # Create intake
        intake = Intake.create(
            client_id=client['id'],
            plan_year=data['plan_year'],
            household_size=data['household_size'],
            ages=data['ages'],
            income=data['income'],
            doctors=data.get('doctors', []),
            prescriptions=data.get('prescriptions', []),
            preferences=data.get('preferences', {})
        )
        
        return jsonify({
            'success': True,
            'intake_id': intake['id'],
            'client_id': client['id']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@api_bp.route('/plans')
def api_get_plans():
    """API endpoint to get available plans"""
    zip_code = request.args.get('zip')
    county = request.args.get('county')
    state = request.args.get('state')
    plan_year = request.args.get('plan_year', 2024, type=int)
    
    if not all([zip_code, county, state]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    plans = get_mock_plans(zip_code, county, state, plan_year)
    return jsonify({'plans': plans})

@api_bp.route('/quote/preview', methods=['POST'])
def api_quote_preview():
    """API endpoint to generate quote preview"""
    try:
        data = request.json
        intake_id = data.get('intake_id')
        
        if not intake_id:
            return jsonify({'error': 'Missing intake_id'}), 400
        
        intake = Intake.get_by_id(intake_id)
        if not intake:
            return jsonify({'error': 'Intake not found'}), 404
        
        # Generate plan comparison
        quote_result = generate_plan_comparison(intake)
        
        return jsonify({
            'success': True,
            'aptc': quote_result['aptc'],
            'csr_level': quote_result['csr_level'],
            'plan_fits': [
                {
                    'plan_id': pf['plan']['id'],
                    'plan_name': pf['plan']['name'],
                    'issuer': pf['plan']['issuer'],
                    'metal': pf['plan']['metal'],
                    'net_premium': pf['net_premium'],
                    'fit_score': pf['fit_score'],
                    'rationale': pf['rationale']
                }
                for pf in quote_result['plan_fits']
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/explain/top3', methods=['POST'])
def api_explain_top3():
    """API endpoint to generate GPT explanation"""
    try:
        data = request.json
        intake_id = data.get('intake_id')
        
        intake = Intake.get_by_id(intake_id)
        if not intake:
            return jsonify({'error': 'Intake not found'}), 404
        
        # Generate plan comparison
        quote_result = generate_plan_comparison(intake)
        
        # Generate explanation
        explanation = generate_plan_explanation(
            intake,
            quote_result['top_3'],
            quote_result['aptc'],
            quote_result['csr_level']
        )
        
        return jsonify({
            'success': True,
            'explanation': explanation
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/clients/<client_id>/artifacts')
def api_get_artifacts(client_id):
    """API endpoint to get client artifacts"""
    from models import Artifact
    
    client = Client.get_by_id(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    
    artifacts = Artifact.get_by_client_id(client_id)
    
    return jsonify({
        'artifacts': [
            {
                'id': a['id'],
                'type': a['type'],
                'created_at': a['created_at'].isoformat(),
                'url': a.get('url')
            }
            for a in artifacts
        ]
    })

@api_bp.route('/export/pdf', methods=['POST'])
def api_export_pdf():
    """API endpoint to generate PDF export"""
    try:
        data = request.json
        intake_id = data.get('intake_id')
        
        intake = Intake.get_by_id(intake_id)
        if not intake:
            return jsonify({'error': 'Intake not found'}), 404
        
        client = Client.get_by_id(intake['client_id'])
        
        # Generate plan comparison and explanation
        quote_result = generate_plan_comparison(intake)
        explanation = generate_plan_explanation(
            intake,
            quote_result['top_3'],
            quote_result['aptc'],
            quote_result['csr_level']
        )
        
        # For API endpoint, return data instead of PDF bytes
        return jsonify({
            'success': True,
            'pdf_data': {
                'client': client,
                'intake': intake,
                'explanation': explanation,
                'quote_result': quote_result
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/soa', methods=['POST'])
def api_generate_soa():
    """API endpoint to generate Statement of Advice"""
    try:
        from services.gpt_service import generate_soa_content
        from models import Artifact
        
        data = request.json
        intake_id = data.get('intake_id')
        
        intake = Intake.get_by_id(intake_id)
        if not intake:
            return jsonify({'error': 'Intake not found'}), 404
        
        client = Client.get_by_id(intake['client_id'])
        quote_result = generate_plan_comparison(intake)
        
        # Generate SOA
        soa_content = generate_soa_content(intake, quote_result, client)
        
        # Save as artifact
        artifact = Artifact.create(
            client_id=client['id'],
            artifact_type='soa',
            payload=soa_content
        )
        
        return jsonify({
            'success': True,
            'soa_id': artifact['id'],
            'content': soa_content
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/debug/storage')
def api_debug_storage():
    """Debug endpoint to view storage contents"""
    return jsonify({
        'agents': len(storage['agents']),
        'clients': len(storage['clients']),
        'intakes': len(storage['intakes']),
        'artifacts': len(storage['artifacts']),
        'sample_agent': list(storage['agents'].values())[:1],
        'sample_client': list(storage['clients'].values())[:1]
    })
