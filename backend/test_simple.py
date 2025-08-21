#!/usr/bin/env python3
"""
Minimal Harris County TX test to verify complete workflow
"""
import sys
import os
sys.path.insert(0, '.')

from models import Agent, Client, _storage
from api.plans import normalize_plan_data
import requests

print("🎯 Harris County TX Minimal Test")
print("=" * 40)

# Clear storage and create minimal data
for key in _storage:
    _storage[key].clear()

# Create agent and client
agent = Agent.create("Test Agent", "test@example.com", "Test Brand", "")
client = Client.create(agent.id, "Maria", "Rodriguez", "maria@example.com", 
                      "1989-01-15", "77001", "Harris", "TX")
print(f"✅ Created: {client.first_name} {client.last_name} in {client.county} County")

# Load one plan
plan_data = {
    "plan_id": "77001TX001", "plan_year": 2025, "issuer_name": "Blue Cross Blue Shield of Texas",
    "plan_name": "Blue Choice Silver 3000", "metal_level": "Silver", 
    "premium_adult": 380, "premium_child": 190, "deductible_individual": 3000,
    "out_of_pocket_max_individual": 8550, "csr_variation": "03"
}
normalize_plan_data(plan_data)
print(f"✅ Loaded: {plan_data['plan_name']}")

# Test intake API
intake_data = {
    'client_id': client.id,
    'plan_year': 2025,
    'household_size': 2,
    'ages': [35, 33],
    'income': 42000.0,
    'doctors': [],
    'prescriptions': [],
    'prefs': {}
}

response = requests.post('http://localhost:5000/api/intake', json=intake_data)
if response.status_code in [200, 201]:
    result = response.json()
    if result['success']:
        intake_id = result['data']['id']
        print(f"✅ Intake: ID {intake_id} (ages 35,33, income $42k)")
        
        # Test quote API
        quote_response = requests.post('http://localhost:5000/api/quote/preview', 
                                     json={'intake_id': intake_id})
        if quote_response.status_code == 200:
            quote_result = quote_response.json()
            if quote_result['success']:
                quote_data = quote_result['data']
                aptc = quote_data['aptc']
                plan_fits = quote_data['plan_fits']
                print(f"✅ Quote: APTC ${aptc}, {len(plan_fits)} plans")
                
                if plan_fits:
                    best_plan = plan_fits[0]
                    print(f"✅ Best: {best_plan['plan']['name']} (Score: {best_plan['fit_score']}, Net: ${best_plan['net_premium']})")
                
                # Test PDF
                pdf_data = {
                    'client_id': client.id,
                    'plans': [{
                        'name': best_plan['plan']['name'],
                        'issuer': best_plan['plan']['issuer'],
                        'metal': best_plan['plan']['metal'],
                        'premium_full': best_plan['plan']['premium_full'],
                        'net_premium': best_plan['net_premium'],
                        'deductible': best_plan['plan']['deductible'],
                        'moop': best_plan['plan']['moop'],
                        'fit_score': best_plan['fit_score']
                    }],
                    'quote_data': {
                        'aptc': aptc,
                        'csr_level': quote_data['csr_level'],
                        'income': 42000,
                        'household_size': 2
                    }
                }
                
                pdf_response = requests.post('http://localhost:5000/api/export/pdf', json=pdf_data)
                if pdf_response.status_code == 200:
                    pdf_result = pdf_response.json()
                    if pdf_result['success']:
                        filename = pdf_result['data']['filename']
                        print(f"✅ PDF: {filename}")
                        
                        # Verify disclaimer
                        from app import generate_pdf_html
                        html = generate_pdf_html(client, pdf_data['plans'], 
                                               pdf_data['quote_data'], {})
                        
                        if 'Important Information' in html and 'verify all plan details' in html:
                            print("✅ Disclaimer: Present in PDF")
                            
                            print("\n" + "=" * 40)
                            print("🎉 SUCCESS: Complete workflow verified")
                            print("✅ Harris County TX family (ages 35, 33, income $42k)")
                            print("✅ Intake → Quote → PDF with disclaimer")
                            print("✅ All assertions passed")
                        else:
                            print("❌ Disclaimer missing")
                    else:
                        print(f"❌ PDF failed: {pdf_result.get('error')}")
                else:
                    print(f"❌ PDF API failed: {pdf_response.status_code}")
            else:
                print(f"❌ Quote failed: {quote_result.get('error')}")
        else:
            print(f"❌ Quote API failed: {quote_response.status_code}")
            print(f"   Response: {quote_response.text[:100]}...")
    else:
        print(f"❌ Intake failed: {result.get('error')}")
else:
    print(f"❌ Intake API failed: {response.status_code}")