"""Plan comparison and fit scoring service"""
from services.mock_data import (
    get_mock_plans, 
    check_provider_network, 
    check_drug_formulary,
    calculate_aptc,
    determine_csr_level
)

def calculate_fit_score(plan, net_premium, doctor_coverage, rx_coverage, max_premium=1000):
    """
    Calculate weighted fit score based on:
    - 40% premium component
    - 30% out-of-pocket component  
    - 20% doctor component
    - 10% prescription component
    """
    
    # Premium component (normalized inverse - lower premium = higher score)
    premium_component = max(0, (max_premium - net_premium) / max_premium)
    
    # OOP component (based on deductible and MOOP)
    max_deductible = 8000
    max_moop = 10000
    deductible_score = max(0, (max_deductible - plan['deductible']) / max_deductible)
    moop_score = max(0, (max_moop - plan['moop']) / max_moop)
    oop_component = (deductible_score + moop_score) / 2
    
    # Doctor component (% in network)
    if doctor_coverage:
        in_network_count = sum(1 for doc in doctor_coverage if doc['in_network'])
        doctor_component = in_network_count / len(doctor_coverage) if doctor_coverage else 0.5
    else:
        doctor_component = 0.5  # Neutral if no doctors specified
    
    # Prescription component (average tier score with penalties)
    if rx_coverage:
        tier_scores = []
        for drug in rx_coverage:
            if drug['covered']:
                # Lower tier = higher score
                tier_score = max(0, (5 - drug['tier']) / 4)
                # Penalties for PA/ST
                if drug['prior_auth']:
                    tier_score *= 0.8
                if drug['step_therapy']:
                    tier_score *= 0.7
                tier_scores.append(tier_score)
            else:
                tier_scores.append(0)
        rx_component = sum(tier_scores) / len(tier_scores) if tier_scores else 0.5
    else:
        rx_component = 0.5  # Neutral if no prescriptions specified
    
    # Weighted final score
    fit_score = 100 * (
        0.40 * premium_component +
        0.30 * oop_component +
        0.20 * doctor_component +
        0.10 * rx_component
    )
    
    return round(fit_score, 1)

def generate_plan_comparison(intake_data):
    """Generate comprehensive plan comparison with fit scores"""
    
    # Get client location info
    zip_code = intake_data.get('zip_code')
    county = intake_data.get('county')
    state = intake_data.get('state')
    plan_year = intake_data.get('plan_year', 2024)
    
    # Calculate APTC and CSR
    aptc = calculate_aptc(
        intake_data['income'],
        intake_data['household_size'],
        intake_data['ages'],
        county,
        state
    )
    
    csr_level = determine_csr_level(
        intake_data['income'],
        intake_data['household_size']
    )
    
    # Get available plans
    plans = get_mock_plans(zip_code, county, state, plan_year)
    
    # Extract doctor NPIs and drug names
    doctor_npis = [doc.get('npi') for doc in intake_data.get('doctors', []) if doc.get('npi')]
    drug_names = [rx.get('name') for rx in intake_data.get('prescriptions', []) if rx.get('name')]
    
    plan_ids = [plan['id'] for plan in plans]
    
    # Check provider networks and formularies
    provider_results = check_provider_network(plan_ids, doctor_npis)
    formulary_results = check_drug_formulary(plan_ids, drug_names)
    
    # Calculate fit scores for each plan
    plan_fits = []
    
    for plan in plans:
        plan_id = plan['id']
        
        # Calculate net premium (after APTC)
        monthly_premium = plan['premium_full']
        net_premium = max(0, monthly_premium - aptc)
        
        # Get doctor and drug coverage for this plan
        doctor_coverage = provider_results.get(plan_id, [])
        rx_coverage = formulary_results.get(plan_id, [])
        
        # Calculate fit score
        fit_score = calculate_fit_score(plan, net_premium, doctor_coverage, rx_coverage)
        
        # Generate rationale
        rationale = generate_plan_rationale(plan, net_premium, doctor_coverage, rx_coverage, fit_score)
        
        plan_fit = {
            'plan': plan,
            'net_premium': net_premium,
            'doctor_coverage': doctor_coverage,
            'rx_coverage': rx_coverage,
            'fit_score': fit_score,
            'rationale': rationale
        }
        
        plan_fits.append(plan_fit)
    
    # Sort by fit score (highest first)
    plan_fits.sort(key=lambda x: x['fit_score'], reverse=True)
    
    return {
        'aptc': aptc,
        'csr_level': csr_level,
        'plan_fits': plan_fits,
        'top_3': plan_fits[:3]
    }

def generate_plan_rationale(plan, net_premium, doctor_coverage, rx_coverage, fit_score):
    """Generate human-readable rationale for plan ranking"""
    rationale = {
        'premium_analysis': f"${net_premium:.2f}/month after tax credits",
        'coverage_highlights': [],
        'doctor_network': f"{sum(1 for d in doctor_coverage if d['in_network'])}/{len(doctor_coverage)} doctors in-network" if doctor_coverage else "No doctors specified",
        'prescription_coverage': f"{sum(1 for r in rx_coverage if r['covered'])}/{len(rx_coverage)} medications covered" if rx_coverage else "No prescriptions specified",
        'overall_rating': get_rating_description(fit_score)
    }
    
    # Add coverage highlights based on plan benefits
    if plan['metal'] == 'Bronze':
        rationale['coverage_highlights'].append("Lower monthly premium, higher out-of-pocket costs")
    elif plan['metal'] == 'Silver':
        rationale['coverage_highlights'].append("Balanced premium and out-of-pocket costs")
        if plan['csr_flag']:
            rationale['coverage_highlights'].append("Eligible for cost-sharing reductions")
    elif plan['metal'] == 'Gold':
        rationale['coverage_highlights'].append("Higher premium, lower out-of-pocket costs")
    elif plan['metal'] == 'Platinum':
        rationale['coverage_highlights'].append("Highest premium, lowest out-of-pocket costs")
    
    return rationale

def get_rating_description(fit_score):
    """Convert numeric fit score to descriptive rating"""
    if fit_score >= 80:
        return "Excellent fit"
    elif fit_score >= 70:
        return "Very good fit"
    elif fit_score >= 60:
        return "Good fit"
    elif fit_score >= 50:
        return "Fair fit"
    else:
        return "Poor fit"
