from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class MetalLevel(str, Enum):
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    CATASTROPHIC = "Catastrophic"

class CSRLevel(str, Enum):
    NONE = "None"
    CSR_73 = "73%"
    CSR_87 = "87%"
    CSR_94 = "94%"

@dataclass
class Agent:
    id: str
    name: str
    email: str
    brand_name: str
    logo_url: str = ""

@dataclass
class Client:
    id: str
    agent_id: str
    first_name: str
    last_name: str
    email: str
    dob: str
    zip_code: str
    county: str
    state: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Doctor:
    npi: str
    name: str
    specialty: str = ""

@dataclass
class Prescription:
    name: str
    dosage: str = ""
    quantity: int = 30

@dataclass
class Preferences:
    max_premium: Optional[float] = None
    prefer_low_deductible: bool = False
    prefer_broad_network: bool = True

@dataclass
class Intake:
    id: str
    client_id: str
    plan_year: int
    household_size: int
    ages: List[int]
    annual_income: float
    doctors: List[Doctor] = field(default_factory=list)
    prescriptions: List[Prescription] = field(default_factory=list)
    preferences: Preferences = field(default_factory=Preferences)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Plan:
    id: str
    plan_year: int
    issuer: str
    name: str
    metal: MetalLevel
    premium_full: float  # Full premium before APTC
    deductible: float
    moop: float  # Maximum out-of-pocket
    csr_eligible: bool = False
    service_area: str = ""
    
@dataclass
class QuoteResult:
    id: str
    intake_id: str
    aptc: float  # Advanced Premium Tax Credit
    csr_level: CSRLevel
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class DoctorFit:
    npi: str
    name: str
    in_network: bool
    tier: str = ""

@dataclass
class RxFit:
    name: str
    tier: int
    covered: bool
    prior_auth: bool = False
    step_therapy: bool = False
    cost_sharing: float = 0.0

@dataclass
class PlanFit:
    id: str
    quote_result_id: str
    plan_id: str
    net_premium: float  # Premium after APTC
    doctor_fits: List[DoctorFit] = field(default_factory=list)
    rx_fits: List[RxFit] = field(default_factory=list)
    rationale: Dict[str, Any] = field(default_factory=dict)
    fit_score: float = 0.0

@dataclass
class Artifact:
    id: str
    client_id: str
    type: str  # pdf, soa, log
    payload: str  # JSON string or file path
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class HCGovContent:
    id: str
    title: str
    url: str
    text: str
    plan_year: int
    updated_at: datetime
    content_type: str = "article"  # glossary, article, other
