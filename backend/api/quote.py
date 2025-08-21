import json
import os
from typing import List, Dict, Optional, Tuple
from flask import request
from flask_restx import Resource, fields
from models import Intake, Client, Plan, QuoteResult, PlanFit

def load_fpl_table() -> Dict:
    """Load Federal Poverty Level table"""
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, '..', 'data', 'fpl_table.json')
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_slcsp_premiums() -> Dict:
    """Load Second Lowest Cost Silver Plan premiums by ZIP code"""
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, '..', 'data', 'slcsp_premiums.json')
    
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_age_bracket(age: int) -> str:
    """Map age to SLCSP premium age bracket"""
    if age <= 30:
        return "age_27"
    elif age <= 45:
        return "age_40"
    elif age <= 55:
        return "age_50"
    else:
        return "age_60"

def compute_slcsp_premium(zip_code: str, ages: List[int], plan_year: int = 2024) -> float:
    """Compute Second Lowest Cost Silver Plan premium for household"""
    slcsp_data = load_slcsp_premiums()
    year_data = slcsp_data.get(str(plan_year), {})
    zip_data = year_data.get(zip_code, {})
    
    if not zip_data:
        # Default SLCSP premium if ZIP not found
        return 400.0 * len(ages)
    
    total_premium = 0.0
    for age in ages:
        age_bracket = get_age_bracket(age)
        premium = zip_data.get(age_bracket, 400.0)
        total_premium += premium
    
    return total_premium

def get_fpl_amount(household_size: int, state: str = "CA", plan_year: int = 2024) -> float:
    """Get Federal Poverty Level amount for household size"""
    fpl_data = load_fpl_table()
    year_data = fpl_data.get(str(plan_year), {})
    
    # California uses 48 states table
    if state in ["AK", "Alaska"]:
        state_data = year_data.get("alaska", {})
    elif state in ["HI", "Hawaii"]:
        state_data = year_data.get("hawaii", {})
    else:
        state_data = year_data.get("48_states", {})
    
    # For households larger than 8, add $5,380 per additional person
    if household_size <= 8:
        return float(state_data.get(str(household_size), 15060))
    else:
        base_8 = float(state_data.get("8", 52720))
        additional = (household_size - 8) * 5380
        return base_8 + additional

def compute_aptc(income: float, slcsp_premium: float, fpl_amount: float) -> float:
    """Compute Advanced Premium Tax Credit"""
    income_fpl_ratio = income / fpl_amount
    
    # No APTC if income is below 100% FPL or above 400% FPL
    if income_fpl_ratio < 1.0 or income_fpl_ratio > 4.0:
        return 0.0
    
    # Premium contribution caps based on FPL percentage (interpolated)
    if income_fpl_ratio <= 1.5:
        # Linear interpolation between 100% (2.35%) and 150% (4.05%)
        contribution_rate = 0.0235 + (income_fpl_ratio - 1.0) * (0.0405 - 0.0235) / 0.5
    elif income_fpl_ratio <= 2.0:
        # Linear interpolation between 150% (4.05%) and 200% (6.5%)
        contribution_rate = 0.0405 + (income_fpl_ratio - 1.5) * (0.065 - 0.0405) / 0.5
    elif income_fpl_ratio <= 2.5:
        # Linear interpolation between 200% (6.5%) and 250% (8.5%)
        contribution_rate = 0.065 + (income_fpl_ratio - 2.0) * (0.085 - 0.065) / 0.5
    else:
        # 250% FPL and above: 8.5%
        contribution_rate = 0.085
    
    # Calculate APTC - contribution is monthly
    monthly_income = income / 12
    monthly_contribution = monthly_income * contribution_rate
    aptc = max(0, slcsp_premium - monthly_contribution)
    
    return round(aptc, 2)

def determine_csr_level(income: float, fpl_amount: float) -> str:
    """Determine Cost Sharing Reduction level"""
    income_fpl_ratio = income / fpl_amount
    
    if income_fpl_ratio <= 1.5:
        return "94%"  # 94% AV
    elif income_fpl_ratio <= 2.0:
        return "87%"  # 87% AV
    elif income_fpl_ratio <= 2.5:
        return "73%"  # 73% AV
    else:
        return "70%"  # Standard Silver (70% AV)

def compute_oop_risk_score(moop: float, deductible: float) -> float:
    """Compute out-of-pocket risk score (0-100, lower is better)"""
    # Normalize based on typical ACA plan ranges
    max_moop = 9450.0  # 2024 ACA limit
    max_deductible = 9450.0
    
    # Weight MOOP more heavily than deductible
    moop_score = (moop / max_moop) * 70
    deductible_score = (deductible / max_deductible) * 30
    
    total_score = moop_score + deductible_score
    return round(min(100, total_score), 2)

def create_quote_api(api):
    """Create quote API routes"""
    
    # API models for documentation
    quote_request_model = api.model('QuoteRequest', {
        'intake_id': fields.Integer(required=True, description='Intake ID')
    })
    
    plan_fit_model = api.model('PlanFit', {
        'plan_id': fields.String(required=True, description='Plan ID'),
        'issuer': fields.String(required=True, description='Insurance issuer'),
        'name': fields.String(required=True, description='Plan name'),
        'metal': fields.String(required=True, description='Metal level'),
        'premium_full': fields.Float(required=True, description='Full premium'),
        'net_premium': fields.Float(required=True, description='Net premium after APTC'),
        'deductible': fields.Float(required=True, description='Deductible'),
        'moop': fields.Float(required=True, description='Maximum out-of-pocket'),
        'oop_risk_score': fields.Float(required=True, description='Out-of-pocket risk score'),
        'csr_flag': fields.Boolean(required=True, description='CSR eligible')
    })
    
    quote_response_model = api.model('QuoteResponse', {
        'quote_result_id': fields.Integer(required=True, description='Quote result ID'),
        'aptc': fields.Float(required=True, description='Advanced Premium Tax Credit'),
        'csr_level': fields.String(required=True, description='Cost Sharing Reduction level'),
        'slcsp_premium': fields.Float(required=True, description='SLCSP premium'),
        'income_fpl_ratio': fields.Float(required=True, description='Income as % of FPL'),
        'plans': fields.List(fields.Nested(plan_fit_model), description='Available plans with pricing')
    })
    
    @api.route('/quote/preview')
    class QuotePreviewResource(Resource):
        @api.expect(quote_request_model)
        @api.doc('create_quote_preview')
        def post(self):
            """Generate quote preview with APTC and plan pricing"""
            try:
                data = request.get_json()
                intake_id = data['intake_id']
                
                # Load intake
                intake = Intake.get(intake_id)
                if not intake:
                    return {
                        'success': False,
                        'error': 'Intake not found'
                    }, 404
                
                # Load client for location info
                client = Client.get(intake.client_id)
                if not client:
                    return {
                        'success': False,
                        'error': 'Client not found'
                    }, 404
                
                # Ensure plans are loaded
                from api.plans import seed_plans_data
                if not Plan.list_all():
                    seed_plans_data()
                
                # Compute SLCSP premium
                slcsp_premium = compute_slcsp_premium(
                    zip_code=client.zip,
                    ages=intake.ages,
                    plan_year=intake.plan_year
                )
                
                # Get FPL amount
                fpl_amount = get_fpl_amount(
                    household_size=intake.household_size,
                    state=client.state,
                    plan_year=intake.plan_year
                )
                
                # Compute APTC
                aptc = compute_aptc(intake.income, slcsp_premium, fpl_amount)
                
                # Determine CSR level
                csr_level = determine_csr_level(intake.income, fpl_amount)
                
                # Create quote result
                quote_result = QuoteResult.create(
                    intake_id=intake_id,
                    aptc=aptc,
                    csr_level=csr_level
                )
                
                # Get available plans
                plans = Plan.list_by_year(intake.plan_year)
                
                # Compute plan fits
                plan_fits = []
                for plan in plans:
                    net_premium = max(0, plan.premium_full - aptc)
                    oop_risk_score = compute_oop_risk_score(plan.moop, plan.deductible)
                    
                    # Create plan fit record
                    plan_fit = PlanFit.create(
                        quote_result_id=quote_result.id,
                        plan_id=plan.id,
                        net_premium=net_premium,
                        doctor_hits=[],  # TODO: Implement provider matching
                        rx_hits=[],      # TODO: Implement formulary matching
                        rationale={
                            "benefits_match": "Plan analysis pending",
                            "cost_analysis": f"Net premium: ${net_premium:.2f}/month after ${aptc:.2f} APTC",
                            "trade_offs": f"Risk score: {oop_risk_score}/100"
                        },
                        fit_score=100 - oop_risk_score  # Higher score = lower risk
                    )
                    
                    plan_fits.append({
                        'plan_id': plan.id,
                        'issuer': plan.issuer,
                        'name': plan.name,
                        'metal': plan.metal,
                        'premium_full': plan.premium_full,
                        'net_premium': net_premium,
                        'deductible': plan.deductible,
                        'moop': plan.moop,
                        'oop_risk_score': oop_risk_score,
                        'csr_flag': plan.csr_flag
                    })
                
                # Sort plans by fit score (descending)
                plan_fits.sort(key=lambda x: 100 - x['oop_risk_score'], reverse=True)
                
                return {
                    'success': True,
                    'data': {
                        'quote_result_id': quote_result.id,
                        'aptc': aptc,
                        'csr_level': csr_level,
                        'slcsp_premium': slcsp_premium,
                        'income_fpl_ratio': round(intake.income / fpl_amount, 2),
                        'plans': plan_fits
                    }
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }, 500