import unittest
import json
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from models import Client, Agent, _storage

class TestAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and clear storage"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Clear storage before each test
        for store in _storage.values():
            store.clear()
    
    def test_create_intake_success(self):
        """Test successful intake creation"""
        # Create agent and client first
        agent = Agent.create("Test Agent", "agent@test.com", "Test Brand")
        client = Client.create(
            agent_id=agent.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            dob="1985-01-01",
            zip="12345",
            county="Test County",
            state="CA"
        )
        
        # Intake data
        intake_data = {
            "client_id": client.id,
            "plan_year": 2024,
            "household_size": 2,
            "ages": [35, 32],
            "income": 75000.0,
            "doctors": [
                {
                    "npi": "1234567890",
                    "name": "Dr. Smith",
                    "specialty": "Cardiology"
                }
            ],
            "prescriptions": [
                {
                    "rxcui": "123456",
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "Daily"
                }
            ],
            "prefs": {
                "max_premium": 500.0,
                "important_benefits": ["Vision", "Dental"]
            }
        }
        
        # Make request
        response = self.app.post('/intake',
                               data=json.dumps(intake_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['client_id'], client.id)
        self.assertEqual(data['data']['plan_year'], 2024)
    
    def test_create_intake_missing_data(self):
        """Test intake creation with missing required data"""
        intake_data = {
            "plan_year": 2024,
            # Missing client_id and other required fields
        }
        
        response = self.app.post('/intake',
                               data=json.dumps(intake_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_get_client_artifacts_success(self):
        """Test successful retrieval of client artifacts"""
        # Create agent and client
        agent = Agent.create("Test Agent", "agent@test.com", "Test Brand")
        client = Client.create(
            agent_id=agent.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            dob="1985-01-01",
            zip="12345",
            county="Test County",
            state="CA"
        )
        
        # Make request
        response = self.app.get(f'/clients/{client.id}/artifacts')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], [])  # No artifacts initially
    
    def test_get_client_artifacts_not_found(self):
        """Test client artifacts retrieval for non-existent client"""
        response = self.app.get('/clients/999/artifacts')
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Client not found')

if __name__ == '__main__':
    unittest.main()