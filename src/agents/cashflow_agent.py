import pandas as pd
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

class CompanyCashflow:
    def __init__(self, model="llama3-70b-8192"):
        """Initialize the cashflow agent with the specified model."""
        self.llm = ChatGroq(model=model)
        self.cashflow_data = None
        self.load_cashflow_data()
        
        self.system_prompt = """
        You are an AI-powered Cash Flow & Maturity Agent specializing in bond payment schedules and cash flow analysis.
        Your task is to provide detailed information about bond cash flows, maturity schedules, and payment timelines based on the user's query.
        
        Focus on these aspects:
        1. Payment dates and amounts
        2. Maturity schedules
        3. Cash flow projections
        4. Interest payment details
        5. Yield calculations over time
        
        When responding:
        - Be precise about dates and amounts
        - Explain the cash flow structure clearly
        - Provide a timeline of payments when relevant
        - Calculate present values when appropriate
        
        Format your response as a well-structured cash flow analysis with:
        - Summary of key dates
        - Detailed payment schedule
        - Cash flow visualizations (described in text)
        - Maturity information
        """
        
        self.query_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "Bond ISIN: {isin}\nQuery: {query}\nCash Flow Data: {cashflow_data}"),
            ]
        )
    
    def load_cashflow_data(self):
        """Load cash flow data from CSV file."""
        try:
            data_path = os.path.join(os.path.dirname(__file__), "cashflows_202503011113.csv")
            self.cashflow_data = pd.read_csv(data_path)
            # Convert date strings to datetime objects for easier comparison
            if 'payment_date' in self.cashflow_data.columns:
                self.cashflow_data['payment_date'] = pd.to_datetime(self.cashflow_data['payment_date'])
        except Exception as e:
            print(f"Error loading cash flow data: {e}")
            # Create empty dataframe with expected columns as fallback
            self.cashflow_data = pd.DataFrame(columns=[
                'isin', 'payment_date', 'payment_type', 'amount', 
                'currency', 'record_date'
            ])
    
    def extract_isin(self, query):
        """Extract ISIN from query."""
        # Pattern for Indian ISINs - adjust as needed for different formats
        pattern = r'INE[0-9A-Z]{10}'
        match = re.search(pattern, query)
        if match:
            return match.group(0)
        return None
    
    def get_cashflows(self, isin):
        """Get cash flow data for a specific bond."""
        if self.cashflow_data is None:
            self.load_cashflow_data()
            
        if isin is None:
            return "No ISIN provided to look up cash flows."
            
        bond_cashflows = self.cashflow_data[self.cashflow_data['isin'] == isin]
        
        if len(bond_cashflows) == 0:
            return f"No cash flow data available for bond with ISIN: {isin}"
        
        # Sort by payment date
        bond_cashflows = bond_cashflows.sort_values(by='payment_date')
        
        return bond_cashflows.to_dict(orient='records')
    
    def get_upcoming_payments(self, isin):
        """Get upcoming payments for a specific bond."""
        if self.cashflow_data is None:
            self.load_cashflow_data()
            
        if isin is None:
            return "No ISIN provided to look up upcoming payments."
            
        bond_cashflows = self.cashflow_data[self.cashflow_data['isin'] == isin]
        
        if len(bond_cashflows) == 0:
            return f"No cash flow data available for bond with ISIN: {isin}"
        
        # Get current date
        current_date = datetime.now()
        
        # Filter for upcoming payments
        upcoming_payments = bond_cashflows[bond_cashflows['payment_date'] > current_date]
        
        if len(upcoming_payments) == 0:
            return f"No upcoming payments for bond with ISIN: {isin}"
        
        # Sort by payment date
        upcoming_payments = upcoming_payments.sort_values(by='payment_date')
        
        return upcoming_payments.to_dict(orient='records')
    
    def query(self, user_query):
        """Process a user query about bond cash flows."""
        isin = self.extract_isin(user_query)
        
        if not isin:
            return f"I couldn't identify a specific bond ISIN in your query. Please provide an ISIN for detailed cash flow information."
        
        cashflow_data = self.get_cashflows(isin)
        
        # Check if query is about upcoming payments
        is_upcoming = any(keyword in user_query.lower() for keyword in ["next", "upcoming", "future", "scheduled"])
        
        if is_upcoming:
            cashflow_data = self.get_upcoming_payments(isin)
        
        # Prepare the prompt
        formatted_prompt = {
            "isin": isin,
            "query": user_query,
            "cashflow_data": cashflow_data
        }
        
        # Generate response with LLM
        chain = self.query_prompt | self.llm
        response = chain.invoke(formatted_prompt)
        
        return response.content

if __name__ == "__main__":
    agent = CompanyCashflow()
    result = agent.query("When is the next payment for bond with ISIN INE123456789?")
    print(result) 