"""
Provider Network and Formulary Integration Module

This module provides interfaces to check provider network participation
and prescription drug formulary coverage for insurance plans.

For MVP, returns randomized mock values to simulate real provider/formulary APIs.
"""

import random
import hashlib
from typing import List, Dict, Any, Tuple

def _seed_random(plan_id: str, identifier: str) -> None:
    """Seed random generator for consistent mock results per plan/provider combo"""
    seed_str = f"{plan_id}_{identifier}"
    seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    random.seed(seed_hash)

def check_providers(plan_ids: List[str], npi_list: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Check provider network participation for given plans
    
    Args:
        plan_ids: List of plan IDs to check
        npi_list: List of provider NPIs to check
    
    Returns:
        Dictionary mapping plan_id to list of provider match results
        
    Example:
        {
            "plan_id_1": [
                {
                    "npi": "1234567890",
                    "name": "Dr. Smith",
                    "specialty": "Primary Care",
                    "in_network": True,
                    "tier": "preferred",
                    "copay": 25.0,
                    "distance_miles": 2.3
                }
            ]
        }
    """
    results = {}
    
    # Mock network participation rates by plan type
    network_rates = {
        "HMO": 0.75,      # HMOs typically have more restricted networks
        "PPO": 0.85,      # PPOs have broader networks
        "EPO": 0.80       # EPOs are in between
    }
    
    for plan_id in plan_ids:
        plan_results = []
        
        # Determine plan type from plan_id (mock logic)
        plan_type = "HMO"
        if "PPO" in plan_id.upper():
            plan_type = "PPO"
        elif "EPO" in plan_id.upper():
            plan_type = "EPO"
        
        base_rate = network_rates.get(plan_type, 0.80)
        
        for npi in npi_list:
            _seed_random(plan_id, npi)
            
            # Randomized network participation
            in_network = random.random() < base_rate
            
            # Mock provider details (would come from provider directory API)
            provider_names = [
                "Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez",
                "Dr. David Kim", "Dr. Lisa Thompson", "Dr. James Wilson",
                "Dr. Maria Garcia", "Dr. Robert Brown", "Dr. Jennifer Lee"
            ]
            
            specialties = [
                "Primary Care", "Internal Medicine", "Family Medicine",
                "Cardiology", "Dermatology", "Orthopedics", "Gastroenterology",
                "Endocrinology", "Neurology", "Psychiatry"
            ]
            
            # Generate consistent mock data
            name_index = int(hashlib.md5(npi.encode()).hexdigest()[:2], 16) % len(provider_names)
            specialty_index = int(hashlib.md5(npi.encode()).hexdigest()[2:4], 16) % len(specialties)
            
            provider_result = {
                "npi": npi,
                "name": provider_names[name_index],
                "specialty": specialties[specialty_index],
                "in_network": in_network
            }
            
            if in_network:
                # Add network-specific details
                provider_result.update({
                    "tier": random.choice(["preferred", "standard", "specialty"]),
                    "copay": random.choice([15.0, 25.0, 35.0, 50.0]),
                    "distance_miles": round(random.uniform(0.5, 15.0), 1)
                })
            else:
                # Out-of-network details
                provider_result.update({
                    "tier": "out_of_network",
                    "copay": None,
                    "distance_miles": round(random.uniform(0.5, 25.0), 1),
                    "out_of_network_coverage": random.choice([True, False])
                })
            
            plan_results.append(provider_result)
        
        results[plan_id] = plan_results
    
    return results

def check_rx(plan_ids: List[str], rx_list: List[Dict[str, str]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Check prescription drug formulary coverage for given plans
    
    Args:
        plan_ids: List of plan IDs to check
        rx_list: List of prescriptions with rxcui, name, dosage, frequency
    
    Returns:
        Dictionary mapping plan_id to list of formulary match results
        
    Example:
        {
            "plan_id_1": [
                {
                    "rxcui": "123456",
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "Daily",
                    "covered": True,
                    "tier": 1,
                    "copay": 10.0,
                    "prior_auth_required": False,
                    "quantity_limit": None,
                    "alternatives": ["Enalapril", "Captopril"]
                }
            ]
        }
    """
    results = {}
    
    # Mock formulary coverage rates by drug tier
    coverage_rates = {
        "generic": 0.95,      # Generic drugs typically well covered
        "brand": 0.75,        # Brand drugs less coverage
        "specialty": 0.60     # Specialty drugs most restrictions
    }
    
    # Common drug categories for tier assignment
    generic_drugs = {
        "lisinopril", "metformin", "atorvastatin", "amlodipine", "omeprazole",
        "losartan", "gabapentin", "hydrochlorothiazide", "sertraline", "tramadol"
    }
    
    specialty_drugs = {
        "humira", "enbrel", "remicade", "rituxan", "herceptin", "avastin",
        "tecfidera", "copaxone", "gilenya", "tysabri"
    }
    
    for plan_id in plan_ids:
        plan_results = []
        
        for rx in rx_list:
            rxcui = rx.get("rxcui", "")
            name = rx.get("name", "").lower()
            dosage = rx.get("dosage", "")
            frequency = rx.get("frequency", "")
            
            _seed_random(plan_id, rxcui)
            
            # Determine drug tier
            if name in generic_drugs:
                drug_tier = "generic"
                tier_num = 1
            elif name in specialty_drugs:
                drug_tier = "specialty"
                tier_num = 4
            else:
                drug_tier = "brand"
                tier_num = random.choice([2, 3])
            
            # Check coverage based on tier
            base_rate = coverage_rates.get(drug_tier, 0.80)
            covered = random.random() < base_rate
            
            rx_result = {
                "rxcui": rxcui,
                "name": rx.get("name", ""),
                "dosage": dosage,
                "frequency": frequency,
                "covered": covered
            }
            
            if covered:
                # Add formulary details for covered drugs
                copay_by_tier = {1: 10.0, 2: 30.0, 3: 60.0, 4: 150.0}
                
                rx_result.update({
                    "tier": tier_num,
                    "copay": copay_by_tier.get(tier_num, 50.0),
                    "prior_auth_required": random.random() < (0.1 if tier_num <= 2 else 0.4),
                    "quantity_limit": random.choice([None, "30 day supply", "90 day supply"]) if tier_num >= 3 else None,
                    "step_therapy_required": random.random() < 0.15
                })
                
                # Mock alternatives (would come from drug database)
                if drug_tier == "generic":
                    alternatives = random.sample(["Generic Alternative A", "Generic Alternative B"], 
                                               random.randint(0, 2))
                else:
                    alternatives = random.sample(["Brand Alternative X", "Generic Equivalent Y"], 
                                               random.randint(0, 2))
                rx_result["alternatives"] = alternatives
                
            else:
                # Not covered - provide alternatives
                rx_result.update({
                    "tier": None,
                    "copay": None,
                    "prior_auth_required": False,
                    "coverage_reason": random.choice([
                        "Not on formulary",
                        "Medical exception required", 
                        "Age restriction",
                        "Diagnosis restriction"
                    ])
                })
                
                # Suggest covered alternatives
                alternatives = random.sample([
                    f"Covered Alternative for {rx.get('name', 'medication')} A",
                    f"Covered Alternative for {rx.get('name', 'medication')} B"
                ], random.randint(1, 2))
                rx_result["alternatives"] = alternatives
            
            plan_results.append(rx_result)
        
        results[plan_id] = plan_results
    
    return results

def get_provider_summary(provider_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for provider network results"""
    if not provider_results:
        return {"in_network_count": 0, "total_count": 0, "coverage_rate": 0.0}
    
    in_network = sum(1 for p in provider_results if p.get("in_network", False))
    total = len(provider_results)
    
    return {
        "in_network_count": in_network,
        "total_count": total,
        "coverage_rate": round(in_network / total, 2) if total > 0 else 0.0,
        "preferred_providers": sum(1 for p in provider_results 
                                 if p.get("tier") == "preferred"),
        "avg_copay": round(sum(p.get("copay", 0) for p in provider_results 
                             if p.get("copay")) / max(1, in_network), 2) if in_network > 0 else None
    }

def get_rx_summary(rx_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for formulary results"""
    if not rx_results:
        return {"covered_count": 0, "total_count": 0, "coverage_rate": 0.0}
    
    covered = sum(1 for rx in rx_results if rx.get("covered", False))
    total = len(rx_results)
    
    prior_auth = sum(1 for rx in rx_results if rx.get("prior_auth_required", False))
    
    return {
        "covered_count": covered,
        "total_count": total,
        "coverage_rate": round(covered / total, 2) if total > 0 else 0.0,
        "prior_auth_count": prior_auth,
        "avg_copay": round(sum(rx.get("copay", 0) for rx in rx_results 
                             if rx.get("copay")) / max(1, covered), 2) if covered > 0 else None,
        "tier_breakdown": {
            "tier_1": sum(1 for rx in rx_results if rx.get("tier") == 1),
            "tier_2": sum(1 for rx in rx_results if rx.get("tier") == 2),
            "tier_3": sum(1 for rx in rx_results if rx.get("tier") == 3),
            "tier_4": sum(1 for rx in rx_results if rx.get("tier") == 4)
        }
    }