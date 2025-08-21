import unittest
import json
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from models import _storage, Agent, Client, Intake, Doctor, Prescription, Preferences
from api.quote import (
    compute_aptc, determine_csr_level, compute_oop_risk_score,
    get_fpl_amount, compute_slcsp_premium, get_age_bracket
)

class TestQuoteAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and clear storage"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Clear storage before each test
        for store in _storage.values():
            store.clear()
    
    def create_test_data(self):
        """Create test agent, client, and intake"""
        # Create agent
        agent = Agent.create("Test Agent", "agent@test.com", "Test Insurance")
        
        # Create client
        client = Client.create(
            agent_id=agent.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            dob="1985-01-01",
            zip="94102",
            county="San Francisco",
            state="CA"
        )
        
        # Create intake
        doctors = [Doctor(npi="1234567890", name="Dr. Smith", specialty="Primary Care")]
        prescriptions = [Prescription(rxcui="123", name="Lisinopril", dosage="10mg", frequency="Daily")]
        prefs = Preferences(max_premium=500.0, important_benefits=["Preventive Care"])
        
        intake = Intake.create(
            client_id=client.id,
            plan_year=2024,
            household_size=2,
            ages=[39, 35],
            income=60000.0,
            doctors=doctors,
            prescriptions=prescriptions,
            prefs=prefs
        )
        
        return agent, client, intake
    
    def test_get_age_bracket(self):
        """Test age bracket mapping for SLCSP premiums"""
        self.assertEqual(get_age_bracket(25), "age_27")
        self.assertEqual(get_age_bracket(30), "age_27")
        self.assertEqual(get_age_bracket(35), "age_40")
        self.assertEqual(get_age_bracket(45), "age_40")
        self.assertEqual(get_age_bracket(50), "age_50")
        self.assertEqual(get_age_bracket(55), "age_50")
        self.assertEqual(get_age_bracket(60), "age_60")
        self.assertEqual(get_age_bracket(65), "age_60")
    
    def test_get_fpl_amount(self):
        """Test Federal Poverty Level amount calculation"""
        # Test 48 states (including CA)
        fpl_1 = get_fpl_amount(1, "CA", 2024)
        self.assertEqual(fpl_1, 15060)
        
        fpl_4 = get_fpl_amount(4, "CA", 2024)
        self.assertEqual(fpl_4, 31200)
        
        # Test household larger than 8
        fpl_10 = get_fpl_amount(10, "CA", 2024)
        expected = 52720 + (2 * 5380)  # Base 8 + 2 additional
        self.assertEqual(fpl_10, expected)
    
    def test_compute_slcsp_premium(self):
        """Test SLCSP premium calculation"""
        # Test known ZIP code
        premium = compute_slcsp_premium("94102", [40, 35], 2024)
        # Should be age_40 + age_40 brackets
        expected = 360.28 + 360.28
        self.assertEqual(premium, expected)
        
        # Test unknown ZIP code (should use default)
        premium_unknown = compute_slcsp_premium("99999", [30], 2024)
        self.assertEqual(premium_unknown, 400.0)
    
    def test_compute_aptc_scenarios(self):
        """Test APTC calculation for various income scenarios"""
        slcsp_premium = 500.0
        fpl_amount = 31200.0  # 4-person household
        
        # Test 150% FPL - should get significant APTC
        income_150 = fpl_amount * 1.5  # $46,800
        aptc_150 = compute_aptc(income_150, slcsp_premium, fpl_amount)
        
        # At 150% FPL, contribution should be 4.05% of monthly income
        monthly_income_150 = income_150 / 12
        expected_contribution = monthly_income_150 * 0.0405
        expected_aptc = slcsp_premium - expected_contribution
        self.assertAlmostEqual(aptc_150, expected_aptc, places=2)
        
        # Test 250% FPL
        income_250 = fpl_amount * 2.5  # $78,000
        aptc_250 = compute_aptc(income_250, slcsp_premium, fpl_amount)
        
        # At 250% FPL, contribution should be 8.5% of monthly income
        monthly_income_250 = income_250 / 12
        expected_contribution_250 = monthly_income_250 * 0.085
        expected_aptc_250 = max(0, slcsp_premium - expected_contribution_250)
        self.assertAlmostEqual(aptc_250, expected_aptc_250, places=2)
        
        # Test income too high (>400% FPL)
        income_high = fpl_amount * 5  # $156,000
        aptc_high = compute_aptc(income_high, slcsp_premium, fpl_amount)
        self.assertEqual(aptc_high, 0.0)
        
        # Test income too low (<100% FPL)
        income_low = fpl_amount * 0.9  # $28,080
        aptc_low = compute_aptc(income_low, slcsp_premium, fpl_amount)
        self.assertEqual(aptc_low, 0.0)
    
    def test_determine_csr_level(self):
        """Test CSR level determination"""
        fpl_amount = 31200.0  # 4-person household
        
        # Test 140% FPL - should get 94% AV
        income_140 = fpl_amount * 1.4
        csr_140 = determine_csr_level(income_140, fpl_amount)
        self.assertEqual(csr_140, "94%")
        
        # Test 180% FPL - should get 87% AV
        income_180 = fpl_amount * 1.8
        csr_180 = determine_csr_level(income_180, fpl_amount)
        self.assertEqual(csr_180, "87%")
        
        # Test 220% FPL - should get 73% AV
        income_220 = fpl_amount * 2.2
        csr_220 = determine_csr_level(income_220, fpl_amount)
        self.assertEqual(csr_220, "73%")
        
        # Test 300% FPL - should get standard 70% AV
        income_300 = fpl_amount * 3.0
        csr_300 = determine_csr_level(income_300, fpl_amount)
        self.assertEqual(csr_300, "70%")
    
    def test_compute_oop_risk_score(self):
        """Test out-of-pocket risk score calculation"""
        # Low risk plan (low deductible and MOOP)
        low_risk = compute_oop_risk_score(5000, 1000)
        
        # High risk plan (high deductible and MOOP)
        high_risk = compute_oop_risk_score(9000, 8000)
        
        # Low risk should have lower score
        self.assertLess(low_risk, high_risk)
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(low_risk, 0)
        self.assertLessEqual(low_risk, 100)
        self.assertGreaterEqual(high_risk, 0)
        self.assertLessEqual(high_risk, 100)
    
    def test_quote_preview_success(self):
        """Test successful quote preview generation"""
        agent, client, intake = self.create_test_data()
        
        # Make request
        response = self.app.post('/quote/preview',
                               data=json.dumps({'intake_id': intake.id}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        quote_data = data['data']
        
        # Check required fields
        self.assertIn('quote_result_id', quote_data)
        self.assertIn('aptc', quote_data)
        self.assertIn('csr_level', quote_data)
        self.assertIn('slcsp_premium', quote_data)
        self.assertIn('income_fpl_ratio', quote_data)
        self.assertIn('plans', quote_data)
        
        # Check APTC is reasonable (should be > 0 for this income level)
        self.assertGreater(quote_data['aptc'], 0)
        
        # Check income FPL ratio
        self.assertGreater(quote_data['income_fpl_ratio'], 0)
        
        # Check plans array
        self.assertIsInstance(quote_data['plans'], list)
        self.assertGreater(len(quote_data['plans']), 0)
        
        # Check plan structure
        if quote_data['plans']:
            plan = quote_data['plans'][0]
            required_plan_fields = [
                'plan_id', 'issuer', 'name', 'metal', 'premium_full',
                'net_premium', 'deductible', 'moop', 'oop_risk_score', 'csr_flag'
            ]
            for field in required_plan_fields:
                self.assertIn(field, plan)
            
            # Net premium should be less than or equal to full premium
            self.assertLessEqual(plan['net_premium'], plan['premium_full'])
    
    def test_quote_preview_intake_not_found(self):
        """Test quote preview with non-existent intake"""
        response = self.app.post('/quote/preview',
                               data=json.dumps({'intake_id': 999}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Intake not found')
    
    def test_quote_preview_missing_data(self):
        """Test quote preview with missing request data"""
        response = self.app.post('/quote/preview',
                               data=json.dumps({}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()