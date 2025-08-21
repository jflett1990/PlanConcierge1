"""
LLM Tool Binding System for Plan Concierge

This module provides OpenAI function calling tools that wrap our internal APIs
to provide intelligent plan explanations and healthcare content search.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Internal API imports
from worker.hcgov_ingest import get_ingestor
from models import Plan
from integrations.provider_formulary import check_providers, check_rx, get_provider_summary, get_rx_summary

def hcgov_content_search(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search healthcare.gov content and glossary
    
    Args:
        query: Search query string
        limit: Maximum number of results (default: 5)
        
    Returns:
        Dictionary with search results and metadata
    """
    try:
        ingestor = get_ingestor()
        results = ingestor.search_content(query, limit)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'text': result.get('match_snippet', result.get('text', '')),
                'type': result.get('type', ''),
                'source': result.get('source', ''),
                'relevance_score': result.get('relevance_score', 0)
            })
        
        stats = ingestor.get_content_stats()
        
        return {
            'success': True,
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results),
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error in hcgov_content_search: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': [],
            'total_results': 0
        }

def plans_lookup(zip_code: str = None, county: str = None, year: int = 2024, 
                metal: str = None, issuer: str = None, limit: int = 10) -> Dict[str, Any]:
    """
    Look up available health insurance plans with filtering
    
    Args:
        zip_code: ZIP code for location filtering
        county: County name for location filtering  
        year: Plan year (default: 2024)
        metal: Metal level filter (Bronze, Silver, Gold, Platinum)
        issuer: Insurance issuer filter
        limit: Maximum number of plans to return
        
    Returns:
        Dictionary with filtered plan data
    """
    try:
        from api.plans import filter_plans_by_location
        
        # Get all plans for the year
        plans = Plan.list_by_year(year)
        
        # Apply location filtering if specified
        if zip_code or county:
            plans = filter_plans_by_location(plans, zip_code, county)
        
        # Apply additional filters
        if metal:
            plans = [p for p in plans if p.metal.lower() == metal.lower()]
        
        if issuer:
            plans = [p for p in plans if issuer.lower() in p.issuer.lower()]
        
        # Limit results
        plans = plans[:limit]
        
        # Format response
        plan_data = []
        for plan in plans:
            plan_data.append({
                'id': plan.id,
                'plan_year': plan.plan_year,
                'issuer': plan.issuer,
                'name': plan.name,
                'metal': plan.metal,
                'premium_full': plan.premium_full,
                'deductible': plan.deductible,
                'moop': plan.moop,
                'csr_flag': plan.csr_flag
            })
        
        return {
            'success': True,
            'data': plan_data,
            'count': len(plan_data),
            'filters_applied': {
                'zip_code': zip_code,
                'county': county,
                'year': year,
                'metal': metal,
                'issuer': issuer
            }
        }
        
    except Exception as e:
        logger.error(f"Error in plans_lookup: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': [],
            'count': 0
        }

def networks_formularies_check(plan_ids: List[str], npi_list: List[str] = None, 
                              rx_list: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Check provider networks and formulary coverage for given plans
    
    Args:
        plan_ids: List of plan IDs to check
        npi_list: List of provider NPIs (optional)
        rx_list: List of prescriptions with rxcui, name, dosage, frequency (optional)
        
    Returns:
        Dictionary with provider and formulary coverage results
    """
    try:
        results = {
            'success': True,
            'plan_ids': plan_ids,
            'provider_results': {},
            'rx_results': {},
            'summaries': {}
        }
        
        # Check provider networks if NPIs provided
        if npi_list:
            provider_results = check_providers(plan_ids, npi_list)
            results['provider_results'] = provider_results
            
            # Generate summaries for each plan
            for plan_id in plan_ids:
                if plan_id in provider_results:
                    summary = get_provider_summary(provider_results[plan_id])
                    if 'summaries' not in results:
                        results['summaries'] = {}
                    if plan_id not in results['summaries']:
                        results['summaries'][plan_id] = {}
                    results['summaries'][plan_id]['provider'] = summary
        
        # Check formulary coverage if prescriptions provided
        if rx_list:
            rx_results = check_rx(plan_ids, rx_list)
            results['rx_results'] = rx_results
            
            # Generate summaries for each plan
            for plan_id in plan_ids:
                if plan_id in rx_results:
                    summary = get_rx_summary(rx_results[plan_id])
                    if 'summaries' not in results:
                        results['summaries'] = {}
                    if plan_id not in results['summaries']:
                        results['summaries'][plan_id] = {}
                    results['summaries'][plan_id]['rx'] = summary
        
        return results
        
    except Exception as e:
        logger.error(f"Error in networks_formularies_check: {e}")
        return {
            'success': False,
            'error': str(e),
            'plan_ids': plan_ids,
            'provider_results': {},
            'rx_results': {},
            'summaries': {}
        }

# OpenAI Tool Definitions
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "hcgov_content_search",
            "description": "Search healthcare.gov content and glossary for definitions and explanations",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for healthcare terms or concepts"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plans_lookup",
            "description": "Look up and filter available health insurance plans",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {
                        "type": "string",
                        "description": "ZIP code for location-based filtering"
                    },
                    "county": {
                        "type": "string", 
                        "description": "County name for location-based filtering"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Plan year (default: 2024)",
                        "default": 2024
                    },
                    "metal": {
                        "type": "string",
                        "description": "Metal level filter: Bronze, Silver, Gold, or Platinum"
                    },
                    "issuer": {
                        "type": "string",
                        "description": "Insurance issuer name filter"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of plans to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "networks_formularies_check",
            "description": "Check provider network participation and prescription drug coverage for health plans",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of plan IDs to check"
                    },
                    "npi_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of provider NPI numbers (optional)"
                    },
                    "rx_list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rxcui": {"type": "string"},
                                "name": {"type": "string"},
                                "dosage": {"type": "string"},
                                "frequency": {"type": "string"}
                            }
                        },
                        "description": "List of prescription medications (optional)"
                    }
                },
                "required": ["plan_ids"]
            }
        }
    }
]

# System prompt for the Plan Concierge
SYSTEM_PROMPT = """You are 'James's Plan Concierge.' You are an expert health insurance advisor who helps people understand their coverage options.

**Core Guidelines:**
- Use your tools to gather facts from authoritative sources
- Never fabricate information - always use tools for current data
- Cite healthcare.gov glossary definitions and content when available
- Always include a "What this means for you" section with practical implications
- End responses with the disclaimer: "Networks and formularies change. Verify at enrollment."

**Output Format:**
Always respond with valid JSON in this exact structure:
{
  "title": "Clear, descriptive title",
  "sections": [
    {
      "heading": "Section heading",
      "body": "Detailed explanation with practical insights"
    }
  ],
  "citations": [
    {
      "title": "Source title",
      "url": "https://healthcare.gov/..."
    }
  ]
}

**Response Templates:**

1) **Definition Template** - Use for explaining insurance terms:
   - Title: "Understanding [Term]"
   - Sections: Definition, Key Details, What this means for you
   - Always search healthcare.gov first for official definitions

2) **Plan Explanation Template** - Use for analyzing specific plans:
   - Title: "[Plan Name] Analysis"
   - Sections: Plan Overview, Costs & Coverage, Network & Formulary, What this means for you
   - Include provider network and prescription coverage when relevant

3) **Top 3 Summary Template** - Use for comparing multiple plans:
   - Title: "Your Top 3 Plan Options"
   - Sections: Plan Comparison Overview, Plan 1 Details, Plan 2 Details, Plan 3 Details, What this means for you
   - Rank by fit score and explain trade-offs

**Important:**
- Use tools before responding to ensure accuracy
- Focus on practical implications for the user
- Be clear about costs, coverage, and limitations
- Always verify information is current and accurate"""

def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call by name with given arguments
    
    Args:
        tool_name: Name of the tool to call
        arguments: Arguments to pass to the tool
        
    Returns:
        Tool execution result
    """
    try:
        if tool_name == "hcgov_content_search":
            return hcgov_content_search(**arguments)
        elif tool_name == "plans_lookup":
            return plans_lookup(**arguments)
        elif tool_name == "networks_formularies_check":
            return networks_formularies_check(**arguments)
        else:
            return {
                'success': False,
                'error': f'Unknown tool: {tool_name}'
            }
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def call_plan_concierge_llm(user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call the Plan Concierge LLM with tool access
    
    Args:
        user_message: User's question or request
        context: Additional context (client info, intake data, etc.)
        
    Returns:
        Structured response from the Plan Concierge
    """
    if not openai_client:
        return {
            'success': False,
            'error': 'OpenAI API key not configured'
        }
    
    try:
        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add context if provided
        if context:
            context_message = f"Context: {json.dumps(context, indent=2)}"
            messages.append({"role": "user", "content": context_message})
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        # Make initial LLM call with tools
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=2000,
            temperature=0.3
        )
        
        # Handle tool calls
        message = response.choices[0].message
        
        if message.tool_calls:
            # Execute tool calls
            tool_results = []
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                result = execute_tool_call(tool_name, arguments)
                tool_results.append({
                    'tool_call_id': tool_call.id,
                    'tool_name': tool_name,
                    'result': result
                })
            
            # Add tool results to conversation
            messages.append(message)
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result['tool_call_id'],
                    "content": json.dumps(tool_result['result'])
                })
            
            # Make final call for structured response
            final_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            response_content = final_response.choices[0].message.content
            try:
                parsed_response = json.loads(response_content)
                return {
                    'success': True,
                    'response': parsed_response,
                    'tool_calls_made': len(tool_results)
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return {
                    'success': False,
                    'error': 'Invalid JSON response from LLM',
                    'raw_response': response_content
                }
        
        else:
            # No tool calls needed, direct response
            try:
                # Request JSON format for consistency
                json_request = f"{user_message}\n\nPlease respond in the required JSON format."
                messages[-1]['content'] = json_request
                
                json_response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                response_content = json_response.choices[0].message.content
                parsed_response = json.loads(response_content)
                
                return {
                    'success': True,
                    'response': parsed_response,
                    'tool_calls_made': 0
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse direct JSON response: {e}")
                return {
                    'success': False,
                    'error': 'Invalid JSON response from LLM',
                    'raw_response': response_content
                }
        
    except Exception as e:
        logger.error(f"Error in call_plan_concierge_llm: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# Template functions for common use cases
def define_term(term: str) -> Dict[str, Any]:
    """Generate definition response for insurance term"""
    return call_plan_concierge_llm(f"Please explain the health insurance term '{term}' using the definition template.")

def explain_plan(plan_id: str, client_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate plan explanation with client context"""
    context_str = ""
    if client_context:
        context_str = f" for a client with this profile: {json.dumps(client_context)}"
    
    return call_plan_concierge_llm(
        f"Please analyze plan ID '{plan_id}' using the plan explanation template{context_str}.",
        context=client_context
    )

def summarize_top3_plans(plan_ids: List[str], client_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate top 3 plan comparison summary"""
    plans_str = ", ".join(plan_ids)
    context_str = ""
    if client_context:
        context_str = f" for a client with this profile: {json.dumps(client_context)}"
    
    return call_plan_concierge_llm(
        f"Please compare and summarize these top 3 plans: {plans_str} using the top 3 summary template{context_str}.",
        context=client_context
    )