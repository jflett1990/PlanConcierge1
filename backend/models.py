from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

# In-memory storage
_storage = {
    'agents': {},
    'clients': {},
    'intakes': {},
    'plans': {},
    'quote_results': {},
    'plan_fits': {},
    'artifacts': {}
}

# Helper functions
def get_next_id(store_name: str) -> int:
    """Get next available ID for a store"""
    return max(_storage[store_name].keys(), default=0) + 1

def filter_by_field(store_name: str, field: str, value: Any) -> List[Any]:
    """Filter items in store by field value"""
    return [item for item in _storage[store_name].values() 
            if hasattr(item, field) and getattr(item, field) == value]

@dataclass
class Agent:
    id: int
    name: str
    email: str
    brand_name: str
    logo_url: Optional[str] = None

    @classmethod
    def create(cls, name: str, email: str, brand_name: str, logo_url: Optional[str] = None):
        agent_id = get_next_id('agents')
        agent = cls(agent_id, name, email, brand_name, logo_url)
        _storage['agents'][agent_id] = agent
        return agent

    @classmethod
    def get(cls, agent_id: int):
        return _storage['agents'].get(agent_id)

    @classmethod
    def list_all(cls):
        return list(_storage['agents'].values())

@dataclass
class Client:
    id: int
    agent_id: int
    first_name: str
    last_name: str
    email: str
    dob: str
    zip: str
    county: str
    state: str

    @classmethod
    def create(cls, agent_id: int, first_name: str, last_name: str, email: str, 
               dob: str, zip: str, county: str, state: str):
        client_id = get_next_id('clients')
        client = cls(client_id, agent_id, first_name, last_name, email, dob, zip, county, state)
        _storage['clients'][client_id] = client
        return client

    @classmethod
    def get(cls, client_id: int):
        return _storage['clients'].get(client_id)

    @classmethod
    def list_all(cls):
        return list(_storage['clients'].values())

    @classmethod
    def list_by_agent(cls, agent_id: int):
        return filter_by_field('clients', 'agent_id', agent_id)

@dataclass
class Doctor:
    npi: str
    name: str
    specialty: str

@dataclass
class Prescription:
    rxcui: str
    name: str
    dosage: str
    frequency: str

@dataclass
class Preferences:
    max_premium: Optional[float] = None
    max_deductible: Optional[float] = None
    important_benefits: Optional[List[str]] = None
    pharmacy_preference: Optional[str] = None

@dataclass
class Intake:
    id: int
    client_id: int
    plan_year: int
    household_size: int
    ages: List[int]
    income: float
    doctors: List[Doctor]
    prescriptions: List[Prescription]
    prefs: Preferences

    @classmethod
    def create(cls, client_id: int, plan_year: int, household_size: int, ages: List[int],
               income: float, doctors: List[Doctor], prescriptions: List[Prescription],
               prefs: Preferences):
        intake_id = get_next_id('intakes')
        intake = cls(intake_id, client_id, plan_year, household_size, ages, 
                    income, doctors, prescriptions, prefs)
        _storage['intakes'][intake_id] = intake
        return intake

    @classmethod
    def get(cls, intake_id: int):
        return _storage['intakes'].get(intake_id)

    @classmethod
    def list_all(cls):
        return list(_storage['intakes'].values())

    @classmethod
    def list_by_client(cls, client_id: int):
        return filter_by_field('intakes', 'client_id', client_id)

@dataclass
class Plan:
    id: str
    plan_year: int
    issuer: str
    name: str
    metal: str
    premium_full: float
    deductible: float
    moop: float
    csr_flag: bool

    @classmethod
    def create(cls, plan_id: str, plan_year: int, issuer: str, name: str, metal: str,
               premium_full: float, deductible: float, moop: float, csr_flag: bool):
        plan = cls(plan_id, plan_year, issuer, name, metal, premium_full, deductible, moop, csr_flag)
        _storage['plans'][plan_id] = plan
        return plan

    @classmethod
    def get(cls, plan_id: str):
        return _storage['plans'].get(plan_id)

    @classmethod
    def list_all(cls):
        return list(_storage['plans'].values())

    @classmethod
    def list_by_year(cls, plan_year: int):
        return filter_by_field('plans', 'plan_year', plan_year)

@dataclass
class QuoteResult:
    id: int
    intake_id: int
    aptc: float
    csr_level: str

    @classmethod
    def create(cls, intake_id: int, aptc: float, csr_level: str):
        quote_id = get_next_id('quote_results')
        quote = cls(quote_id, intake_id, aptc, csr_level)
        _storage['quote_results'][quote_id] = quote
        return quote

    @classmethod
    def get(cls, quote_id: int):
        return _storage['quote_results'].get(quote_id)

    @classmethod
    def list_all(cls):
        return list(_storage['quote_results'].values())

    @classmethod
    def list_by_intake(cls, intake_id: int):
        return filter_by_field('quote_results', 'intake_id', intake_id)

@dataclass
class PlanFit:
    id: int
    quote_result_id: int
    plan_id: str
    net_premium: float
    doctor_hits: List[str]
    rx_hits: List[str]
    rationale: Dict[str, str]
    fit_score: float

    @classmethod
    def create(cls, quote_result_id: int, plan_id: str, net_premium: float,
               doctor_hits: List[str], rx_hits: List[str], rationale: Dict[str, str],
               fit_score: float):
        fit_id = get_next_id('plan_fits')
        plan_fit = cls(fit_id, quote_result_id, plan_id, net_premium, doctor_hits, 
                      rx_hits, rationale, fit_score)
        _storage['plan_fits'][fit_id] = plan_fit
        return plan_fit

    @classmethod
    def get(cls, fit_id: int):
        return _storage['plan_fits'].get(fit_id)

    @classmethod
    def list_all(cls):
        return list(_storage['plan_fits'].values())

    @classmethod
    def list_by_quote(cls, quote_result_id: int):
        return filter_by_field('plan_fits', 'quote_result_id', quote_result_id)

@dataclass
class Artifact:
    id: int
    client_id: int
    type: str
    payload: Optional[Any] = None
    url: Optional[str] = None
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    @classmethod
    def create(cls, client_id: int, artifact_type: str, payload: Optional[Any] = None, 
               url: Optional[str] = None):
        artifact_id = get_next_id('artifacts')
        artifact = cls(artifact_id, client_id, artifact_type, payload, url)
        _storage['artifacts'][artifact_id] = artifact
        return artifact

    @classmethod
    def get(cls, artifact_id: int):
        return _storage['artifacts'].get(artifact_id)

    @classmethod
    def list_all(cls):
        return list(_storage['artifacts'].values())

    @classmethod
    def list_by_client(cls, client_id: int):
        return filter_by_field('artifacts', 'client_id', client_id)