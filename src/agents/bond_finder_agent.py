import pandas as pd
import os
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from .websearch import WebAgent

# Load environment variables
load_dotenv()

class BondFinderAgent:
    def __init__(self, model="llama3-70b-8192"):
        """Initialize the bond finder agent with the specified model."""
        self.llm = ChatGroq(model=model)
        self.bond_data = None
        self.load_bond_data()
        
        # Prompt for keyword extraction
        self.keyword_extraction_prompt = """
        Extract key bond search criteria from the following query:
        
        User query: {query}
        
        Return ONLY a JSON object with these keys (include only if present in query):
        - issuer_type: Type of issuer (e.g., corporate, government, municipal)
        - rating: Credit rating criteria (e.g., AAA, AA+, investment grade)
        - yield_min: Minimum yield percentage (number only)
        - yield_max: Maximum yield percentage (number only)
        - maturity_min: Minimum maturity in years (number only)
        - maturity_max: Maximum maturity in years (number only)
        - amount_min: Minimum investment amount (number only)
        - amount_max: Maximum investment amount (number only)
        - issuer_name: Specific company name if mentioned
        - industry: Industry sector if mentioned
        
        For example: {"issuer_type": "corporate", "rating": "AAA", "yield_min": 5}
        """
        
        self.system_prompt = """
        You are an AI-powered Bond Finder Agent specializing in finding and comparing bonds based on user criteria.
        Your task is to identify the best bonds matching the given criteria and explain their attributes, incorporating real-time market context from web search results.
        
        Focus on these aspects:
        1. Yield comparison and benchmarking
        2. Credit quality assessment
        3. Maturity profile evaluation
        4. Liquidity considerations
        5. Value and relative pricing analysis
        
        When responding:
        - Incorporate the provided web search context into your analysis.
        - Clearly rank the bonds you recommend
        - Explain why each recommended bond matches the criteria
        - Highlight advantages and risks of each recommendation
        - Explain any trade-offs between different options
        
        Format your response as a well-structured recommendation with:
        - Summary of search criteria used
        - Top bond recommendations with key details
        - A brief analysis of current market context based on web results
        - Comparative analysis between options
        - Additional considerations for the investor
        """
        
        self.query_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "Search Criteria: {search_criteria}\nQuery: {query}\nMatching Bonds: {matching_bonds}\n\nWeb Search Context:\n{web_context}"),
            ]
        )
    
    def load_bond_data(self):
        """
        Load bond data from CSV file.
        Note: This is a representative sample of a larger dataset containing over 22,000 ISINs.
        """
        try:
            data_path = os.path.join(os.path.dirname(__file__), "bonds_details_cleaned.csv")
            self.bond_data = pd.read_csv(data_path)
            # Additional data processing if needed
            # Convert maturity_date to datetime if it exists
            if 'maturity_date' in self.bond_data.columns:
                self.bond_data['maturity_date'] = pd.to_datetime(self.bond_data['maturity_date'], errors='coerce')
        except Exception as e:
            print(f"Error loading bond data: {e}")
            # Create empty dataframe with expected columns as fallback
            self.bond_data = pd.DataFrame(columns=[
                'isin', 'company_name', 'issue_size', 'maturity_date', 
                'credit_rating', 'coupon_rate', 'yield_to_maturity'
            ])
    
    def extract_search_criteria(self, query: str) -> Dict[str, Any]:
        """Extract search criteria from user query using the LLM."""
        try:
            # Create a simple LLM chain for criteria extraction
            criteria_prompt = ChatPromptTemplate.from_template(self.keyword_extraction_prompt)
            criteria_chain = criteria_prompt | self.llm
            
            # Extract criteria
            result = criteria_chain.invoke({"query": query})
            
            # Parse the result (assuming the LLM returns a JSON-like string)
            criteria_text = result.content.strip()
            
            # Extract JSON from the response (handling potential formatting issues)
            json_match = re.search(r'\{.*\}', criteria_text, re.DOTALL)
            if json_match:
                criteria_text = json_match.group(0)
            
            # Convert to dictionary using safer eval approach
            import json
            try:
                criteria = json.loads(criteria_text)
            except json.JSONDecodeError:
                print(f"Error parsing criteria JSON: {criteria_text}")
                criteria = {}
            
            return criteria
        except Exception as e:
            print(f"Error extracting search criteria: {e}")
            return {}
    
    def filter_bonds(self, criteria: Dict[str, Any]) -> pd.DataFrame:
        """Filter bonds based on the extracted criteria."""
        if self.bond_data is None or len(self.bond_data) == 0:
            return pd.DataFrame()
        
        # Start with all bonds
        filtered_bonds = self.bond_data.copy()
        
        # Apply filters based on criteria
        if 'issuer_name' in criteria and criteria['issuer_name']:
            issuer_pattern = re.compile(re.escape(criteria['issuer_name']), re.IGNORECASE)
            filtered_bonds = filtered_bonds[filtered_bonds['company_name'].str.contains(issuer_pattern, na=False)]
        
        if 'issuer_type' in criteria and criteria['issuer_type']:
            # This assumes there's a column for issuer type
            if 'issuer_type' in filtered_bonds.columns:
                issuer_type_pattern = re.compile(re.escape(criteria['issuer_type']), re.IGNORECASE)
                filtered_bonds = filtered_bonds[filtered_bonds['issuer_type'].str.contains(issuer_type_pattern, na=False)]
        
        if 'rating' in criteria and criteria['rating']:
            # This assumes there's a column for credit rating
            if 'credit_rating' in filtered_bonds.columns:
                rating_pattern = re.compile(re.escape(criteria['rating']), re.IGNORECASE)
                filtered_bonds = filtered_bonds[filtered_bonds['credit_rating'].str.contains(rating_pattern, na=False)]
        
        if 'yield_min' in criteria and criteria['yield_min'] is not None:
            # This assumes there's a column for yield to maturity
            if 'yield_to_maturity' in filtered_bonds.columns:
                try:
                    yield_min = float(criteria['yield_min'])
                    filtered_bonds = filtered_bonds[filtered_bonds['yield_to_maturity'] >= yield_min]
                except (ValueError, TypeError):
                    pass
        
        if 'yield_max' in criteria and criteria['yield_max'] is not None:
            # This assumes there's a column for yield to maturity
            if 'yield_to_maturity' in filtered_bonds.columns:
                try:
                    yield_max = float(criteria['yield_max'])
                    filtered_bonds = filtered_bonds[filtered_bonds['yield_to_maturity'] <= yield_max]
                except (ValueError, TypeError):
                    pass
        
        # Additional filters for maturity, amount, industry, etc. would go here
        
        return filtered_bonds
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a bond finder query and return matching bonds."""
        # Extract search criteria from the query
        search_criteria = self.extract_search_criteria(query)
        
        # Filter bonds based on criteria
        matching_bonds = self.filter_bonds(search_criteria)

        # Get live web context
        web_agent = WebAgent()
        web_query = f"current market trends for {search_criteria.get('issuer_type', 'corporate')} bonds"
        web_context = web_agent.get_info(web_query)
        
        # Prepare the formatted result
        formatted_prompt = {
            "search_criteria": search_criteria,
            "query": query,
            "matching_bonds": matching_bonds.to_dict(orient='records'),
            "web_context": web_context
        }
        
        # Generate response with LLM
        chain = self.query_prompt | self.llm
        response = chain.invoke(formatted_prompt)
        
        # Return the result
        return {
            "keywords": search_criteria,
            "count": len(matching_bonds),
            "results": matching_bonds,
            "response": response.content,
            "web_context": web_context
        }
    
    def answer(self, query: str) -> str:
        """Alternative method to directly answer queries about bonds."""
        result = self.process_query(query)
        return result["response"]

if __name__ == "__main__":
    agent = BondFinderAgent()
    result = agent.process_query("Find corporate bonds with at least 5% yield and AAA rating")
    print(f"Found {result['count']} matching bonds")
    print("\n--- Web Context ---")
    print(result['web_context'])
    print("\n--- LLM Response ---")
    print(result["response"]) 