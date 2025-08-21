"""
Healthcare.gov Content Ingestion Worker

This module fetches glossary and content data from healthcare.gov APIs
and provides search functionality for the ingested content.
"""

import requests
import logging
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthcareGovIngestor:
    """
    Handles fetching and storing content from healthcare.gov APIs
    """
    
    def __init__(self):
        self.base_url = "https://www.healthcare.gov"
        self.api_base = "https://www.healthcare.gov/api"
        self.content_store: List[Dict[str, Any]] = []
        self.last_updated: Optional[float] = None
        
    def fetch_glossary(self) -> List[Dict[str, Any]]:
        """
        Fetch glossary terms from healthcare.gov
        
        Returns:
            List of glossary entries with title, url, and text
        """
        try:
            # Healthcare.gov glossary API endpoint
            glossary_url = f"{self.api_base}/glossary.json"
            
            logger.info(f"Fetching glossary from {glossary_url}")
            response = requests.get(glossary_url, timeout=30)
            response.raise_for_status()
            
            glossary_data = response.json()
            glossary_entries = []
            
            # Process glossary entries
            if isinstance(glossary_data, list):
                for entry in glossary_data:
                    if isinstance(entry, dict):
                        glossary_entries.append({
                            'title': entry.get('title', '').strip(),
                            'url': urljoin(self.base_url, entry.get('url', '')),
                            'text': entry.get('plain_language_definition', entry.get('definition', '')).strip(),
                            'type': 'glossary',
                            'source': 'healthcare.gov'
                        })
            elif isinstance(glossary_data, dict):
                # Handle different API response formats
                entries = glossary_data.get('glossary', glossary_data.get('data', []))
                for entry in entries:
                    if isinstance(entry, dict):
                        glossary_entries.append({
                            'title': entry.get('title', entry.get('term', '')).strip(),
                            'url': urljoin(self.base_url, entry.get('url', entry.get('link', ''))),
                            'text': entry.get('plain_language_definition', 
                                           entry.get('definition', 
                                           entry.get('description', ''))).strip(),
                            'type': 'glossary',
                            'source': 'healthcare.gov'
                        })
            
            logger.info(f"Successfully fetched {len(glossary_entries)} glossary entries")
            return glossary_entries
            
        except requests.RequestException as e:
            logger.error(f"Error fetching glossary: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error processing glossary: {e}")
            return []
    
    def fetch_content_index(self) -> List[Dict[str, Any]]:
        """
        Fetch content index from healthcare.gov
        
        Returns:
            List of content entries with title, url, and text
        """
        try:
            # Healthcare.gov content/topics API endpoint
            content_urls = [
                f"{self.api_base}/topics.json",
                f"{self.api_base}/articles.json",
                f"{self.api_base}/blog.json"
            ]
            
            content_entries = []
            
            for content_url in content_urls:
                try:
                    logger.info(f"Fetching content from {content_url}")
                    response = requests.get(content_url, timeout=30)
                    response.raise_for_status()
                    
                    content_data = response.json()
                    
                    # Process content entries
                    entries = []
                    if isinstance(content_data, list):
                        entries = content_data
                    elif isinstance(content_data, dict):
                        entries = content_data.get('articles', content_data.get('topics', content_data.get('posts', [])))
                    
                    for entry in entries:
                        if isinstance(entry, dict):
                            # Extract text content from various possible fields
                            text_content = ""
                            for field in ['excerpt', 'summary', 'description', 'content', 'body']:
                                if entry.get(field):
                                    text_content = entry[field].strip()
                                    break
                            
                            content_entries.append({
                                'title': entry.get('title', '').strip(),
                                'url': urljoin(self.base_url, entry.get('url', entry.get('link', ''))),
                                'text': text_content,
                                'type': 'content',
                                'source': 'healthcare.gov',
                                'category': entry.get('category', entry.get('topic', 'general'))
                            })
                    
                    logger.info(f"Fetched {len(entries)} entries from {content_url}")
                    
                except requests.RequestException as e:
                    logger.warning(f"Could not fetch {content_url}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing {content_url}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(content_entries)} content entries total")
            return content_entries
            
        except Exception as e:
            logger.error(f"Unexpected error fetching content: {e}")
            return []
    
    def fetch_mock_data(self) -> List[Dict[str, Any]]:
        """
        Generate realistic mock healthcare.gov content for development/testing
        This provides authentic-looking data structure while APIs are being set up
        """
        logger.info("Using mock healthcare.gov data for development")
        
        mock_glossary = [
            {
                'title': 'Premium',
                'url': 'https://www.healthcare.gov/glossary/premium/',
                'text': 'The amount you pay for your health insurance every month. In addition to your premium, you usually have to pay other costs for your health care, including a deductible, copayments, and coinsurance.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            },
            {
                'title': 'Deductible',
                'url': 'https://www.healthcare.gov/glossary/deductible/',
                'text': 'The amount you owe for health care services your health insurance or plan covers before your health insurance or plan begins to pay. For example, if your deductible is $1,000, your plan won\'t pay anything until you\'ve met your $1,000 deductible for covered health care services subject to the deductible.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            },
            {
                'title': 'Copayment',
                'url': 'https://www.healthcare.gov/glossary/copayment/',
                'text': 'A fixed amount ($20, for example) you pay for a covered health care service after you\'ve paid your deductible. The amount can vary by the type of covered health care service.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            },
            {
                'title': 'Coinsurance',
                'url': 'https://www.healthcare.gov/glossary/coinsurance/',
                'text': 'The percentage of costs of a covered health care service you pay (20%, for example) after you\'ve paid your deductible. Let\'s say your health insurance plan\'s allowed amount for an office visit is $100 and your coinsurance is 20%. If you\'ve paid your deductible: You pay 20% of $100, or $20. The insurance company pays the rest.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            },
            {
                'title': 'Out-of-pocket maximum',
                'url': 'https://www.healthcare.gov/glossary/out-of-pocket-maximum-limit/',
                'text': 'The most you have to pay for covered services in a plan year. After you spend this amount on deductibles, copayments, and coinsurance for in-network care and services, your health plan pays 100% of the costs of covered benefits.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            },
            {
                'title': 'Network',
                'url': 'https://www.healthcare.gov/glossary/network/',
                'text': 'The facilities, providers and suppliers your health insurer or plan has contracted with to provide health care services.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            },
            {
                'title': 'Essential Health Benefits',
                'url': 'https://www.healthcare.gov/glossary/essential-health-benefits/',
                'text': 'A set of health care service categories that must be covered by certain plans, starting in 2014. These categories are: ambulatory patient services; emergency services; hospitalization; maternity and newborn care; mental health and substance use disorder services, including behavioral health treatment; prescription drugs; rehabilitative and habilitative services and devices; laboratory services; preventive and wellness services and chronic disease management; and pediatric services, including oral and vision care.',
                'type': 'glossary',
                'source': 'healthcare.gov'
            }
        ]
        
        mock_content = [
            {
                'title': 'How to apply for health coverage',
                'url': 'https://www.healthcare.gov/apply-and-enroll/how-to-apply/',
                'text': 'Learn the steps to apply for health insurance coverage through the Health Insurance Marketplace. You can apply online, by phone, or with the help of a trained assister in your community.',
                'type': 'content',
                'source': 'healthcare.gov',
                'category': 'enrollment'
            },
            {
                'title': 'Choosing a health plan',
                'url': 'https://www.healthcare.gov/choose-a-plan/',
                'text': 'When choosing a health insurance plan, consider the total cost, not just the premium. Look at deductibles, copayments, coinsurance, and out-of-pocket maximums. Also check if your doctors and prescriptions are covered.',
                'type': 'content',
                'source': 'healthcare.gov',
                'category': 'plan-selection'
            },
            {
                'title': 'Qualifying life events',
                'url': 'https://www.healthcare.gov/glossary/qualifying-life-event/',
                'text': 'A change in your life that can make you eligible for a Special Enrollment Period, allowing you to enroll in health coverage outside of the annual Open Enrollment Period. Examples include losing health coverage, moving, getting married, having a baby, or adopting a child.',
                'type': 'content',
                'source': 'healthcare.gov',
                'category': 'enrollment'
            },
            {
                'title': 'Preventive care benefits',
                'url': 'https://www.healthcare.gov/preventive-care-benefits/',
                'text': 'Health plans must cover certain preventive services without charging a copayment or coinsurance, even if you haven\'t met your deductible. This includes immunizations, screenings, and counseling services.',
                'type': 'content',
                'source': 'healthcare.gov',
                'category': 'benefits'
            }
        ]
        
        return mock_glossary + mock_content
    
    def ingest_content(self, use_mock: bool = False) -> bool:
        """
        Ingest content from healthcare.gov APIs or mock data
        
        Args:
            use_mock: Whether to use mock data instead of real API calls
            
        Returns:
            True if ingestion was successful, False otherwise
        """
        try:
            logger.info("Starting healthcare.gov content ingestion")
            
            if use_mock:
                # Use mock data for development
                all_content = self.fetch_mock_data()
            else:
                # Fetch real data from APIs
                glossary_entries = self.fetch_glossary()
                content_entries = self.fetch_content_index()
                
                # Combine all content with glossary first (as requested)
                all_content = glossary_entries + content_entries
            
            # Filter out entries without title or text
            valid_content = [
                entry for entry in all_content 
                if entry.get('title') and entry.get('text')
            ]
            
            # Store in memory
            self.content_store = valid_content
            self.last_updated = time.time()
            
            logger.info(f"Successfully ingested {len(valid_content)} content entries")
            logger.info(f"Glossary entries: {len([c for c in valid_content if c.get('type') == 'glossary'])}")
            logger.info(f"Content entries: {len([c for c in valid_content if c.get('type') == 'content'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during content ingestion: {e}")
            return False
    
    def search_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search ingested content for matching entries
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching content entries, with glossary entries first
        """
        if not query.strip():
            return []
        
        query_lower = query.lower().strip()
        matches = []
        
        # Search through content store
        for entry in self.content_store:
            score = 0
            
            # Title match (highest priority)
            title = entry.get('title', '').lower()
            if query_lower in title:
                score += 10
                if title.startswith(query_lower):
                    score += 5  # Bonus for prefix match
            
            # Text content match
            text = entry.get('text', '').lower()
            if query_lower in text:
                score += 5
                # Bonus for multiple occurrences
                score += min(text.count(query_lower) - 1, 3)
            
            # Category/type bonus for relevant searches
            category = entry.get('category', '').lower()
            if query_lower in category:
                score += 2
            
            if score > 0:
                matches.append({
                    **entry,
                    'relevance_score': score,
                    'match_snippet': self._create_snippet(entry.get('text', ''), query_lower)
                })
        
        # Sort by type (glossary first) then by relevance score
        matches.sort(key=lambda x: (
            0 if x.get('type') == 'glossary' else 1,  # Glossary first
            -x.get('relevance_score', 0)  # Then by relevance (descending)
        ))
        
        return matches[:limit]
    
    def _create_snippet(self, text: str, query: str, snippet_length: int = 200) -> str:
        """
        Create a text snippet highlighting the search query
        
        Args:
            text: Full text content
            query: Search query
            snippet_length: Maximum length of snippet
            
        Returns:
            Text snippet with query context
        """
        if not text or not query:
            return text[:snippet_length] + ('...' if len(text) > snippet_length else '')
        
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Find first occurrence of query
        query_pos = text_lower.find(query_lower)
        if query_pos == -1:
            return text[:snippet_length] + ('...' if len(text) > snippet_length else '')
        
        # Calculate snippet start and end
        start = max(0, query_pos - snippet_length // 3)
        end = min(len(text), start + snippet_length)
        
        # Adjust start to word boundary if possible
        if start > 0:
            space_pos = text.find(' ', start)
            if space_pos != -1 and space_pos < start + 20:
                start = space_pos + 1
        
        snippet = text[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'
        
        return snippet
    
    def get_content_stats(self) -> Dict[str, Any]:
        """
        Get statistics about ingested content
        
        Returns:
            Dictionary with content statistics
        """
        if not self.content_store:
            return {
                'total_entries': 0,
                'glossary_entries': 0,
                'content_entries': 0,
                'last_updated': None
            }
        
        return {
            'total_entries': len(self.content_store),
            'glossary_entries': len([c for c in self.content_store if c.get('type') == 'glossary']),
            'content_entries': len([c for c in self.content_store if c.get('type') == 'content']),
            'last_updated': self.last_updated
        }

# Global ingestor instance
_ingestor = None

def get_ingestor() -> HealthcareGovIngestor:
    """Get or create the global ingestor instance"""
    global _ingestor
    if _ingestor is None:
        _ingestor = HealthcareGovIngestor()
        # Initialize with mock data for development
        _ingestor.ingest_content(use_mock=True)
    return _ingestor