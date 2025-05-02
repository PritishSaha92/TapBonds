# ChatBond.ai - Multi-Agent Bond Guidance Framework

A sophisticated AI-powered framework for bond market analysis, search, and advisory capabilities. This multiagent system leverages specialized AI agents to handle different types of bond-related queries effectively.

## Architecture

The framework uses a structured, hierarchical approach with these key components:

1. **Orchestrator Agent**: Routes queries to specialized agents based on the type of query
2. **Bond Directory Agent**: Routes further to Finder or Cashflow agents based on request
3. **Bond Finder Agent**: Finds and compares bonds based on specific criteria
4. **Bond Screener Agent**: Analyzes company financials and bond metrics
5. **Cashflow Agent**: Provides detailed bond cashflow and payment information
6. **Bond Calculator Agent**: Calculates bond prices/yields and provides financial metrics

## Directory Structure

```
ChatBond.ai/
├── app/                      # Web application 
│   ├── app.py                # FastAPI application
│   ├── ui.py                 # Streamlit UI
│   └── templates/            # HTML templates
├── src/                      # Core source code
│   ├── workflow.py           # Main workflow orchestration
│   └── agents/               # Agent implementations
│       ├── orchestratoragent.py    # Query routing
│       ├── bond_directory_agent.py # Directory agent  
│       ├── bond_screener_agent.py  # Financial analysis
│       ├── bond_finder_agent.py    # Bond search/comparison
│       ├── cashflow_agent.py       # Cash flow analysis
│       ├── bond_calculator_agent.py # Price/yield calculations
│       └── websearch.py            # Web search integration
├── data/                     # Data files
│   ├── bonds_details_cleaned.csv  # Bond data
│   ├── bonds_details_202503011115.csv # Full bond database
│   ├── cashflows_202503011113.csv # Cash flow data
│   ├── company_insights_202503011114.csv # Financial metrics
│   └── bond-directory.ipynb # Data preprocessing notebook
├── run_workflow.py           # Command-line interface
└── .env                      # Environment configuration
```

## Technical Highlights

- **Multi-Agent Architecture**: Implements a hierarchical 6-agent system with specialized task routing
- **Advanced Bond Calculations**: Supports multiple day-count methods with <0.1% variance from Excel models
- **AI Integration**: Uses LangChain with Groq's Llama 3-70B model for natural language processing
- **Data Processing**: Handles 22,000+ bond ISINs with comprehensive cashflow and financial data
- **Hybrid Search**: Combines semantic understanding with regex pattern matching for accurate bond queries
- **Web Enhancement**: Enriches responses with real-time market data through web search integration

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your API keys in the `.env` file

### Running the Application

#### Command Line Interface

```bash
# Process a natural language query
python run_workflow.py --query "Find corporate bonds with high yield"

# Get information for a specific bond by ISIN
python run_workflow.py --isin INE123456789

# Compare multiple bonds
python run_workflow.py --compare INE123456789 INE987654321

# Use the bond calculator
python run_workflow.py --calculate --calc-type price
```

#### Web Interface

```bash
# Run the FastAPI backend
uvicorn app.app:app --host 0.0.0.0 --port 8000

# Run the Streamlit UI
streamlit run app/ui.py
```

## Query Processing Flow

1. User submits a query
2. Orchestrator agent classifies query type (0 = Directory, 1 = Screener)
3. If Directory route:
   - Directory agent further classifies (0 = Cashflow, 1 = Finder)
   - Appropriate agent processes query
4. If Screener route:
   - Screener agent analyzes query for financial insights
5. Results are enhanced with web search data
6. Final response is presented to user

## Agent Capabilities

- **Bond Directory Agent**: ISIN lookup, bond details, maturity dates
- **Bond Finder Agent**: Bond comparison, yield evaluation, investment recommendations
- **Bond Screener Agent**: Company financial analysis, performance metrics, risk assessment
- **Cashflow Agent**: Payment schedules, maturity timelines, cash flow projections
- **Bond Calculator Agent**: Price/yield calculations, accrued interest, clean/dirty price computations

## Technologies Used

- LangChain framework for LLM integration
- Groq LLM API (Llama 3-70B model)
- FastAPI for backend API
- Streamlit for user interface
- Pandas for data processing
