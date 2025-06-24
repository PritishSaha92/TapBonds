from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Uncomment if using caching
"""
from langchain.globals import set_llm_cache
import hashlib
from gptcache import Cache
from gptcache.manager.factory import manager_factory
from gptcache.processor.pre import get_prompt
from langchain_community.cache import GPTCache

def get_hashed_name(name):
    return hashlib.sha256(name.encode()).hexdigest()
    
def init_gptcache(cache_obj: Cache, llm: str):
    hashed_llm = get_hashed_name(llm)
    cache_obj.init(
        pre_embedding_func=get_prompt,
        data_manager=manager_factory(manager="map", data_dir=f"map_cache_{hashed_llm}"),
    )

set_llm_cache(GPTCache(init_gptcache))
"""

# Load environment variables
load_dotenv()

class BondQueryResponse(BaseModel):
    binary_score: int = Field(..., description="0 for Cash Flow & Maturity Agent, 1 for Bond Finder Agent, 2 for Bond Calculator Agent")

class BondDirectoryAgent:
    def __init__(self, model = "llama3-70b-8192"):
        """
        Initializes the BondQueryRouter with a language model and API key.
        """
        self.llm = ChatGroq(model=model)
        self.structured_llm_router = self.llm.with_structured_output(BondQueryResponse)
        
        self.system_prompt = """
        You are an evaluator determining whether a bond-related query should be routed to:
        - The **Cash Flow & Maturity Agent (0)** for queries related to cash flows, maturity schedules, and payment timelines.
        - The **Bond Finder Agent (1)** for queries about bond comparison, best yields, and investment options.
        - The **Bond Calculator Agent (2)** for queries requiring a precise calculation, such as bond price, yield (YTM), or accrued interest.

        **Evaluation Criteria:**
        - **Return `0`** if the query involves:
          - Bond cash flows, payment schedules, or maturity dates.
          - Next coupon or interest payment date.

        - **Return `1`** if the query involves:
          - Bond comparison or finding the best yield/return.
          - Investment recommendations or filtering bonds.
          - Finding bonds with certain characteristics (e.g., "high-yield corporate bonds").

        - **Return `2`** if the query involves:
          - Calculating the price of a specific bond for a given yield.
          - Calculating the Yield to Maturity (YTM) for a given price.
          - Asking "what is the price" or "what is the yield" for a specific ISIN.

        **Output Format:**
        - If the query is about **cash flows or maturity**, output: `0`
        - If the query is about **bond comparison and finding bonds**, output: `1`
        - If the query is about **price or yield calculation**, output: `2`

        **Examples:**
        🔹 **User Query:** "When is the next payment for bond ISIN XYZ?"
        👉 **Output:** `0`

        🔹 **User Query:** "List government bonds with the highest returns available today."
        👉 **Output:** `1`
        
        🔹 **User Query:** "Calculate the price of ISIN ABC if the yield is 5.5%."
        👉 **Output:** `2`

        🔹 **User Query:** "What is the YTM for bond XYZ if I buy it at 98.75?"
        👉 **Output:** `2`

        **Ensure that your response is only `0`, `1`, or `2`, with no additional explanation.**
        """

        self.query_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{query}"),
            ]
        )

        self.router = self.query_prompt | self.structured_llm_router

    def route_query(self, query):
        """
        Routes the bond-related query to either Bond Finder Agent (1) or Cash Flow & Maturity Agent (0).
        """
        response = self.router.invoke({"query": query})
        return response.binary_score

if __name__ == "__main__":
    router = BondDirectoryAgent()
    
    # Sample Queries
    queries = [
        "Show me details for ISIN INE123456789.", # Should be 0 or 1 depending on detail type, let's say 1
        "When is the next payment for bond with ISIN INE123456789?", # Should be 0
        "Find corporate bonds with at least 5% yield.", # Should be 1
        "What is the price of bond INE123456789 if I want a 6% yield?", # Should be 2
        "Calculate the yield on a bond I bought for 1020." # Should be 2
    ]

    for query in queries:
        routing_result = router.route_query(query)
        print(f"Query: '{query}' -> Routing Decision: {routing_result}") 