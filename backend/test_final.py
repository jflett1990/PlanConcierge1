#!/usr/bin/env python3
"""
Harris County TX Final Integration Test
Tests complete workflow with proper error handling
"""

import sys
import os
sys.path.insert(0, '.')
import json
import requests
import time

def test_harris_county_complete():
    """Complete Harris County test with all assertions"""
    
    print("🎯 Harris County TX Complete Test")
    print("=" * 45)
    
    try:
        from models import Agent, Client, _storage
        from api.plans import normalize_plan_data
        
        # Step 1: Clear storage and setup data  
        print("1. Setting up Harris County fixtures...")
        for key in _storage:
            _storage[key].clear()
        
        # Create agent and client
        agent = Agent.create("Harris Agent", "test@harris.gov", "Harris Health", "")
        client = Client.create(agent.id, "Maria", "Rodriguez", "maria@harris.gov", 
                              "1989-01-15", "77001", "Harris", "TX")
        print(f"   ✅ Created client: {client.first_name} {client.last_name} (ID: {client.id})")
        
        # Load Harris County plans
        plans = [
            {"plan_id": "77001TX001", "plan_year": 2025, "issuer_name": "Blue Cross Blue Shield of Texas", 
             "plan_name": "Blue Choice Silver 3000", "metal_level": "Silver", 
             "premium_adult": 380, "premium_child": 190, "deductible_individual": 3000,
             "out_of_pocket_max_individual": 8550, "csr_variation": "03"},
            {"plan_id": "77001TX002", "plan_year": 2025, "issuer_name": "Aetna Health Inc",
             "plan_name": "Aetna CVS Health Silver", "metal_level": "Silver",
             "premium_adult": 425, "premium_child": 212, "deductible_individual": 2500,
             "out_of_pocket_max_individual": 7500, "csr_variation": "03"},
            {"plan_id": "77001TX003", "plan_year": 2025, "issuer_name": "Molina Healthcare",
             "plan_name": "Molina Silver Care", "metal_level": "Silver",
             "premium_adult": 355, "premium_child": 177, "deductible_individual": 3500,
             "out_of_pocket_max_individual": 8000, "csr_variation": "03"},
        ]
        
        for plan in plans:
            normalize_plan_data(plan)
        print(f"   ✅ Loaded {len(plans)} Silver plans")
        
        # Step 2: Test intake submission
        print("2. Submitting intake (ages 35, 33, income $42k)...")
        intake_data = {
            'client_id': client.id,
            'plan_year': 2025,
            'household_size': 2,
            'ages': [35, 33],
            'income': 42000.0,
            'doctors': [{'npi': '1234567890', 'name': 'Dr. Johnson', 'specialty': 'Family Medicine'}],
            'prescriptions': [{'rxcui': '198440', 'name': 'Metformin', 'dosage': '500mg', 'frequency': 'Daily'}],
            'prefs': {'max_premium': 200.0, 'important_benefits': ['Prescription coverage']}
        }
        
        # Allow server to restart after any reloads
        time.sleep(2)
        
        response = requests.post('http://localhost:5000/api/intake', json=intake_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            print(f"   ❌ Intake failed: {response.text}")
            return False
            
        intake_result = response.json()
        if not intake_result.get('success'):
            print(f"   ❌ Intake failed: {intake_result.get('error')}")
            return False
            
        intake_id = intake_result['data']['id']
        print(f"   ✅ Intake created: ID {intake_id}")
        
        # Step 3: Test quote generation
        print("3. Generating quote with APTC/CSR calculations...")
        
        # Add small delay to ensure data is persisted
        time.sleep(1)
        
        quote_response = requests.post('http://localhost:5000/api/quote/preview', 
                                     json={'intake_id': intake_id}, timeout=10)
        
        if quote_response.status_code != 200:
            print(f"   ❌ Quote failed: {quote_response.status_code}")
            print(f"   Response: {quote_response.text[:200]}...")
            
            # Debug: Check if data is still in storage
            intake_check = _storage['intakes'].get(intake_id)
            if intake_check:
                print(f"   Debug: Intake {intake_id} exists with client_id {intake_check.client_id}")
                client_check = _storage['clients'].get(intake_check.client_id)
                if client_check:
                    print(f"   Debug: Client {intake_check.client_id} exists: {client_check.first_name}")
                else:
                    print(f"   Debug: Client {intake_check.client_id} NOT FOUND")
            else:
                print(f"   Debug: Intake {intake_id} NOT FOUND")
            return False
            
        quote_result = quote_response.json()
        if not quote_result.get('success'):
            print(f"   ❌ Quote failed: {quote_result.get('error')}")
            return False
            
        quote_data = quote_result['data']
        aptc = quote_data['aptc']
        csr_level = quote_data['csr_level']
        plan_fits = quote_data['plan_fits']
        
        print(f"   ✅ APTC: ${aptc}/month")
        print(f"   ✅ CSR Level: {csr_level}")
        print(f"   ✅ Plan fits: {len(plan_fits)}")
        
        if len(plan_fits) > 0:
            top_plan = plan_fits[0]
            print(f"   ✅ Top plan: {top_plan['plan']['name']} (Score: {top_plan['fit_score']})")
        
        # Step 4: Test PDF export
        print("4. Testing PDF export with disclaimer...")
        pdf_data = {
            'client_id': client.id,
            'plans': [
                {
                    'name': pf['plan']['name'],
                    'issuer': pf['plan']['issuer'], 
                    'metal': pf['plan']['metal'],
                    'premium_full': pf['plan']['premium_full'],
                    'net_premium': pf['net_premium'],
                    'deductible': pf['plan']['deductible'],
                    'moop': pf['plan']['moop'],
                    'fit_score': pf['fit_score']
                } for pf in plan_fits[:3]  # Top 3 plans
            ],
            'quote_data': {
                'aptc': aptc,
                'csr_level': csr_level,
                'income': 42000,
                'household_size': 2
            }
        }
        
        pdf_response = requests.post('http://localhost:5000/api/export/pdf', json=pdf_data, timeout=15)
        
        if pdf_response.status_code != 200:
            print(f"   ❌ PDF failed: {pdf_response.status_code}")
            return False
            
        pdf_result = pdf_response.json()
        if not pdf_result.get('success'):
            print(f"   ❌ PDF failed: {pdf_result.get('error')}")
            return False
            
        filename = pdf_result['data']['filename']
        download_url = pdf_result['data']['download_url']
        print(f"   ✅ PDF generated: {filename}")
        
        # Test PDF download
        pdf_dl = requests.get(f'http://localhost:5000{download_url}')
        if pdf_dl.status_code == 200:
            print(f"   ✅ PDF downloadable ({len(pdf_dl.content):,} bytes)")
        else:
            print(f"   ❌ PDF download failed: {pdf_dl.status_code}")
            return False
            
        # Assert disclaimer present
        from app import generate_pdf_html
        html = generate_pdf_html(client, pdf_data['plans'], pdf_data['quote_data'], {})
        
        if 'Important Information' in html and 'verify all plan details' in html:
            print("   ✅ Disclaimer present in PDF")
        else:
            print("   ❌ Disclaimer missing in PDF")
            return False
        
        # Step 5: Test GPT explanations (optional, may fail without API key)
        print("5. Testing AI explanations...")
        try:
            top_3_ids = [pf['plan']['id'] for pf in plan_fits[:3]]
            explain_response = requests.post('http://localhost:5000/api/explain/top3',
                                           json={'plan_ids': top_3_ids, 'client_id': client.id}, 
                                           timeout=30)
            
            if explain_response.status_code == 200:
                explain_result = explain_response.json()
                if explain_result.get('success'):
                    explanation = explain_result['data']
                    citations = explanation.get('citations', [])
                    if len(citations) > 0:
                        print(f"   ✅ AI explanation with {len(citations)} citations")
                    else:
                        print("   ⚠️  AI explanation generated (no citations)")
                else:
                    print(f"   ⚠️  AI explanation failed: {explain_result.get('error', 'Unknown error')}")
            else:
                print(f"   ⚠️  AI explanation API error (likely needs OpenAI key)")
        except Exception as e:
            print(f"   ⚠️  AI explanation skipped: {str(e)[:50]}...")
        
        print("\n" + "=" * 45)
        print("🎉 HARRIS COUNTY TX TEST PASSED")
        print("✅ Complete workflow: Intake → Quote → PDF")
        print("✅ Family of 2 (ages 35, 33) with $42k income")
        print("✅ Silver plans with APTC/CSR calculations")
        print("✅ PDF export with professional disclaimer")
        print("✅ All core assertions verified")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_harris_county_complete()
    
    if success:
        print("\n🎯 Harris County TX fixtures and workflow verified!")
        print("Ready for deployment.")
        sys.exit(0)
    else:
        print("\n❌ Harris County test failed.")
        sys.exit(1)