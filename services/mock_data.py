"""Mock data service for ACA plans and provider/formulary data"""
from datetime import datetime

def get_mock_plans(zip_code, county, state, plan_year=2024):
    """Generate mock ACA plans for a given location"""
    plans = [
        {
            'id': 'plan_1',
            'plan_year': plan_year,
            'issuer': 'Blue Cross Blue Shield',
            'name': 'BCBS Silver Preferred',
            'metal': 'Silver',
            'premium_full': 450.00,
            'deductible': 3000,
            'moop': 8000,
            'csr_flag': True,
            'service_area': f"{county}, {state}",
            'benefits': {
                'primary_care': 30,
                'specialist': 60,
                'emergency_room': 400,
                'hospital': '20% after deductible'
            }
        },
        {
            'id': 'plan_2',
            'plan_year': plan_year,
            'issuer': 'Aetna',
            'name': 'Aetna Better Health Gold',
            'metal': 'Gold',
            'premium_full': 520.00,
            'deductible': 1500,
            'moop': 6000,
            'csr_flag': False,
            'service_area': f"{county}, {state}",
            'benefits': {
                'primary_care': 25,
                'specialist': 45,
                'emergency_room': 300,
                'hospital': '15% after deductible'
            }
        },
        {
            'id': 'plan_3',
            'plan_year': plan_year,
            'issuer': 'Humana',
            'name': 'Humana Bronze Essential',
            'metal': 'Bronze',
            'premium_full': 320.00,
            'deductible': 6000,
            'moop': 8500,
            'csr_flag': False,
            'service_area': f"{county}, {state}",
            'benefits': {
                'primary_care': '40% after deductible',
                'specialist': '40% after deductible',
                'emergency_room': '40% after deductible',
                'hospital': '40% after deductible'
            }
        },
        {
            'id': 'plan_4',
            'plan_year': plan_year,
            'issuer': 'Kaiser Permanente',
            'name': 'Kaiser Silver HMO',
            'metal': 'Silver',
            'premium_full': 475.00,
            'deductible': 2500,
            'moop': 7500,
            'csr_flag': True,
            'service_area': f"{county}, {state}",
            'benefits': {
                'primary_care': 25,
                'specialist': 50,
                'emergency_room': 350,
                'hospital': '20% after deductible'
            }
        },
        {
            'id': 'plan_5',
            'plan_year': plan_year,
            'issuer': 'Cigna',
            'name': 'Cigna Platinum Plus',
            'metal': 'Platinum',
            'premium_full': 650.00,
            'deductible': 500,
            'moop': 4500,
            'csr_flag': False,
            'service_area': f"{county}, {state}",
            'benefits': {
                'primary_care': 20,
                'specialist': 35,
                'emergency_room': 200,
                'hospital': '10% after deductible'
            }
        }
    ]
    
    return plans

def check_provider_network(plan_ids, doctor_npis):
    """Mock provider network checking"""
    results = {}
    
    for plan_id in plan_ids:
        plan_providers = []
        for npi in doctor_npis:
            # Mock logic: some plans cover some doctors
            in_network = hash(f"{plan_id}_{npi}") % 3 != 0  # ~67% in network
            plan_providers.append({
                'npi': npi,
                'in_network': in_network,
                'tier': 'preferred' if in_network else 'out_of_network'
            })
        results[plan_id] = plan_providers
    
    return results

def check_drug_formulary(plan_ids, drug_names):
    """Mock drug formulary checking"""
    results = {}
    
    # Common drug tiers and costs
    tier_info = {
        1: {'name': 'Generic', 'copay': 10},
        2: {'name': 'Preferred Brand', 'copay': 30},
        3: {'name': 'Non-Preferred Brand', 'copay': 60},
        4: {'name': 'Specialty', 'copay': 150}
    }
    
    for plan_id in plan_ids:
        plan_drugs = []
        for drug in drug_names:
            # Mock logic: assign tiers based on drug name hash
            tier = (hash(f"{plan_id}_{drug}") % 4) + 1
            covered = tier <= 3  # Tier 4 might not be covered by all plans
            
            plan_drugs.append({
                'drug_name': drug,
                'covered': covered,
                'tier': tier,
                'tier_name': tier_info[tier]['name'],
                'copay': tier_info[tier]['copay'] if covered else None,
                'prior_auth': tier >= 3,
                'step_therapy': tier == 4
            })
        results[plan_id] = plan_drugs
    
    return results

def calculate_aptc(household_income, household_size, ages, county, state):
    """Mock APTC calculation based on federal poverty level"""
    # 2024 Federal Poverty Level guidelines (simplified)
    fpl_base = 15060
    fpl_per_person = 5380
    fpl_amount = fpl_base + (fpl_per_person * (household_size - 1))
    
    income_percentage = (household_income / fpl_amount) * 100
    
    # APTC eligibility: 100% - 400% FPL
    if income_percentage < 100 or income_percentage > 400:
        return 0
    
    # Simplified APTC calculation
    # In reality, this would use complex benchmark plan calculations
    if income_percentage <= 150:
        contribution_percentage = 0.02  # 2% of income
    elif income_percentage <= 200:
        contribution_percentage = 0.04  # 4% of income
    elif income_percentage <= 250:
        contribution_percentage = 0.06  # 6% of income
    elif income_percentage <= 300:
        contribution_percentage = 0.08  # 8% of income
    else:
        contribution_percentage = 0.095  # 9.5% of income
    
    expected_contribution = household_income * contribution_percentage
    benchmark_premium = 450 * household_size  # Mock benchmark premium
    
    aptc = max(0, benchmark_premium - expected_contribution)
    return round(aptc / 12, 2)  # Monthly APTC

def determine_csr_level(household_income, household_size):
    """Determine Cost Sharing Reduction level"""
    fpl_base = 15060
    fpl_per_person = 5380
    fpl_amount = fpl_base + (fpl_per_person * (household_size - 1))
    
    income_percentage = (household_income / fpl_amount) * 100
    
    if income_percentage <= 150:
        return 'CSR_94'  # 94% actuarial value
    elif income_percentage <= 200:
        return 'CSR_87'  # 87% actuarial value
    elif income_percentage <= 250:
        return 'CSR_73'  # 73% actuarial value
    else:
        return None  # No CSR
