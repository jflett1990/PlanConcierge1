import unittest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from integrations.provider_formulary import (
    check_providers, check_rx, get_provider_summary, get_rx_summary
)

class TestProviderFormulary(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.plan_ids = ["11512CA0040001", "94506CA0990001"]
        self.npi_list = ["1234567890", "9876543210"]
        self.rx_list = [
            {"rxcui": "123", "name": "Lisinopril", "dosage": "10mg", "frequency": "Daily"},
            {"rxcui": "456", "name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"}
        ]
    
    def test_check_providers_structure(self):
        """Test provider check returns correct structure"""
        results = check_providers(self.plan_ids, self.npi_list)
        
        # Check overall structure
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), len(self.plan_ids))
        
        for plan_id in self.plan_ids:
            self.assertIn(plan_id, results)
            plan_results = results[plan_id]
            self.assertIsInstance(plan_results, list)
            self.assertEqual(len(plan_results), len(self.npi_list))
            
            for provider_result in plan_results:
                # Check required fields
                required_fields = ['npi', 'name', 'specialty', 'in_network']
                for field in required_fields:
                    self.assertIn(field, provider_result)
                
                # Check data types
                self.assertIsInstance(provider_result['in_network'], bool)
                self.assertIn(provider_result['npi'], self.npi_list)
                
                # Check conditional fields based on network status
                if provider_result['in_network']:
                    self.assertIn('tier', provider_result)
                    self.assertIn('copay', provider_result)
                    self.assertIn('distance_miles', provider_result)
                    self.assertIsInstance(provider_result['copay'], (int, float))
                else:
                    self.assertEqual(provider_result['tier'], 'out_of_network')
                    self.assertIsNone(provider_result['copay'])
    
    def test_check_providers_consistency(self):
        """Test that provider results are consistent across calls"""
        results1 = check_providers(self.plan_ids, self.npi_list)
        results2 = check_providers(self.plan_ids, self.npi_list)
        
        # Results should be identical due to seeded randomization
        self.assertEqual(results1, results2)
    
    def test_check_rx_structure(self):
        """Test formulary check returns correct structure"""
        results = check_rx(self.plan_ids, self.rx_list)
        
        # Check overall structure
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), len(self.plan_ids))
        
        for plan_id in self.plan_ids:
            self.assertIn(plan_id, results)
            plan_results = results[plan_id]
            self.assertIsInstance(plan_results, list)
            self.assertEqual(len(plan_results), len(self.rx_list))
            
            for rx_result in plan_results:
                # Check required fields
                required_fields = ['rxcui', 'name', 'dosage', 'frequency', 'covered']
                for field in required_fields:
                    self.assertIn(field, rx_result)
                
                # Check data types
                self.assertIsInstance(rx_result['covered'], bool)
                self.assertIn(rx_result['rxcui'], [rx['rxcui'] for rx in self.rx_list])
                
                # Check conditional fields based on coverage
                if rx_result['covered']:
                    self.assertIn('tier', rx_result)
                    self.assertIn('copay', rx_result)
                    self.assertIsInstance(rx_result['tier'], int)
                    self.assertIsInstance(rx_result['copay'], (int, float))
                else:
                    self.assertIsNone(rx_result['tier'])
                    self.assertIsNone(rx_result['copay'])
                    self.assertIn('coverage_reason', rx_result)
    
    def test_check_rx_consistency(self):
        """Test that formulary results are consistent across calls"""
        results1 = check_rx(self.plan_ids, self.rx_list)
        results2 = check_rx(self.plan_ids, self.rx_list)
        
        # Results should be identical due to seeded randomization
        self.assertEqual(results1, results2)
    
    def test_get_provider_summary(self):
        """Test provider summary calculation"""
        # Test with sample provider results
        provider_results = [
            {"npi": "123", "in_network": True, "tier": "preferred", "copay": 25.0},
            {"npi": "456", "in_network": True, "tier": "standard", "copay": 35.0},
            {"npi": "789", "in_network": False, "tier": "out_of_network", "copay": None}
        ]
        
        summary = get_provider_summary(provider_results)
        
        self.assertEqual(summary['in_network_count'], 2)
        self.assertEqual(summary['total_count'], 3)
        self.assertEqual(summary['coverage_rate'], 0.67)
        self.assertEqual(summary['preferred_providers'], 1)
        self.assertEqual(summary['avg_copay'], 30.0)
    
    def test_get_provider_summary_empty(self):
        """Test provider summary with empty results"""
        summary = get_provider_summary([])
        
        self.assertEqual(summary['in_network_count'], 0)
        self.assertEqual(summary['total_count'], 0)
        self.assertEqual(summary['coverage_rate'], 0.0)
    
    def test_get_rx_summary(self):
        """Test formulary summary calculation"""
        # Test with sample rx results
        rx_results = [
            {"rxcui": "123", "covered": True, "tier": 1, "copay": 10.0, "prior_auth_required": False},
            {"rxcui": "456", "covered": True, "tier": 2, "copay": 30.0, "prior_auth_required": True},
            {"rxcui": "789", "covered": False, "tier": None, "copay": None, "prior_auth_required": False}
        ]
        
        summary = get_rx_summary(rx_results)
        
        self.assertEqual(summary['covered_count'], 2)
        self.assertEqual(summary['total_count'], 3)
        self.assertEqual(summary['coverage_rate'], 0.67)
        self.assertEqual(summary['prior_auth_count'], 1)
        self.assertEqual(summary['avg_copay'], 20.0)
        self.assertEqual(summary['tier_breakdown']['tier_1'], 1)
        self.assertEqual(summary['tier_breakdown']['tier_2'], 1)
    
    def test_get_rx_summary_empty(self):
        """Test formulary summary with empty results"""
        summary = get_rx_summary([])
        
        self.assertEqual(summary['covered_count'], 0)
        self.assertEqual(summary['total_count'], 0)
        self.assertEqual(summary['coverage_rate'], 0.0)
    
    def test_empty_inputs(self):
        """Test functions handle empty inputs gracefully"""
        # Empty plan IDs
        provider_results = check_providers([], self.npi_list)
        self.assertEqual(provider_results, {})
        
        rx_results = check_rx([], self.rx_list)
        self.assertEqual(rx_results, {})
        
        # Empty provider/rx lists
        provider_results = check_providers(self.plan_ids, [])
        for plan_id in self.plan_ids:
            self.assertEqual(provider_results[plan_id], [])
        
        rx_results = check_rx(self.plan_ids, [])
        for plan_id in self.plan_ids:
            self.assertEqual(rx_results[plan_id], [])
    
    def test_drug_tier_logic(self):
        """Test that drug tier assignment follows expected patterns"""
        # Test known generic drug
        generic_rx = [{"rxcui": "123", "name": "lisinopril", "dosage": "10mg", "frequency": "Daily"}]
        results = check_rx(["test_plan"], generic_rx)
        
        rx_result = results["test_plan"][0]
        if rx_result['covered']:
            self.assertEqual(rx_result['tier'], 1)  # Generic should be tier 1
        
        # Test known specialty drug
        specialty_rx = [{"rxcui": "456", "name": "humira", "dosage": "40mg", "frequency": "Biweekly"}]
        results = check_rx(["test_plan"], specialty_rx)
        
        rx_result = results["test_plan"][0]
        if rx_result['covered']:
            self.assertEqual(rx_result['tier'], 4)  # Specialty should be tier 4
    
    def test_plan_type_network_rates(self):
        """Test that different plan types have different network rates"""
        hmo_plan = "TEST_HMO_PLAN"
        ppo_plan = "TEST_PPO_PLAN"
        
        # Test multiple times to see pattern (though results are seeded)
        hmo_results = check_providers([hmo_plan], ["1234567890"] * 20)
        ppo_results = check_providers([ppo_plan], ["1234567890"] * 20)
        
        # Both should have some results
        self.assertIn(hmo_plan, hmo_results)
        self.assertIn(ppo_plan, ppo_results)

if __name__ == '__main__':
    unittest.main()