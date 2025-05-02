import os
import sys
import datetime
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow import BondWorkflowChain
from src.agents.bond_calculator_agent import BondCalculatorAgent

# App configuration
st.set_page_config(
    page_title="ChatBond.ai",
    page_icon="💰",
    layout="wide"
)

# Initialize the classes
if "workflow_chain" not in st.session_state:
    st.session_state.workflow_chain = BondWorkflowChain()
if "calculator" not in st.session_state:
    st.session_state.calculator = BondCalculatorAgent(
        current_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        current_user="guest"
    )
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome to ChatBond.ai! I can help you find information about bonds, compare yields, analyze cash flows, and screen potential investments."}
    ]

# Header
st.title("ChatBond.ai")
st.write(f"User: Guest | Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Create two simple tabs
tab1, tab2, tab3 = st.tabs(["Chat", "Bond Info", "Bond Calculator"])

# Tab 1: Chat Interface
with tab1:
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            st.write(f"🤖 **Assistant**: {message['content']}")
        else:
            st.write(f"👤 **You**: {message['content']}")
    
    # Sample queries for quick selection
    st.write("### Quick Questions:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("What information do you have on corporate bonds with AAA rating?"):
            st.session_state.user_query = "What information do you have on corporate bonds with AAA rating?"
        if st.button("When is the next payment date for US Treasury bonds?"):
            st.session_state.user_query = "When is the next payment date for US Treasury bonds?"
    with col2:
        if st.button("Show me the highest yielding bonds available right now."):
            st.session_state.user_query = "Show me the highest yielding bonds available right now."
        if st.button("Which companies have the strongest financial metrics in their bond offerings?"):
            st.session_state.user_query = "Which companies have the strongest financial metrics in their bond offerings?"
    
    # User input
    user_query = st.text_input("Ask about bonds:", key="user_query")
    
    # Process user query
    if user_query:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Process the query
        with st.spinner("Getting answer..."):
            try:
                # Direct call to the workflow chain
                response = st.session_state.workflow_chain.process_query(user_query)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_message = f"Error: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_message})
        
        # Clear the input and refresh the page
        st.experimental_rerun()

# Tab 2: Bond Info
with tab2:
    st.write("### Bond Information")
    st.write("Enter a bond ISIN to get detailed information:")
    
    # Simple ISIN input
    isin = st.text_input("Bond ISIN:", placeholder="Example: INE123456789")
    
    if st.button("Get Bond Info"):
        if not isin:
            st.error("Please enter an ISIN")
        else:
            with st.spinner("Fetching bond information..."):
                try:
                    # Direct call to the directory agent
                    directory_agent = st.session_state.workflow_chain.directory
                    result = directory_agent.route_query(f"Get information for bond ISIN {isin}")
                    st.success(f"Bond Information Retrieved")
                    st.json(result)
                except Exception as e:
                    st.error(f"Error retrieving bond information: {str(e)}")

# Tab 3: Bond Calculator
with tab3:
    st.write("### Bond Yield Calculator")
    st.write("Calculate bond price from yield rate or yield rate from price:")
    
    # Calculator form
    calc_type = st.radio("Calculation Type:", ["Price from Yield", "Yield from Price"])
    
    # ISIN input
    isin = st.text_input("Bond ISIN:", placeholder="Example: INE002A08534", key="calc_isin")
    
    # Investment details
    col1, col2 = st.columns(2)
    with col1:
        investment_date = st.date_input("Investment Date:", datetime.datetime.now())
        units = st.number_input("Number of Units:", min_value=1, value=100)
    
    with col2:
        if calc_type == "Price from Yield":
            input_value = st.number_input("Yield Rate (%):", min_value=0.1, max_value=30.0, value=8.5, step=0.1)
            input_label = "yield_rate"
            calc_type_code = "price"
        else:
            input_value = st.number_input("Price:", min_value=1.0, value=1000000.0, step=1000.0)
            input_label = "price"
            calc_type_code = "yield"
    
    # Bond details (simplified for demo)
    st.write("### Bond Details")
    issuer = st.text_input("Issuer Name:", "RELIANCE INDUSTRIES LIMITED")
    face_value = st.text_input("Face Value:", "1000000")
    coupon_rate = st.text_input("Coupon Rate (%):", "9.05%")
    maturity_date = st.text_input("Maturity Date (DD-MM-YYYY):", "17-10-2028")
    
    if st.button("Calculate"):
        if not isin:
            st.error("Please enter an ISIN")
        else:
            with st.spinner("Calculating..."):
                try:
                    # Create request object
                    request = {
                        "isin": isin,
                        "calculation_type": calc_type_code,
                        "investment_date": f"{investment_date} 00:00:00",
                        "units": units,
                        "input_value": input_value,
                        "bond_data": {
                            "isin": isin,
                            "issuer_name": issuer,
                            "face_value": face_value,
                            "coupon_rate": coupon_rate,
                            "maturity_date": maturity_date
                        }
                    }
                    
                    # Process calculation
                    result = st.session_state.calculator.process_calculation_request(request)
                    st.success("Calculation Complete")
                    st.markdown(f"**Result:**\n\n{result}")
                except Exception as e:
                    st.error(f"Calculation error: {str(e)}")

if __name__ == "__main__":
    # This will allow running the Streamlit app directly with 'python ui.py'
    import subprocess
    subprocess.run(["streamlit", "run", __file__]) 