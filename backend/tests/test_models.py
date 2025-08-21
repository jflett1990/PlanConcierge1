import unittest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import (
    Agent, Client, Intake, Plan, QuoteResult, PlanFit, Artifact,
    Doctor, Prescription, Preferences, _storage
)

class TestModels(unittest.TestCase):
    
    def setUp(self):
        """Clear storage before each test"""
        for store in _storage.values():
            store.clear()
    
    def test_agent_crud(self):
        """Test Agent CRUD operations"""
        # Create
        agent = Agent.create("John Doe", "john@example.com", "Acme Insurance")
        self.assertEqual(agent.id, 1)
        self.assertEqual(agent.name, "John Doe")
        self.assertEqual(agent.email, "john@example.com")
        self.assertEqual(agent.brand_name, "Acme Insurance")
        
        # Get
        retrieved = Agent.get(1)
        self.assertEqual(retrieved.name, "John Doe")
        
        # List
        agents = Agent.list_all()
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0].name, "John Doe")
    
    def test_client_crud(self):
        """Test Client CRUD operations"""
        # Create agent first
        agent = Agent.create("Agent", "agent@test.com", "Test Brand")
        
        # Create client
        client = Client.create(
            agent_id=agent.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            dob="1985-06-15",
            zip="12345",
            county="Test County",
            state="CA"
        )
        
        self.assertEqual(client.id, 1)
        self.assertEqual(client.first_name, "Jane")
        self.assertEqual(client.agent_id, agent.id)
        
        # Get
        retrieved = Client.get(1)
        self.assertEqual(retrieved.first_name, "Jane")
        
        # List by agent
        clients = Client.list_by_agent(agent.id)
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0].first_name, "Jane")
    
    def test_intake_crud(self):
        """Test Intake CRUD operations"""
        # Create agent and client
        agent = Agent.create("Agent", "agent@test.com", "Test Brand")
        client = Client.create(
            agent_id=agent.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            dob="1985-06-15",
            zip="12345",
            county="Test County",
            state="CA"
        )
        
        # Create intake data
        doctors = [Doctor(npi="1234567890", name="Dr. Smith", specialty="Cardiology")]
        prescriptions = [Prescription(rxcui="123", name="Medication", dosage="10mg", frequency="Daily")]
        prefs = Preferences(max_premium=500.0, important_benefits=["Vision", "Dental"])
        
        # Create intake
        intake = Intake.create(
            client_id=client.id,
            plan_year=2024,
            household_size=2,
            ages=[35, 32],
            income=75000.0,
            doctors=doctors,
            prescriptions=prescriptions,
            prefs=prefs
        )
        
        self.assertEqual(intake.id, 1)
        self.assertEqual(intake.client_id, client.id)
        self.assertEqual(intake.plan_year, 2024)
        self.assertEqual(len(intake.doctors), 1)
        self.assertEqual(intake.doctors[0].name, "Dr. Smith")
        
        # Get
        retrieved = Intake.get(1)
        self.assertEqual(retrieved.plan_year, 2024)
        
        # List by client
        intakes = Intake.list_by_client(client.id)
        self.assertEqual(len(intakes), 1)
    
    def test_plan_crud(self):
        """Test Plan CRUD operations"""
        # Create plan
        plan = Plan.create(
            plan_id="PLAN_123",
            plan_year=2024,
            issuer="Blue Cross",
            name="Silver Plan",
            metal="Silver",
            premium_full=450.0,
            deductible=2500.0,
            moop=8000.0,
            csr_flag=True
        )
        
        self.assertEqual(plan.id, "PLAN_123")
        self.assertEqual(plan.issuer, "Blue Cross")
        self.assertEqual(plan.metal, "Silver")
        
        # Get
        retrieved = Plan.get("PLAN_123")
        self.assertEqual(retrieved.name, "Silver Plan")
        
        # List by year
        plans = Plan.list_by_year(2024)
        self.assertEqual(len(plans), 1)
    
    def test_quote_result_crud(self):
        """Test QuoteResult CRUD operations"""
        # Create dependencies
        agent = Agent.create("Agent", "agent@test.com", "Test Brand")
        client = Client.create(
            agent_id=agent.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            dob="1985-06-15",
            zip="12345",
            county="Test County",
            state="CA"
        )
        
        doctors = [Doctor(npi="1234567890", name="Dr. Smith", specialty="Cardiology")]
        prescriptions = [Prescription(rxcui="123", name="Medication", dosage="10mg", frequency="Daily")]
        prefs = Preferences()
        
        intake = Intake.create(
            client_id=client.id,
            plan_year=2024,
            household_size=1,
            ages=[35],
            income=50000.0,
            doctors=doctors,
            prescriptions=prescriptions,
            prefs=prefs
        )
        
        # Create quote result
        quote = QuoteResult.create(
            intake_id=intake.id,
            aptc=200.0,
            csr_level="87%"
        )
        
        self.assertEqual(quote.id, 1)
        self.assertEqual(quote.intake_id, intake.id)
        self.assertEqual(quote.aptc, 200.0)
        
        # Get
        retrieved = QuoteResult.get(1)
        self.assertEqual(retrieved.csr_level, "87%")
    
    def test_artifact_crud(self):
        """Test Artifact CRUD operations"""
        # Create client
        agent = Agent.create("Agent", "agent@test.com", "Test Brand")
        client = Client.create(
            agent_id=agent.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            dob="1985-06-15",
            zip="12345",
            county="Test County",
            state="CA"
        )
        
        # Create artifact
        artifact = Artifact.create(
            client_id=client.id,
            artifact_type="pdf_comparison",
            url="https://example.com/report.pdf"
        )
        
        self.assertEqual(artifact.id, 1)
        self.assertEqual(artifact.client_id, client.id)
        self.assertEqual(artifact.type, "pdf_comparison")
        self.assertIsNotNone(artifact.created_at)
        
        # Get
        retrieved = Artifact.get(1)
        self.assertEqual(retrieved.url, "https://example.com/report.pdf")
        
        # List by client
        artifacts = Artifact.list_by_client(client.id)
        self.assertEqual(len(artifacts), 1)

if __name__ == '__main__':
    unittest.main()