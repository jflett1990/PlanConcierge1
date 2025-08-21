from datetime import datetime
from typing import Dict, List, Optional
import uuid

# In-memory storage - will be replaced with PostgreSQL in Phase-2
storage = {
    'agents': {},
    'clients': {},
    'intakes': {},
    'plans': {},
    'quote_results': {},
    'plan_fits': {},
    'artifacts': {},
    'hcgov_content': {}
}

def init_storage():
    """Initialize storage with default agent and sample data"""
    global storage
    
    # Default agent
    agent_id = str(uuid.uuid4())
    storage['agents'][agent_id] = {
        'id': agent_id,
        'name': 'Agent Demo',
        'email': 'agent@plansconcierge.com',
        'brand_name': 'Plan Concierge',
        'logo_url': None,
        'created_at': datetime.now()
    }
    
    # Sample HC.gov content for RAG
    storage['hcgov_content']['glossary'] = [
        {
            'id': '1',
            'title': 'Premium',
            'url': 'https://www.healthcare.gov/glossary/premium/',
            'text': 'The amount you pay for your health insurance every month.',
            'type': 'glossary',
            'plan_year': 2024,
            'updated_at': datetime.now()
        },
        {
            'id': '2',
            'title': 'Deductible',
            'url': 'https://www.healthcare.gov/glossary/deductible/',
            'text': 'The amount you pay for covered health care services before your insurance plan starts to pay.',
            'type': 'glossary',
            'plan_year': 2024,
            'updated_at': datetime.now()
        },
        {
            'id': '3',
            'title': 'Advanced Premium Tax Credit (APTC)',
            'url': 'https://www.healthcare.gov/glossary/advanced-premium-tax-credit/',
            'text': 'A tax credit that can be used right away to lower monthly insurance premiums.',
            'type': 'glossary',
            'plan_year': 2024,
            'updated_at': datetime.now()
        }
    ]

class Agent:
    @staticmethod
    def get_default():
        agents = list(storage['agents'].values())
        return agents[0] if agents else None

class Client:
    @staticmethod
    def create(agent_id, first_name, last_name, email, dob, zip_code, county, state):
        client_id = str(uuid.uuid4())
        client = {
            'id': client_id,
            'agent_id': agent_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'dob': dob,
            'zip': zip_code,
            'county': county,
            'state': state,
            'created_at': datetime.now()
        }
        storage['clients'][client_id] = client
        return client
    
    @staticmethod
    def get_by_id(client_id):
        return storage['clients'].get(client_id)
    
    @staticmethod
    def get_all():
        return list(storage['clients'].values())

class Intake:
    @staticmethod
    def create(client_id, plan_year, household_size, ages, income, doctors, prescriptions, preferences):
        intake_id = str(uuid.uuid4())
        intake = {
            'id': intake_id,
            'client_id': client_id,
            'plan_year': plan_year,
            'household_size': household_size,
            'ages': ages,
            'income': income,
            'doctors': doctors,
            'prescriptions': prescriptions,
            'preferences': preferences,
            'created_at': datetime.now()
        }
        storage['intakes'][intake_id] = intake
        return intake
    
    @staticmethod
    def get_by_id(intake_id):
        return storage['intakes'].get(intake_id)

class QuoteResult:
    @staticmethod
    def create(intake_id, aptc, csr_level):
        quote_id = str(uuid.uuid4())
        quote = {
            'id': quote_id,
            'intake_id': intake_id,
            'aptc': aptc,
            'csr_level': csr_level,
            'created_at': datetime.now()
        }
        storage['quote_results'][quote_id] = quote
        return quote

class PlanFit:
    @staticmethod
    def create(quote_result_id, plan_id, net_premium, doctor_hits, rx_hits, rationale, fit_score):
        fit_id = str(uuid.uuid4())
        plan_fit = {
            'id': fit_id,
            'quote_result_id': quote_result_id,
            'plan_id': plan_id,
            'net_premium': net_premium,
            'doctor_hits': doctor_hits,
            'rx_hits': rx_hits,
            'rationale': rationale,
            'fit_score': fit_score,
            'created_at': datetime.now()
        }
        storage['plan_fits'][fit_id] = plan_fit
        return plan_fit

class Artifact:
    @staticmethod
    def create(client_id, artifact_type, payload, url=None):
        artifact_id = str(uuid.uuid4())
        artifact = {
            'id': artifact_id,
            'client_id': client_id,
            'type': artifact_type,
            'payload': payload,
            'url': url,
            'created_at': datetime.now()
        }
        storage['artifacts'][artifact_id] = artifact
        return artifact
    
    @staticmethod
    def get_by_client_id(client_id):
        return [a for a in storage['artifacts'].values() if a['client_id'] == client_id]

class HCGovContent:
    @staticmethod
    def search(query):
        """Simple search through HC.gov content"""
        results = []
        query_lower = query.lower()
        
        for content_list in storage['hcgov_content'].values():
            for item in content_list:
                if (query_lower in item['title'].lower() or 
                    query_lower in item['text'].lower()):
                    results.append({
                        'title': item['title'],
                        'url': item['url'],
                        'snippet': item['text'][:200] + '...' if len(item['text']) > 200 else item['text']
                    })
        
        return results[:5]  # Return top 5 results
