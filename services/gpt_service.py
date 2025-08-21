"""OpenAI GPT service for plan explanations"""
import json
import os
from openai import OpenAI
from models import HCGovContent

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def search_hcgov_content(query):
    """Search HC.gov content for relevant information"""
    return HCGovContent.search(query)

def generate_plan_explanation(intake_data, top_3_plans, aptc, csr_level):
    """Generate plain-English explanation of top 3 plan recommendations"""
    
    if not client:
        return generate_fallback_explanation(intake_data, top_3_plans, aptc, csr_level)
    
    # Search for relevant HC.gov content
    search_terms = ["premium", "deductible", "out of pocket maximum", "network", "formulary"]
    hc_content = []
    for term in search_terms:
        results = search_hcgov_content(term)
        hc_content.extend(results[:2])  # Take top 2 results per term
    
    # Prepare context for GPT
    context = {
        "client_info": {
            "household_size": intake_data.get('household_size'),
            "ages": intake_data.get('ages'),
            "income": intake_data.get('income'),
            "location": f"{intake_data.get('county', 'Unknown')}, {intake_data.get('state', 'Unknown')}",
            "doctors": len(intake_data.get('doctors', [])),
            "prescriptions": len(intake_data.get('prescriptions', []))
        },
        "financial_assistance": {
            "aptc": aptc,
            "csr_level": csr_level
        },
        "top_plans": []
    }
    
    for i, plan_fit in enumerate(top_3_plans):
        plan = plan_fit['plan']
        context["top_plans"].append({
            "rank": i + 1,
            "issuer": plan['issuer'],
            "name": plan['name'],
            "metal": plan['metal'],
            "premium_full": plan['premium_full'],
            "net_premium": plan_fit['net_premium'],
            "deductible": plan['deductible'],
            "moop": plan['moop'],
            "fit_score": plan_fit['fit_score'],
            "rationale": plan_fit['rationale']
        })
    
    system_prompt = """You are a licensed health insurance agent helping clients understand their ACA marketplace options. 
    
    Your task is to explain the top 3 recommended plans in clear, client-friendly language. Include:
    1. A brief summary of each plan's key features
    2. Why each plan was recommended based on their specific situation
    3. Trade-offs between the plans
    4. At least 2 citations to Healthcare.gov definitions or explanations
    5. Clear next steps for enrollment
    
    Use the HC.gov content provided to ensure accurate definitions. Always include the required disclaimer about network and formulary changes.
    
    Respond in JSON format with this structure:
    {
        "summary": "Brief overview paragraph",
        "plan_explanations": [
            {
                "rank": 1,
                "title": "Plan name and why it's recommended",
                "explanation": "Detailed explanation",
                "pros": ["list", "of", "advantages"],
                "cons": ["list", "of", "disadvantages"]
            }
        ],
        "comparison": "Key differences between the plans",
        "citations": [
            {
                "term": "Premium",
                "definition": "Definition from HC.gov",
                "source_url": "URL"
            }
        ],
        "next_steps": "What the client should do next",
        "disclaimer": "Required compliance disclaimer"
    }"""
    
    user_prompt = f"""
    Based on this client information and plan data, generate a comprehensive explanation:
    
    CLIENT CONTEXT:
    {json.dumps(context, indent=2)}
    
    HC.GOV REFERENCE CONTENT:
    {json.dumps(hc_content, indent=2)}
    
    Please provide a clear, professional explanation that helps the client understand their options.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"GPT service error: {e}")
        return generate_fallback_explanation(intake_data, top_3_plans, aptc, csr_level)

def generate_fallback_explanation(intake_data, top_3_plans, aptc, csr_level):
    """Fallback explanation when GPT is not available"""
    
    explanations = []
    for i, plan_fit in enumerate(top_3_plans):
        plan = plan_fit['plan']
        explanations.append({
            "rank": i + 1,
            "title": f"{plan['issuer']} {plan['name']} - {plan_fit['rationale']['overall_rating']}",
            "explanation": f"This {plan['metal'].lower()} plan offers a monthly premium of ${plan_fit['net_premium']:.2f} after your ${aptc:.2f} tax credit. With a ${plan['deductible']:,} deductible and ${plan['moop']:,} out-of-pocket maximum, it provides {plan_fit['rationale']['overall_rating'].lower()} value for your situation.",
            "pros": [
                f"${plan_fit['net_premium']:.2f}/month after tax credits",
                f"{plan_fit['rationale']['doctor_network']}",
                f"{plan_fit['rationale']['prescription_coverage']}"
            ],
            "cons": [
                f"${plan['deductible']:,} annual deductible",
                f"${plan['moop']:,} out-of-pocket maximum"
            ]
        })
    
    citations = [
        {
            "term": "Premium",
            "definition": "The amount you pay for your health insurance every month.",
            "source_url": "https://www.healthcare.gov/glossary/premium/"
        },
        {
            "term": "Deductible", 
            "definition": "The amount you pay for covered health care services before your insurance plan starts to pay.",
            "source_url": "https://www.healthcare.gov/glossary/deductible/"
        }
    ]
    
    return {
        "summary": f"Based on your household income of ${intake_data['income']:,} and family size of {intake_data['household_size']}, you qualify for ${aptc:.2f}/month in premium tax credits. Here are your top 3 recommended plans:",
        "plan_explanations": explanations,
        "comparison": "These plans balance different trade-offs between monthly premiums and out-of-pocket costs. Higher metal tiers (Gold, Platinum) have higher premiums but lower deductibles.",
        "citations": citations,
        "next_steps": "Review these recommendations with your agent and enroll during the open enrollment period or after a qualifying life event.",
        "disclaimer": "Networks and formularies change. Verify provider and prescription coverage at enrollment. This analysis is based on 2024 plan data and current federal poverty level guidelines."
    }

def generate_soa_content(intake_data, quote_result, client_info):
    """Generate Statement of Advice content"""
    
    return {
        "client_name": f"{client_info['first_name']} {client_info['last_name']}",
        "agent_name": "Agent Demo",
        "date": "Current Date",
        "analysis_summary": "Based on client needs assessment, recommended top 3 ACA marketplace plans",
        "methodology": "Used weighted fit score algorithm considering premium affordability, out-of-pocket costs, provider network, and prescription coverage",
        "recommendations": f"Top recommendation: {quote_result['top_3'][0]['plan']['name']} with fit score of {quote_result['top_3'][0]['fit_score']}",
        "compliance_notes": "All recommendations based on client-provided information. Networks and formularies subject to change."
    }
