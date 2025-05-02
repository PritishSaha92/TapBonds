import os
import re
import json
import math
import logging
import datetime
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BondCalculationRequest:
    isin: str
    calculation_type: str  # 'price' or 'yield'
    investment_date: datetime.datetime
    units: int
    input_value: float  # yield_rate for price calculation, price for yield calculation
    bond_data: Dict[str, Any]  # Bond details from the finder

@dataclass
class BondCalculationResponse:
    success: bool
    message: str
    calculation_type: str
    results: Dict[str, Union[float, str, int]]
    bond_details: Dict[str, Any]

class BondCalculatorAgent:
    """
    Agent for calculating bond prices and yields using LLM for validation and processing.
    Integrates with LangChain and Groq for natural language processing.
    """
    
    def __init__(self, 
                 llm_model_name: str = "llama3-70b-8192",
                 api_key: Optional[str] = None,
                 current_date: str = None,
                 current_user: str = "guest"):
        """
        Initialize the Bond Calculator Agent.
        
        Args:
            llm_model_name: Name of the LLM model to use
            api_key: Groq API key (will use environment variable if None)
            current_date: Current date and time in UTC
            current_user: Current user's login
        """
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set and no API key provided.")
        
        # Initialize the LLM client
        self.llm = ChatGroq(model=llm_model_name)
        
        # Store current date and user
        if current_date:
            self.current_date = datetime.datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S")
        else:
            self.current_date = datetime.datetime.now()
            
        self.current_user = current_user
        
        # Constants for calculations
        self.days_in_year = 365
        self.payment_frequency = 2  # Semi-annual payments
        
        # Initialize response cache
        self.response_cache = {}
        
        logger.info(f"BondCalculatorAgent initialized with model: {llm_model_name}")

    def get_last_coupon_date(self, current_date: datetime.datetime, maturity_date: datetime.datetime) -> datetime.datetime:
        """Calculate the last coupon date before the current date"""
        days_per_period = 365 // self.payment_frequency
        days_to_maturity = (maturity_date - current_date).days
        periods_to_maturity = math.ceil(days_to_maturity / days_per_period)
        last_coupon = maturity_date - datetime.timedelta(days=periods_to_maturity * days_per_period)
        return last_coupon

    def validate_calculation_request(self, request: Dict[str, Any]) -> Tuple[bool, str, Optional[BondCalculationRequest]]:
        """
        Validate the calculation request using basic validation and LLM.
        
        Args:
            request: Dictionary containing the calculation request parameters
            
        Returns:
            Tuple[bool, str, Optional[BondCalculationRequest]]: Validation result, error message, and processed request
        """
        try:
            # Validate ISIN format
            if not re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', request['isin']):
                return False, "Invalid ISIN format", None

            # Basic field validation
            required_fields = ['isin', 'calculation_type', 'investment_date', 'units', 'input_value', 'bond_data']
            for field in required_fields:
                if field not in request:
                    return False, f"Missing required field: {field}", None

            if request['calculation_type'] not in ['price', 'yield']:
                return False, "Invalid calculation_type. Must be 'price' or 'yield'", None

            try:
                units = int(request['units'])
                if units <= 0:
                    return False, "Units must be positive", None
            except (ValueError, TypeError):
                return False, "Invalid units value", None

            try:
                input_value = float(request['input_value'])
                if input_value <= 0:
                    return False, "Input value must be positive", None
                
                # Validate reasonable ranges
                if request['calculation_type'] == 'yield':
                    if input_value > 10000000:  # Max price validation
                        return False, "Price out of reasonable range", None
                else:  # price calculation
                    if input_value > 100:  # Max yield rate validation
                        return False, "Yield rate out of reasonable range", None
            except (ValueError, TypeError):
                return False, "Invalid input value", None

            # Validate dates
            try:
                investment_date = datetime.datetime.strptime(request['investment_date'], "%Y-%m-%d %H:%M:%S")
                maturity_date = datetime.datetime.strptime(request['bond_data']['maturity_date'], '%d-%m-%Y')
                
                if maturity_date <= investment_date:
                    return False, "Maturity date must be after investment date", None
            except ValueError as e:
                return False, f"Invalid date format: {str(e)}", None

            # Validate bond data
            required_bond_fields = ['isin', 'issuer_name', 'face_value', 'coupon_rate', 'maturity_date']
            for field in required_bond_fields:
                if field not in request['bond_data']:
                    return False, f"Missing required bond data field: {field}", None

            # Create BondCalculationRequest object
            calc_request = BondCalculationRequest(
                isin=request['isin'],
                calculation_type=request['calculation_type'],
                investment_date=investment_date,
                units=units,
                input_value=input_value,
                bond_data=request['bond_data']
            )

            return True, "", calc_request

        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            return False, f"Validation error: {str(e)}", None

    def calculate_price(self, request: BondCalculationRequest) -> BondCalculationResponse:
        """Calculate bond price given yield rate"""
        try:
            # Extract and sanitize bond details
            face_value = float(str(request.bond_data['face_value']).replace('₹', '').replace(',', ''))
            coupon_rate = float(request.bond_data['coupon_rate'].replace('%', '')) / 100
            maturity_date = datetime.datetime.strptime(request.bond_data['maturity_date'], '%d-%m-%Y')
            
            # Calculate cash flows
            annual_coupon = face_value * coupon_rate
            semi_annual_coupon = annual_coupon / self.payment_frequency
            
            # Generate future cash flows
            cashflows = []
            current_date = request.investment_date
            while current_date <= maturity_date:
                if current_date > request.investment_date:
                    if current_date == maturity_date:
                        cashflows.append((current_date, semi_annual_coupon + face_value))
                    else:
                        cashflows.append((current_date, semi_annual_coupon))
                current_date += datetime.timedelta(days=365//self.payment_frequency)

            # Calculate present value
            dirty_price = 0
            yield_rate = request.input_value / 100
            
            for payment_date, amount in cashflows:
                time_to_payment = (payment_date - request.investment_date).days / self.days_in_year
                discount_factor = 1 / ((1 + yield_rate) ** time_to_payment)
                dirty_price += amount * discount_factor

            # Calculate accrued interest
            last_coupon_date = self.get_last_coupon_date(request.investment_date, maturity_date)
            days_since_last_coupon = (request.investment_date - last_coupon_date).days
            accrued_interest = (annual_coupon * days_since_last_coupon) / self.days_in_year
            
            clean_price = dirty_price - accrued_interest
            
            results = {
                "clean_price_per_unit": clean_price,
                "clean_price_total": clean_price * request.units,
                "dirty_price_per_unit": dirty_price,
                "dirty_price_total": dirty_price * request.units,
                "accrued_interest": accrued_interest,
                "yield_rate": request.input_value,
                "units": request.units,
                "investment_date": request.investment_date.strftime('%Y-%m-%d %H:%M:%S'),
                "calculation_date": self.current_date.strftime('%Y-%m-%d %H:%M:%S')
            }

            return BondCalculationResponse(
                success=True,
                message="Price calculation successful",
                calculation_type="price",
                results=results,
                bond_details=request.bond_data
            )

        except Exception as e:
            logger.error(f"Error in price calculation: {str(e)}")
            return BondCalculationResponse(
                success=False,
                message=f"Error calculating price: {str(e)}",
                calculation_type="price",
                results={},
                bond_details=request.bond_data
            )

    def calculate_yield(self, request: BondCalculationRequest) -> BondCalculationResponse:
        """Calculate yield to maturity given price using binary search method"""
        try:
            # Extract and sanitize bond details
            face_value = float(str(request.bond_data['face_value']).replace('₹', '').replace(',', ''))
            coupon_rate = float(request.bond_data['coupon_rate'].replace('%', '')) / 100
            maturity_date = datetime.datetime.strptime(request.bond_data['maturity_date'], '%d-%m-%Y')
            
            # Calculate time to maturity in years
            time_to_maturity = (maturity_date - request.investment_date).days / self.days_in_year
            
            if time_to_maturity <= 0:
                raise ValueError("Bond has matured")
                
            # Calculate annual coupon payment
            annual_coupon = face_value * coupon_rate
            semi_annual_coupon = annual_coupon / self.payment_frequency
            
            # Binary search method to find yield
            def calculate_price_at_yield(ytm):
                # Generate future cash flows
                cashflows = []
                current_date = request.investment_date
                while current_date <= maturity_date:
                    if current_date > request.investment_date:
                        if current_date == maturity_date:
                            cashflows.append((current_date, semi_annual_coupon + face_value))
                        else:
                            cashflows.append((current_date, semi_annual_coupon))
                    current_date += datetime.timedelta(days=365//self.payment_frequency)

                # Calculate present value at given yield
                price = 0
                for payment_date, amount in cashflows:
                    time_to_payment = (payment_date - request.investment_date).days / self.days_in_year
                    discount_factor = 1 / ((1 + ytm) ** time_to_payment)
                    price += amount * discount_factor
                
                return price
            
            # Binary search for yield
            target_price = request.input_value
            lower_yield = 0.0001  # 0.01%
            upper_yield = 1.0     # 100%
            tolerance = 0.0001
            
            while upper_yield - lower_yield > tolerance:
                mid_yield = (lower_yield + upper_yield) / 2
                price_at_mid = calculate_price_at_yield(mid_yield)
                
                if abs(price_at_mid - target_price) < tolerance:
                    break
                
                if price_at_mid > target_price:
                    lower_yield = mid_yield
                else:
                    upper_yield = mid_yield
            
            ytm = (lower_yield + upper_yield) / 2
            ytm_percent = ytm * 100
            
            results = {
                "yield_to_maturity": ytm_percent,
                "price_per_unit": target_price,
                "price_total": target_price * request.units,
                "units": request.units,
                "investment_date": request.investment_date.strftime('%Y-%m-%d %H:%M:%S'),
                "calculation_date": self.current_date.strftime('%Y-%m-%d %H:%M:%S')
            }

            return BondCalculationResponse(
                success=True,
                message="Yield calculation successful",
                calculation_type="yield",
                results=results,
                bond_details=request.bond_data
            )

        except Exception as e:
            logger.error(f"Error in yield calculation: {str(e)}")
            return BondCalculationResponse(
                success=False,
                message=f"Error calculating yield: {str(e)}",
                calculation_type="yield",
                results={},
                bond_details=request.bond_data
            )

    @lru_cache(maxsize=100)
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from LLM with caching"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            return f"Error: {str(e)}"

    def format_response(self, response: BondCalculationResponse) -> str:
        """Format the calculation response using LLM"""
        if not response.success:
            return response.message
        
        try:
            prompt = f"""
            Please format the following bond calculation results in a clear, professional manner:
            
            Calculation Type: {response.calculation_type}
            Bond ISIN: {response.bond_details['isin']}
            Issuer: {response.bond_details['issuer_name']}
            Face Value: {response.bond_details['face_value']}
            Coupon Rate: {response.bond_details['coupon_rate']}
            Maturity Date: {response.bond_details['maturity_date']}
            
            Results:
            {json.dumps(response.results, indent=2)}
            
            The output should be formatted for readability with important figures highlighted.
            """
            
            llm_response = self._get_llm_response(prompt)
            return llm_response
        except Exception as e:
            logger.error(f"Error formatting response with LLM: {str(e)}")
            return self._basic_format_response(response)

    def _basic_format_response(self, response: BondCalculationResponse) -> str:
        """Basic formatting for when LLM formatting fails"""
        if not response.success:
            return response.message
            
        output = f"--- Bond Calculation Results ({response.calculation_type.upper()}) ---\n\n"
        output += f"Bond: {response.bond_details['isin']} - {response.bond_details['issuer_name']}\n"
        output += f"Face Value: {response.bond_details['face_value']}\n"
        output += f"Coupon Rate: {response.bond_details['coupon_rate']}\n"
        output += f"Maturity Date: {response.bond_details['maturity_date']}\n\n"
        
        output += "Results:\n"
        for key, value in response.results.items():
            if isinstance(value, float):
                output += f"  {key.replace('_', ' ').title()}: {value:.4f}\n"
            else:
                output += f"  {key.replace('_', ' ').title()}: {value}\n"
                
        output += f"\nCalculation performed on {response.results['calculation_date']}"
        
        return output

    def process_query(self, query: str) -> str:
        """Process a natural language query or ISIN and return bond calculations"""
        # Check if the query is a direct ISIN
        if re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', query.strip()):
            isin = query.strip()
            # Here we'd normally use the bond_finder_agent to get bond data
            # For simplicity, we'll use a mock bond
            bond_data = {
                "isin": isin,
                "issuer_name": "Example Bond Issuer",
                "face_value": "1000000",
                "coupon_rate": "8.25%",
                "maturity_date": "17-10-2028"
            }
            
            # Create a price calculation request with default values
            request = {
                "isin": isin,
                "calculation_type": "price",
                "investment_date": self.current_date.strftime("%Y-%m-%d %H:%M:%S"),
                "units": 1,
                "input_value": 8.5,  # 8.5% yield
                "bond_data": bond_data
            }
            
            return self.process_calculation_request(request)
        else:
            # For more complex queries, we could use LLM to extract parameters
            # For now, return a simple message
            return f"To calculate bond metrics, please provide the ISIN directly or use the bond calculator form."

    def process_calculation_request(self, request: Dict[str, Any]) -> str:
        """Process a structured calculation request"""
        # Validate request
        is_valid, error_message, calc_request = self.validate_calculation_request(request)
        
        if not is_valid:
            return f"Error: {error_message}"
        
        # Perform calculation
        if calc_request.calculation_type == 'price':
            response = self.calculate_price(calc_request)
        else:
            response = self.calculate_yield(calc_request)
        
        # Format and return response
        return self.format_response(response)

if __name__ == "__main__":
    # Example usage
    calculator = BondCalculatorAgent(
        current_date="2025-03-09 21:58:59",
        current_user="guest"
    )
    
    # Example bond data
    bond_data = {
        "isin": "INE002A08534",
        "issuer_name": "RELIANCE INDUSTRIES LIMITED",
        "face_value": "1000000",
        "coupon_rate": "9.05%",
        "maturity_date": "17-10-2028"
    }
    
    # Example price calculation request
    price_request = {
        "isin": "INE002A08534",
        "calculation_type": "price",
        "investment_date": "2025-03-09 21:58:59",
        "units": 100,
        "input_value": 8.5,  # 8.5% yield
        "bond_data": bond_data
    }
    
    result = calculator.process_calculation_request(price_request)
    print(result) 