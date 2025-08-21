import unittest
import sys
import os
import time

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worker.hcgov_ingest import HealthcareGovIngestor, get_ingestor

class TestHealthcareGovIngest(unittest.TestCase):
    
    def setUp(self):
        """Set up test ingestor"""
        self.ingestor = HealthcareGovIngestor()
    
    def test_ingest_content_mock(self):
        """Test content ingestion with mock data"""
        success = self.ingestor.ingest_content(use_mock=True)
        
        self.assertTrue(success)
        self.assertGreater(len(self.ingestor.content_store), 0)
        self.assertIsNotNone(self.ingestor.last_updated)
        
        # Check content structure
        for entry in self.ingestor.content_store:
            self.assertIn('title', entry)
            self.assertIn('url', entry)
            self.assertIn('text', entry)
            self.assertIn('type', entry)
            self.assertIn('source', entry)
            self.assertEqual(entry['source'], 'healthcare.gov')
    
    def test_glossary_first_ordering(self):
        """Test that glossary entries come first in content store"""
        self.ingestor.ingest_content(use_mock=True)
        
        glossary_entries = [entry for entry in self.ingestor.content_store if entry.get('type') == 'glossary']
        content_entries = [entry for entry in self.ingestor.content_store if entry.get('type') == 'content']
        
        # Should have both types
        self.assertGreater(len(glossary_entries), 0)
        self.assertGreater(len(content_entries), 0)
        
        # Find positions of first glossary and first content entry
        first_glossary_pos = -1
        first_content_pos = -1
        
        for i, entry in enumerate(self.ingestor.content_store):
            if entry.get('type') == 'glossary' and first_glossary_pos == -1:
                first_glossary_pos = i
            elif entry.get('type') == 'content' and first_content_pos == -1:
                first_content_pos = i
            
            if first_glossary_pos != -1 and first_content_pos != -1:
                break
        
        # Glossary should come before content
        if first_glossary_pos != -1 and first_content_pos != -1:
            self.assertLess(first_glossary_pos, first_content_pos)
    
    def test_search_content_basic(self):
        """Test basic content search functionality"""
        self.ingestor.ingest_content(use_mock=True)
        
        # Search for a term that should exist in mock data
        results = self.ingestor.search_content("premium")
        
        self.assertGreater(len(results), 0)
        
        # Check result structure
        for result in results:
            self.assertIn('title', result)
            self.assertIn('url', result)
            self.assertIn('text', result)
            self.assertIn('type', result)
            self.assertIn('relevance_score', result)
            self.assertIn('match_snippet', result)
            self.assertGreater(result['relevance_score'], 0)
    
    def test_search_content_empty_query(self):
        """Test search with empty query"""
        self.ingestor.ingest_content(use_mock=True)
        
        results = self.ingestor.search_content("")
        self.assertEqual(len(results), 0)
        
        results = self.ingestor.search_content("   ")
        self.assertEqual(len(results), 0)
    
    def test_search_content_glossary_priority(self):
        """Test that glossary entries are returned first in search results"""
        self.ingestor.ingest_content(use_mock=True)
        
        # Search for a term that appears in both glossary and content
        results = self.ingestor.search_content("deductible", limit=10)
        
        if len(results) > 1:
            # Check if first results prioritize glossary entries
            glossary_positions = []
            content_positions = []
            
            for i, result in enumerate(results):
                if result.get('type') == 'glossary':
                    glossary_positions.append(i)
                elif result.get('type') == 'content':
                    content_positions.append(i)
            
            # If we have both types, glossary should come first
            if glossary_positions and content_positions:
                self.assertLess(min(glossary_positions), min(content_positions))
    
    def test_search_content_limit(self):
        """Test search result limiting"""
        self.ingestor.ingest_content(use_mock=True)
        
        # Search with different limits
        results_5 = self.ingestor.search_content("health", limit=5)
        results_2 = self.ingestor.search_content("health", limit=2)
        
        self.assertLessEqual(len(results_5), 5)
        self.assertLessEqual(len(results_2), 2)
        
        if len(results_5) >= 2:
            # First 2 results should be the same
            self.assertEqual(results_5[0]['title'], results_2[0]['title'])
            self.assertEqual(results_5[1]['title'], results_2[1]['title'])
    
    def test_search_content_relevance_scoring(self):
        """Test that search results are properly scored for relevance"""
        self.ingestor.ingest_content(use_mock=True)
        
        results = self.ingestor.search_content("premium", limit=10)
        
        if len(results) > 1:
            # Within same type, results should be ordered by relevance
            prev_score = float('inf')
            current_type = None
            
            for result in results:
                if result.get('type') != current_type:
                    # Reset score tracking for new type
                    current_type = result.get('type')
                    prev_score = float('inf')
                
                # Within the same type, scores should be non-increasing
                current_score = result.get('relevance_score', 0)
                self.assertLessEqual(current_score, prev_score)
                prev_score = current_score
    
    def test_create_snippet(self):
        """Test snippet creation functionality"""
        text = "This is a test text about health insurance premiums and how they work with deductibles."
        
        snippet = self.ingestor._create_snippet(text, "premium", 50)
        
        self.assertIn("premium", snippet.lower())
        self.assertLessEqual(len(snippet), 60)  # Allow for ellipsis
        
        # Test with query not in text
        snippet = self.ingestor._create_snippet(text, "nonexistent", 50)
        self.assertLessEqual(len(snippet), 60)
    
    def test_get_content_stats(self):
        """Test content statistics retrieval"""
        # Test with empty content store
        stats = self.ingestor.get_content_stats()
        self.assertEqual(stats['total_entries'], 0)
        self.assertEqual(stats['glossary_entries'], 0)
        self.assertEqual(stats['content_entries'], 0)
        self.assertIsNone(stats['last_updated'])
        
        # Test with content
        self.ingestor.ingest_content(use_mock=True)
        stats = self.ingestor.get_content_stats()
        
        self.assertGreater(stats['total_entries'], 0)
        self.assertGreater(stats['glossary_entries'], 0)
        self.assertGreater(stats['content_entries'], 0)
        self.assertIsNotNone(stats['last_updated'])
        
        # Total should equal sum of parts
        self.assertEqual(
            stats['total_entries'],
            stats['glossary_entries'] + stats['content_entries']
        )
    
    def test_global_ingestor_singleton(self):
        """Test that global ingestor works as singleton"""
        ingestor1 = get_ingestor()
        ingestor2 = get_ingestor()
        
        # Should be the same instance
        self.assertIs(ingestor1, ingestor2)
        
        # Should have content loaded
        self.assertGreater(len(ingestor1.content_store), 0)
    
    def test_fetch_mock_data_structure(self):
        """Test mock data generation and structure"""
        mock_data = self.ingestor.fetch_mock_data()
        
        self.assertGreater(len(mock_data), 0)
        
        # Should have both glossary and content types
        types = set(entry.get('type') for entry in mock_data)
        self.assertIn('glossary', types)
        self.assertIn('content', types)
        
        # All entries should have required fields
        for entry in mock_data:
            self.assertIn('title', entry)
            self.assertIn('url', entry)
            self.assertIn('text', entry)
            self.assertIn('type', entry)
            self.assertIn('source', entry)
            self.assertEqual(entry['source'], 'healthcare.gov')
            
            # Titles and text should not be empty
            self.assertTrue(entry['title'].strip())
            self.assertTrue(entry['text'].strip())
            
            # URLs should be properly formatted
            self.assertTrue(entry['url'].startswith('https://'))

if __name__ == '__main__':
    unittest.main()