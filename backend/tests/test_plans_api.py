import unittest
import json
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from models import _storage
from api.plans import seed_plans_data, normalize_plan_data, filter_plans_by_location
from models import Plan

class TestPlansAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and clear storage"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Clear storage before each test
        for store in _storage.values():
            store.clear()
    
    def test_normalize_plan_data(self):
        """Test plan data normalization"""
        raw_plan = {
            "plan_id": "TEST001",
            "plan_year": 2024,
            "issuer_name": "Test Insurance",
            "plan_name": "Test Silver Plan",
            "metal_level": "Silver",
            "premium_adult": 400.0,
            "premium_child": 240.0,
            "deductible_individual": 3000,
            "out_of_pocket_max_individual": 8000,
            "csr_variation": "87"
        }
        
        plan = normalize_plan_data(raw_plan)
        
        self.assertEqual(plan.id, "TEST001")
        self.assertEqual(plan.plan_year, 2024)
        self.assertEqual(plan.issuer, "Test Insurance")
        self.assertEqual(plan.name, "Test Silver Plan")
        self.assertEqual(plan.metal, "Silver")
        self.assertEqual(plan.premium_full, 320.0)  # (400 + 240) / 2
        self.assertEqual(plan.deductible, 3000)
        self.assertEqual(plan.moop, 8000)
        self.assertTrue(plan.csr_flag)  # Has CSR variation
    
    def test_seed_plans_data(self):
        """Test loading and seeding plans data"""
        # Seed the data
        seed_plans_data()
        
        # Check that plans were loaded
        plans = Plan.list_all()
        self.assertGreater(len(plans), 0)
        
        # Check that all plans have required fields
        for plan in plans:
            self.assertIsNotNone(plan.id)
            self.assertIsNotNone(plan.issuer)
            self.assertIsNotNone(plan.name)
            self.assertIsNotNone(plan.metal)
            self.assertIsInstance(plan.premium_full, (int, float))
            self.assertIsInstance(plan.deductible, (int, float))
            self.assertIsInstance(plan.moop, (int, float))
    
    def test_get_plans_no_filters(self):
        """Test getting all plans without filters"""
        response = self.app.get('/plans')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
    
    def test_get_plans_with_year_filter(self):
        """Test getting plans filtered by year"""
        response = self.app.get('/plans?year=2024')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # All returned plans should be for 2024
        for plan in data['data']:
            self.assertEqual(plan['plan_year'], 2024)
    
    def test_get_plans_with_metal_filter(self):
        """Test getting plans filtered by metal level"""
        response = self.app.get('/plans?metal=Silver')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # All returned plans should be Silver
        for plan in data['data']:
            self.assertEqual(plan['metal'], 'Silver')
    
    def test_get_plans_with_issuer_filter(self):
        """Test getting plans filtered by issuer"""
        response = self.app.get('/plans?issuer=Blue Shield')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # All returned plans should be from Blue Shield
        for plan in data['data']:
            self.assertIn('Blue Shield', plan['issuer'])
    
    def test_get_plans_with_zip_filter(self):
        """Test getting plans filtered by ZIP code"""
        response = self.app.get('/plans?zip=94102')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Should return plans available in the 94102 ZIP code
        self.assertGreater(data['count'], 0)
    
    def test_get_plans_with_county_filter(self):
        """Test getting plans filtered by county"""
        response = self.app.get('/plans?county=San Francisco')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Should return plans available in San Francisco county
        self.assertGreater(data['count'], 0)
    
    def test_get_plans_with_multiple_filters(self):
        """Test getting plans with multiple filters"""
        response = self.app.get('/plans?year=2024&metal=Bronze&issuer=Kaiser')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Check that all filters are applied
        for plan in data['data']:
            self.assertEqual(plan['plan_year'], 2024)
            self.assertEqual(plan['metal'], 'Bronze')
            self.assertIn('Kaiser', plan['issuer'])
    
    def test_get_plans_no_results(self):
        """Test getting plans with filters that return no results"""
        response = self.app.get('/plans?metal=Platinum&issuer=NonExistent')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['data'], [])
    
    def test_filter_plans_by_location(self):
        """Test location-based filtering function"""
        # First seed some plans
        seed_plans_data()
        plans = Plan.list_all()
        
        # Test ZIP code filtering
        filtered_by_zip = filter_plans_by_location(plans, zip_code="94102")
        self.assertGreater(len(filtered_by_zip), 0)
        
        # Test county filtering
        filtered_by_county = filter_plans_by_location(plans, county="San Francisco")
        self.assertGreater(len(filtered_by_county), 0)
        
        # Test no filters (should return all)
        filtered_none = filter_plans_by_location(plans)
        self.assertEqual(len(filtered_none), len(plans))

if __name__ == '__main__':
    unittest.main()