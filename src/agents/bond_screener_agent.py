import pandas as pd
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

class BondScreenerAgent:
    def __init__(self, model = "llama3-70b-8192"):
        """
        Initializes the BondQueryRouter with a language model.
        """
        self.llm = ChatGroq(model=model)
        self.bond_data = None
        self.load_bond_data()
        
        self.system_prompt = """
        You are an AI-powered Bond Screener Agent specializing in company-level financial analysis for bond-issuing firms.
        Your task is to provide comprehensive financial insights based on the user's query.
        
        Consider these aspects in your analysis:
        1. Credit ratings and their implications
        2. Financial health indicators
        3. Industry performance metrics
        4. Yield comparisons
        5. Risk assessment
        
        When responding:
        - Provide a thorough analysis based on available data
        - Explain financial metrics in clear terms
        - Compare relevant bonds when appropriate
        - Suggest additional factors to consider
        
        Format your response as a well-structured financial analysis report with:
        - Overview summary
        - Key financial indicators
        - Risk assessment
        - Recommendations (when appropriate)
        """

        self.query_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "Company: {company_name}\nQuery: {query}\nAvailable Data: {company_data}"),
            ]
        )

    def load_bond_data(self):
        """Load bond data from the dataset."""
        try:
            data_path = os.path.join(os.path.dirname(__file__), "bonds_details_cleaned.csv")
            self.bond_data = pd.read_csv(data_path)
            # Additional data processing if needed
        except Exception as e:
            print(f"Error loading bond data: {e}")
            # Create empty dataframe with expected columns as fallback
            self.bond_data = pd.DataFrame(columns=[
                'isin', 'company_name', 'issue_size', 'maturity_date', 
                'credit_rating', 'coupon_rate', 'yield_to_maturity'
            ])

    def get_company_data(self, company_name):
        """Extract company data from the dataset."""
        if self.bond_data is None:
            self.load_bond_data()
            
        # Try exact match first
        company_bonds = self.bond_data[self.bond_data['company_name'] == company_name]
        
        # If no exact match, try partial match
        if len(company_bonds) == 0:
            pattern = re.compile(re.escape(company_name), re.IGNORECASE)
            company_bonds = self.bond_data[self.bond_data['company_name'].str.contains(pattern, na=False)]
        
        if len(company_bonds) == 0:
            return "No data available for this company."
        
        return company_bonds.to_dict(orient='records')

    def extract_company_name(self, query):
        """Extract company name from query."""
        # Simple pattern matching - in production would use NER or more sophisticated extraction
        patterns = [
            r"(?:analysis|information|details|overview|financial metrics)\s+(?:of|for|about)\s+([A-Za-z0-9\s]+(?:Limited|Ltd|Inc|Corporation|Corp|Company|Co))",
            r"([A-Za-z0-9\s]+(?:Limited|Ltd|Inc|Corporation|Corp|Company|Co))'s\s+(?:financial|bond|credit)",
            r"How\s+(?:is|are)\s+([A-Za-z0-9\s]+(?:Limited|Ltd|Inc|Corporation|Corp|Company|Co))"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
        
        # If no company is found, use a default fallback
        return None

    def query(self, user_query):
        """Process a user query about bond screening or company financial analysis."""
        company_name = self.extract_company_name(user_query)
        
        if not company_name:
            # If company name can't be extracted, use a generic response
            return f"I couldn't identify a specific company in your query. Please specify a company name for a detailed financial analysis."
        
        company_data = self.get_company_data(company_name)
        
        # Prepare the prompt
        formatted_prompt = {
            "company_name": company_name,
            "query": user_query,
            "company_data": company_data
        }
        
        # Generate response with LLM
        chain = self.query_prompt | self.llm
        response = chain.invoke(formatted_prompt)
        
        return response.content

if __name__ == "__main__":
    agent = BondScreenerAgent()
    result = agent.query("Provide financial analysis for Urgo Capital Limited bonds")
    print(result) 