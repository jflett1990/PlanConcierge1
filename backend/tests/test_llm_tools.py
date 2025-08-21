import unittest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from llm.tools import (
    hcgov_content_search, plans_lookup, networks_formularies_check,
    execute_tool_call, TOOL_DEFINITIONS, SYSTEM_PROMPT
)

class TestLLMTools(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Ensure plans and content are loaded
        from api.plans import seed_plans_data
        from worker.hcgov_ingest import get_ingestor
        
        seed_plans_data()  # Load mock plans
        get_ingestor()     # Load mock healthcare.gov content
    
    def test_hcgov_content_search_tool(self):
        """Test healthcare.gov content search tool"""
        result = hcgov_content_search("premium", limit=3)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['query'], 'premium')
        self.assertGreater(len(result['results']), 0)
        self.assertLessEqual(len(result['results']), 3)
        
        # Check result structure
        for item in result['results']:
            self.assertIn('title', item)
            self.assertIn('url', item)
            self.assertIn('text', item)
            self.assertIn('type', item)
            self.assertIn('source', item)
            self.assertIn('relevance_score', item)
    
    def test_hcgov_content_search_empty_query(self):
        """Test content search with empty query"""
        result = hcgov_content_search("", limit=5)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['results']), 0)
    
    def test_plans_lookup_tool(self):
        """Test plans lookup tool"""
        result = plans_lookup(zip_code="94102", metal="Silver", limit=5)
        
        self.assertTrue(result['success'])
        self.assertGreater(len(result['data']), 0)
        self.assertLessEqual(len(result['data']), 5)
        
        # Check filter application
        filters = result['filters_applied']
        self.assertEqual(filters['zip_code'], "94102")
        self.assertEqual(filters['metal'], "Silver")
        
        # Check plan structure
        for plan in result['data']:
            self.assertIn('id', plan)
            self.assertIn('name', plan)
            self.assertIn('metal', plan)
            self.assertIn('premium_full', plan)
            self.assertEqual(plan['metal'], 'Silver')
    
    def test_plans_lookup_no_filters(self):
        """Test plans lookup without filters"""
        result = plans_lookup(limit=3)
        
        self.assertTrue(result['success'])
        self.assertGreater(len(result['data']), 0)
        self.assertLessEqual(len(result['data']), 3)
    
    def test_networks_formularies_check_tool(self):
        """Test networks and formularies check tool"""
        plan_ids = ["11512CA0040001", "94506CA0990001"]
        npi_list = ["1234567890"]
        rx_list = [{"rxcui": "123", "name": "Lisinopril", "dosage": "10mg", "frequency": "Daily"}]
        
        result = networks_formularies_check(plan_ids, npi_list, rx_list)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['plan_ids'], plan_ids)
        
        # Check provider results
        self.assertIn('provider_results', result)
        self.assertIn('rx_results', result)
        self.assertIn('summaries', result)
        
        for plan_id in plan_ids:
            self.assertIn(plan_id, result['provider_results'])
            self.assertIn(plan_id, result['rx_results'])
            self.assertIn(plan_id, result['summaries'])
    
    def test_networks_formularies_check_minimal(self):
        """Test networks check with only plan IDs"""
        plan_ids = ["11512CA0040001"]
        
        result = networks_formularies_check(plan_ids)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['plan_ids'], plan_ids)
        self.assertEqual(result['provider_results'], {})
        self.assertEqual(result['rx_results'], {})
    
    def test_execute_tool_call_valid(self):
        """Test tool call execution with valid tools"""
        # Test content search
        result = execute_tool_call("hcgov_content_search", {"query": "deductible"})
        self.assertTrue(result['success'])
        
        # Test plans lookup
        result = execute_tool_call("plans_lookup", {"zip_code": "94102"})
        self.assertTrue(result['success'])
        
        # Test networks check
        result = execute_tool_call("networks_formularies_check", {
            "plan_ids": ["11512CA0040001"]
        })
        self.assertTrue(result['success'])
    
    def test_execute_tool_call_invalid(self):
        """Test tool call execution with invalid tool name"""
        result = execute_tool_call("invalid_tool", {})
        
        self.assertFalse(result['success'])
        self.assertIn('Unknown tool', result['error'])
    
    def test_tool_definitions_structure(self):
        """Test that tool definitions are properly structured"""
        self.assertEqual(len(TOOL_DEFINITIONS), 3)
        
        tool_names = [tool['function']['name'] for tool in TOOL_DEFINITIONS]
        expected_names = ['hcgov_content_search', 'plans_lookup', 'networks_formularies_check']
        
        for name in expected_names:
            self.assertIn(name, tool_names)
        
        # Check each tool has required structure
        for tool in TOOL_DEFINITIONS:
            self.assertEqual(tool['type'], 'function')
            self.assertIn('function', tool)
            
            func = tool['function']
            self.assertIn('name', func)
            self.assertIn('description', func)
            self.assertIn('parameters', func)
            
            params = func['parameters']
            self.assertEqual(params['type'], 'object')
            self.assertIn('properties', params)
    
    def test_system_prompt_content(self):
        """Test system prompt contains required elements"""
        self.assertIn("James's Plan Concierge", SYSTEM_PROMPT)
        self.assertIn("Use your tools", SYSTEM_PROMPT)
        self.assertIn("Never fabricate", SYSTEM_PROMPT)
        self.assertIn("healthcare.gov", SYSTEM_PROMPT)
        self.assertIn("What this means for you", SYSTEM_PROMPT)
        self.assertIn("Networks and formularies change", SYSTEM_PROMPT)
        self.assertIn("JSON", SYSTEM_PROMPT)
        
        # Check for required JSON structure
        self.assertIn('"title"', SYSTEM_PROMPT)
        self.assertIn('"sections"', SYSTEM_PROMPT)
        self.assertIn('"citations"', SYSTEM_PROMPT)
        
        # Check for templates
        self.assertIn("Definition Template", SYSTEM_PROMPT)
        self.assertIn("Plan Explanation Template", SYSTEM_PROMPT)
        self.assertIn("Top 3 Summary Template", SYSTEM_PROMPT)
    
    def test_plans_lookup_with_issuer_filter(self):
        """Test plans lookup with issuer filtering"""
        result = plans_lookup(issuer="Blue Shield", limit=10)
        
        self.assertTrue(result['success'])
        
        # All returned plans should be from Blue Shield
        for plan in result['data']:
            self.assertIn('blue shield', plan['issuer'].lower())
    
    def test_plans_lookup_with_year_filter(self):
        """Test plans lookup with year filtering"""
        result = plans_lookup(year=2024, limit=10)
        
        self.assertTrue(result['success'])
        
        # All returned plans should be for 2024
        for plan in result['data']:
            self.assertEqual(plan['plan_year'], 2024)
    
    @patch('llm.tools.openai_client')
    def test_openai_client_not_configured(self, mock_client):
        """Test behavior when OpenAI client is not configured"""
        # Temporarily set client to None
        from llm import tools
        original_client = tools.openai_client
        tools.openai_client = None
        
        try:
            from llm.tools import call_plan_concierge_llm
            result = call_plan_concierge_llm("test message")
            
            self.assertFalse(result['success'])
            self.assertIn('OpenAI API key not configured', result['error'])
        finally:
            # Restore original client
            tools.openai_client = original_client
    
    def test_content_search_glossary_priority(self):
        """Test that glossary entries are prioritized in search results"""
        result = hcgov_content_search("health", limit=10)
        
        self.assertTrue(result['success'])
        
        if len(result['results']) > 1:
            # Check for glossary entries appearing first
            glossary_positions = []
            content_positions = []
            
            for i, item in enumerate(result['results']):
                if item['type'] == 'glossary':
                    glossary_positions.append(i)
                elif item['type'] == 'content':
                    content_positions.append(i)
            
            # If both types exist, glossary should come first
            if glossary_positions and content_positions:
                self.assertLess(min(glossary_positions), min(content_positions))

if __name__ == '__main__':
    unittest.main()