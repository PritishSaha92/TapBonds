import os
import sys
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow import BondWorkflowChain
from src.agents.bond_calculator_agent import BondCalculatorAgent

app = FastAPI()

class QueryRequest(BaseModel):
    user_query: str

class QueryResponse(BaseModel):
    response: str

class BondRequest(BaseModel):
    isin: str
    calculation_type: str
    investment_date: str
    units: int
    input_value: float
    bond_data: Dict[str, Any]

# Initialize the workflow chain
workflow_chain = BondWorkflowChain()

@app.post("/process_query", response_model=QueryResponse)
def process_query(request: QueryRequest) -> Any:
    """
    Endpoint to process a bond-related query.

    Args:
        request (QueryRequest): The user's bond-related query

    Returns:
        QueryResponse: The final response from the appropriate agent
    """
    try:
        result = workflow_chain.process_query(request.user_query)
        return QueryResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate")
async def calculate_bond(request: BondRequest):
    """
    Endpoint to calculate bond price or yield.
    
    Args:
        request (BondRequest): Bond calculation parameters
        
    Returns:
        Dict: Calculation results
    """
    try:
        calculator = BondCalculatorAgent(
            current_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_user="api_user"
        )
        
        calculation_result = calculator.process_calculation_request(request.dict())
        
        return {
            "status": "success",
            "result": calculation_result,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calculation failed: {str(e)}"
        )

@app.get("/")
def root():
    """Root endpoint that returns basic API information."""
    return {
        "message": "Bond Guidance Framework API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/process_query", "method": "POST", "description": "Process a bond-related query"},
            {"path": "/calculate", "method": "POST", "description": "Calculate bond price or yield"},
            {"path": "/", "method": "GET", "description": "API information"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 