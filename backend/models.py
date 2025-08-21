from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class Agent:
    id: int
    name: str
    email: str
    brand_name: str
    logo_url: Optional[str] = None

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
    important_benefits: List[str] = None
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

@dataclass
class QuoteResult:
    id: int
    intake_id: int
    aptc: float
    csr_level: str

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

@dataclass
class Artifact:
    id: int
    client_id: int
    type: str
    payload: Optional[Any] = None
    url: Optional[str] = None
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()