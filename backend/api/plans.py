import json
import os
from typing import List, Optional
from flask import request
from flask_restx import Resource, fields
from models import Plan

def load_mock_plans() -> List[dict]:
    """Load mock ACA plan data from JSON file"""
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, '..', 'data', 'mock_aca_plans.json')
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def normalize_plan_data(raw_plan: dict) -> Plan:
    """Normalize raw plan data into Plan object"""
    # Calculate average premium (adult + child) / 2 for simplicity
    premium_full = (raw_plan['premium_adult'] + raw_plan['premium_child']) / 2
    
    # Use individual deductible and out-of-pocket max
    deductible = raw_plan['deductible_individual']
    moop = raw_plan['out_of_pocket_max_individual']
    
    # CSR flag indicates if plan has Cost Sharing Reduction
    csr_flag = bool(raw_plan.get('csr_variation', ''))
    
    return Plan.create(
        plan_id=raw_plan['plan_id'],
        plan_year=raw_plan['plan_year'],
        issuer=raw_plan['issuer_name'],
        name=raw_plan['plan_name'],
        metal=raw_plan['metal_level'],
        premium_full=premium_full,
        deductible=deductible,
        moop=moop,
        csr_flag=csr_flag
    )

def seed_plans_data():
    """Load and normalize all mock plans into storage"""
    raw_plans = load_mock_plans()
    
    # Clear existing plans
    from models import _storage
    _storage['plans'].clear()
    
    # Load normalized plans
    for raw_plan in raw_plans:
        normalize_plan_data(raw_plan)

def filter_plans_by_location(plans: List[Plan], zip_code: Optional[str] = None, 
                           county: Optional[str] = None) -> List[Plan]:
    """Filter plans by zip code or county"""
    if not zip_code and not county:
        return plans
    
    # Load raw plan data for location filtering
    raw_plans = load_mock_plans()
    plan_locations = {}
    
    for raw_plan in raw_plans:
        plan_locations[raw_plan['plan_id']] = {
            'zip_codes': raw_plan.get('zip_codes', []),
            'counties': raw_plan.get('counties', [])
        }
    
    filtered_plans = []
    for plan in plans:
        location_data = plan_locations.get(plan.id, {})
        
        # Check zip code match
        if zip_code:
            if zip_code in location_data.get('zip_codes', []):
                filtered_plans.append(plan)
                continue
        
        # Check county match
        if county:
            if county in location_data.get('counties', []):
                filtered_plans.append(plan)
                continue
        
        # If no location filters specified, include all
        if not zip_code and not county:
            filtered_plans.append(plan)
    
    return filtered_plans

def create_plans_api(api):
    """Create plans API routes"""
    
    # API model for documentation
    plan_response_model = api.model('PlanResponse', {
        'id': fields.String(required=True, description='Plan ID'),
        'plan_year': fields.Integer(required=True, description='Plan year'),
        'issuer': fields.String(required=True, description='Insurance issuer'),
        'name': fields.String(required=True, description='Plan name'),
        'metal': fields.String(required=True, description='Metal level'),
        'premium_full': fields.Float(required=True, description='Full premium'),
        'deductible': fields.Float(required=True, description='Deductible amount'),
        'moop': fields.Float(required=True, description='Maximum out-of-pocket'),
        'csr_flag': fields.Boolean(required=True, description='Cost Sharing Reduction available')
    })
    
    @api.route('/plans')
    class PlansResource(Resource):
        @api.doc('list_plans')
        @api.param('zip', 'ZIP code filter', type='string', required=False)
        @api.param('county', 'County filter', type='string', required=False)
        @api.param('year', 'Plan year filter', type='integer', required=False)
        @api.param('metal', 'Metal level filter (Bronze, Silver, Gold, Platinum)', type='string', required=False)
        @api.param('issuer', 'Insurance issuer filter', type='string', required=False)
        def get(self):
            """Get filtered list of available plans"""
            try:
                # Ensure plans are loaded
                if not Plan.list_all():
                    seed_plans_data()
                
                # Get query parameters
                zip_code = request.args.get('zip')
                county = request.args.get('county')
                year = request.args.get('year', type=int)
                metal = request.args.get('metal')
                issuer = request.args.get('issuer')
                
                # Start with all plans
                plans = Plan.list_all()
                
                # Apply filters
                if year:
                    plans = [p for p in plans if p.plan_year == year]
                
                if metal:
                    plans = [p for p in plans if p.metal.lower() == metal.lower()]
                
                if issuer:
                    plans = [p for p in plans if issuer.lower() in p.issuer.lower()]
                
                # Apply location filters
                plans = filter_plans_by_location(plans, zip_code, county)
                
                # Convert to response format
                plans_data = []
                for plan in plans:
                    plans_data.append({
                        'id': plan.id,
                        'plan_year': plan.plan_year,
                        'issuer': plan.issuer,
                        'name': plan.name,
                        'metal': plan.metal,
                        'premium_full': plan.premium_full,
                        'deductible': plan.deductible,
                        'moop': plan.moop,
                        'csr_flag': plan.csr_flag
                    })
                
                return {
                    'success': True,
                    'data': plans_data,
                    'count': len(plans_data)
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }, 500