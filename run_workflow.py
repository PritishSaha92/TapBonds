#!/usr/bin/env python
"""
Command-line script to run the Multi-Agent Bond Guidance Framework
"""
import argparse
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Import the workflow chain
from src.workflow import BondWorkflowChain

def main():
    """
    Main entry point for the command-line interface
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Multi-Agent Bond Guidance Framework')
    parser.add_argument('--query', type=str, help='Natural language query about bonds')
    parser.add_argument('--isin', type=str, help='ISIN code for a specific bond')
    parser.add_argument('--compare', type=str, nargs='+', help='List of ISINs to compare')
    parser.add_argument('--calculate', action='store_true', help='Use the bond calculator')
    parser.add_argument('--calc-type', type=str, choices=['price', 'yield'], 
                        help='Calculation type for bond calculator (price or yield)')
    parser.add_argument('--agent', type=str, choices=['directory', 'finder', 'cashflow', 'screener', 'calculator'], 
                        help='Directly use a specific agent')
    
    args = parser.parse_args()
    
    # Initialize workflow chain
    workflow_chain = BondWorkflowChain()
    
    # Process based on arguments
    if args.query:
        logger.info(f"Processing query: {args.query}")
        result = workflow_chain.run_bond_workflow(args.query)
        print_result(result)
        
    elif args.isin:
        logger.info(f"Getting details for bond: {args.isin}")
        # Use directory to route query
        query = f"Get information for bond with ISIN {args.isin}"
        result = workflow_chain.directory.route_query(query)
        print_result(result)
        
    elif args.compare and len(args.compare) > 0:
        logger.info(f"Comparing bonds: {args.compare}")
        # Use finder agent to compare bonds
        isins = ", ".join(args.compare)
        query = f"Compare bonds with ISINs {isins}"
        result = workflow_chain.process_query(query)
        print_result(result)
        
    elif args.calculate:
        logger.info("Using bond calculator")
        # Gather calculation parameters
        isin = input("Enter ISIN: ")
        
        calc_type = args.calc_type
        if not calc_type:
            calc_type = input("Calculation type (price/yield): ").lower()
            if calc_type not in ['price', 'yield']:
                print("Invalid calculation type. Must be 'price' or 'yield'")
                return
                
        units = int(input("Number of units: ") or "100")
        
        if calc_type == 'price':
            input_value = float(input("Yield rate (%): ") or "8.5")
        else:
            input_value = float(input("Price: ") or "1000000")
            
        # Mock bond data - in a real scenario, this would be fetched from the database
        bond_data = {
            "isin": isin,
            "issuer_name": "Example Bond Issuer",
            "face_value": "1000000",
            "coupon_rate": "8.25%",
            "maturity_date": "17-10-2028"
        }
        
        # Create calculation request
        request = {
            "isin": isin,
            "calculation_type": calc_type,
            "investment_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "units": units,
            "input_value": input_value,
            "bond_data": bond_data
        }
        
        result = workflow_chain.calculator.process_calculation_request(request)
        print_result(result)
        
    elif args.agent:
        # Process with specified agent
        query = input(f"Enter your query for the {args.agent} agent: ")
        logger.info(f"Processing with {args.agent} agent: {query}")
        
        if args.agent == 'directory':
            result = workflow_chain.directory.route_query(query)
        elif args.agent == 'finder':
            result = workflow_chain.finder.process_query(query)
        elif args.agent == 'cashflow':
            result = workflow_chain.cashflow.query(query)
        elif args.agent == 'screener':
            result = workflow_chain.screener.query(query)
        elif args.agent == 'calculator':
            result = workflow_chain.calculator.process_query(query)
        else:
            print(f"Unknown agent: {args.agent}")
            parser.print_help()
            return
            
        print_result(result)
        
    else:
        # If no arguments provided, print usage
        print("Please provide a query or other arguments")
        parser.print_help()

def print_result(result):
    """
    Print the result in a readable format
    
    Args:
        result: The result to print
    """
    if isinstance(result, dict):
        if "status" in result:
            print(f"Status: {result['status']}")
            print(f"Message: {result.get('message', '')}")
            
            # Print data if available
            if result.get("data"):
                print("\nData:")
                print_dict(result["data"], indent=2)
        else:
            # Just print the dictionary
            print_dict(result)
    else:
        # Print any other type of result
        print(result)

def print_dict(d, indent=0):
    """
    Print a dictionary in a readable format
    
    Args:
        d: The dictionary to print
        indent: The indentation level
    """
    if not isinstance(d, dict):
        print(" " * indent + str(d))
        return
        
    for key, value in d.items():
        if isinstance(value, dict):
            print(" " * indent + f"{key}:")
            print_dict(value, indent + 2)
        elif isinstance(value, list):
            print(" " * indent + f"{key}:")
            for item in value[:5]:  # Limit to first 5 items
                if isinstance(item, dict):
                    print_dict(item, indent + 2)
                else:
                    print(" " * (indent + 2) + str(item))
            if len(value) > 5:
                print(" " * (indent + 2) + f"... ({len(value) - 5} more items)")
        else:
            print(" " * indent + f"{key}: {value}")

if __name__ == "__main__":
    main() 