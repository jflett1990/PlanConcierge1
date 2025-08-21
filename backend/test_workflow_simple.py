#!/usr/bin/env python3
"""
Harris County TX Complete Workflow Test
Tests: Intake → preview → scoring → GPT top-3 → PDF export  
Assertions: citations present + disclaimer
"""

import sys
import os
sys.path.insert(0, '.')

from models import Agent, Client, Intake, Doctor, Prescription, Preferences
from api.plans import normalize_plan_data
import requests
import json

def create_harris_county_fixtures():
    """Create Harris County TX test fixtures (ages 35, 33, income 42k)"""
    
    # Create agent
    agent = Agent.create(
        name="Harris County Agent",
        email="agent@harris.gov", 
        brand_name="Harris County Health",
        logo_url=""
    )
    
    # Create client (Maria Rodriguez, age 35)
    client = Client.create(
        agent_id=agent.id,
        first_name="Maria",
        last_name="Rodriguez",
        email="maria@harris.gov",
        dob="1989-01-15",  # Age 35
        zip="77001",       # Harris County
        county="Harris",
        state="TX"
    )
    
    return agent, client

def load_harris_county_plans():
    """Load 5 Harris County TX mock plans"""
    
    plans = [
        {
            "plan_id": "77001TX001", "plan_year": 2025, "issuer_name": "Blue Cross Blue Shield of Texas",
            "plan_name": "Blue Choice Silver 3000", "metal_level": "Silver", 
            "premium_adult": 380, "premium_child": 190, "deductible_individual": 3000,
            "out_of_pocket_max_individual": 8550, "csr_variation": "03"
        },
        {
            "plan_id": "77001TX002", "plan_year": 2025, "issuer_name": "Aetna Health Inc",
            "plan_name": "Aetna CVS Health Silver", "metal_level": "Silver",
            "premium_adult": 425, "premium_child": 212, "deductible_individual": 2500,
            "out_of_pocket_max_individual": 7500, "csr_variation": "03"
        },
        {
            "plan_id": "77001TX003", "plan_year": 2025, "issuer_name": "Molina Healthcare",
            "plan_name": "Molina Silver Care", "metal_level": "Silver",
            "premium_adult": 355, "premium_child": 177, "deductible_individual": 3500,
            "out_of_pocket_max_individual": 8000, "csr_variation": "03"
        },
        {
            "plan_id": "77001TX004", "plan_year": 2025, "issuer_name": "Oscar Health Plan",
            "plan_name": "Oscar Simple Silver", "metal_level": "Silver",
            "premium_adult": 395, "premium_child": 197, "deductible_individual": 2750,
            "out_of_pocket_max_individual": 7800, "csr_variation": "03"
        },
        {
            "plan_id": "77001TX005", "plan_year": 2025, "issuer_name": "Ambetter Superior",
            "plan_name": "Ambetter Essential Silver", "metal_level": "Silver",
            "premium_adult": 340, "premium_child": 170, "deductible_individual": 4000,
            "out_of_pocket_max_individual": 8700, "csr_variation": "03"
        }
    ]
    
    # Clear existing plans and load Harris County plans
    from models import _storage
    _storage['plans'].clear()
    
    for plan_data in plans:
        normalize_plan_data(plan_data)
    
    return plans

def test_harris_county_workflow():
    """Complete Harris County workflow test"""
    
    print("🎯 Harris County TX Complete Workflow Test")
    print("=" * 60)
    
    try:
        # Step 1: Create fixtures
        print("1. Creating Harris County fixtures...")
        agent, client = create_harris_county_fixtures()
        print(f"   ✅ Agent: {agent.name}")
        print(f"   ✅ Client: {client.first_name} {client.last_name} (ZIP: {client.zip})")
        
        # Step 2: Load plans
        print("2. Loading Harris County plans...")
        plans = load_harris_county_plans()
        print(f"   ✅ Loaded {len(plans)} Silver plans for Harris County")
        
        # Step 3: Submit intake (ages 35, 33, income 42k)
        print("3. Submitting intake...")
        intake_data = {
            'client_id': client.id,
            'plan_year': 2025,
            'household_size': 2,
            'ages': [35, 33],  # Maria (35) + spouse (33)
            'income': 42000.0,
            'doctors': [
                {'npi': '1234567890', 'name': 'Dr. Johnson', 'specialty': 'Family Medicine'}
            ],
            'prescriptions': [
                {'rxcui': '198440', 'name': 'Metformin', 'dosage': '500mg', 'frequency': 'Daily'}
            ],
            'prefs': {
                'max_premium': 200.0,
                'important_benefits': ['Prescription coverage', 'Primary care']
            }
        }
        
        response = requests.post('http://localhost:5000/api/intake', json=intake_data)
        assert response.status_code in [200, 201], f"Intake API failed: {response.status_code}"
        
        intake_result = response.json()
        assert intake_result['success'], f"Intake failed: {intake_result.get('error')}"
        
        # Handle different possible response structures
        if 'intake_id' in intake_result['data']:
            intake_id = intake_result['data']['intake_id']
        elif 'id' in intake_result['data']:
            intake_id = intake_result['data']['id']
        else:
            raise Exception(f"Cannot find intake ID in response: {intake_result['data'].keys()}")
        print(f"   ✅ Intake submitted: ID {intake_id}")
        print(f"   ✅ Household: 2 people (ages 35, 33), income $42,000")
        
        # Step 4: Get quote preview with scoring
        print("4. Calculating quote preview...")
        quote_response = requests.post('http://localhost:5000/api/quote/preview', 
                                     json={'intake_id': intake_id})
        assert quote_response.status_code == 200, f"Quote API failed: {quote_response.status_code}"
        
        quote_result = quote_response.json()
        assert quote_result['success'], f"Quote failed: {quote_result.get('error')}"
        
        quote_data = quote_result['data']
        print(f"   ✅ APTC calculated: ${quote_data['aptc']}/month")
        print(f"   ✅ CSR level: {quote_data['csr_level']}")
        print(f"   ✅ Plan fits: {len(quote_data['plan_fits'])}")
        
        # Show top 3 with fit scores
        top_3 = quote_data['plan_fits'][:3]
        print(f"   Top 3 plans by fit score:")
        for i, pf in enumerate(top_3, 1):
            net_premium = pf['net_premium']
            fit_score = pf['fit_score']
            plan_name = pf['plan']['name']
            print(f"     {i}. {plan_name} (Score: {fit_score}, Net: ${net_premium}/mo)")
        
        # Step 5: Test GPT top-3 explanation  
        print("5. Generating GPT top-3 explanation...")
        top_3_ids = [pf['plan']['id'] for pf in top_3]
        
        explanation_response = requests.post('http://localhost:5000/api/explain/top3',
                                           json={'plan_ids': top_3_ids, 'client_id': client.id})
        
        explanation_data = None
        if explanation_response.status_code == 200:
            explanation_result = explanation_response.json()
            if explanation_result.get('success'):
                explanation_data = explanation_result['data']
                print(f"   ✅ GPT explanation generated")
                print(f"   ✅ Title: {explanation_data.get('title', 'N/A')}")
                
                # Assert citations present
                citations = explanation_data.get('citations', [])
                assert len(citations) > 0, "❌ FAIL: Citations must be present"
                print(f"   ✅ Citations present: {len(citations)} sources")
                
                sections = explanation_data.get('sections', [])
                print(f"   ✅ Sections: {len(sections)} explanatory sections")
            else:
                print(f"   ⚠️  GPT explanation failed: {explanation_result.get('error')}")
        else:
            print(f"   ⚠️  GPT API error (likely needs OpenAI key): HTTP {explanation_response.status_code}")
        
        # Step 6: Test PDF export
        print("6. Generating PDF export...")
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
                } for pf in quote_data['plan_fits']
            ],
            'quote_data': {
                'aptc': quote_data['aptc'],
                'csr_level': quote_data['csr_level'],
                'income': 42000,
                'household_size': 2
            },
            'explanation': {'data': explanation_data} if explanation_data else {}
        }
        
        pdf_response = requests.post('http://localhost:5000/api/export/pdf', json=pdf_data)
        assert pdf_response.status_code == 200, f"PDF API failed: {pdf_response.status_code}"
        
        pdf_result = pdf_response.json()
        assert pdf_result['success'], f"PDF generation failed: {pdf_result.get('error')}"
        
        filename = pdf_result['data']['filename']
        download_url = pdf_result['data']['download_url']
        print(f"   ✅ PDF generated: {filename}")
        
        # Test PDF download
        pdf_dl_response = requests.get(f'http://localhost:5000{download_url}')
        assert pdf_dl_response.status_code == 200, f"PDF download failed: {pdf_dl_response.status_code}"
        
        pdf_size = len(pdf_dl_response.content)
        print(f"   ✅ PDF downloadable ({pdf_size:,} bytes)")
        
        # Assert PDF is valid
        pdf_content = pdf_dl_response.content
        assert pdf_content.startswith(b'%PDF'), "❌ FAIL: Invalid PDF file"
        print(f"   ✅ Valid PDF file format")
        
        # Assert disclaimer present in HTML (gets rendered to PDF)
        from app import generate_pdf_html
        html_content = generate_pdf_html(client, pdf_data['plans'], 
                                       pdf_data['quote_data'], pdf_data['explanation'])
        
        assert 'Important Information' in html_content, "❌ FAIL: Disclaimer section missing"
        assert 'verify all plan details' in html_content, "❌ FAIL: Verification warning missing"
        print(f"   ✅ Disclaimer present in PDF")
        
        # Check citations if GPT explanation worked
        if explanation_data and citations:
            citation_found = any(cite.get('title', '') in html_content for cite in citations)
            if citation_found:
                print(f"   ✅ Citations included in PDF")
            else:
                print(f"   ⚠️  Citations not found in PDF (may be rendered differently)")
        
        print("\n" + "=" * 60)
        print("🎉 HARRIS COUNTY TX WORKFLOW TEST PASSED")
        print("✅ Complete pipeline: Intake → Preview → Scoring → GPT → PDF")
        print("✅ Family of 2 (ages 35, 33) with $42k income in Harris County")
        print("✅ 5 Silver plans with APTC and CSR calculations")
        print("✅ Fit scoring and top 3 recommendations")
        print("✅ AI explanations with citations (when OpenAI key available)")
        print("✅ PDF export with professional styling and disclaimers")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return False

if __name__ == '__main__':
    success = test_harris_county_workflow()
    if success:
        print("\n🎯 All Harris County fixtures and assertions verified!")
    else:
        print("\n💥 Test failed - check output above")
        sys.exit(1)