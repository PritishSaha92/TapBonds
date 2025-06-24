import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import json

# Load environment variables
load_dotenv()

class WebAgent:
    def __init__(self):
        """Initialize the web search agent with Google Custom Search API credentials."""
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.search_engine_id = os.getenv("SEARCH_ENGINE_ID")
        
        if not self.search_api_key or not self.search_engine_id:
            raise ValueError("SEARCH_API_KEY and SEARCH_ENGINE_ID environment variables must be set.")
            
        self.service = build("customsearch", "v1", developerKey=self.search_api_key)
    
    def get_info(self, query: str, num_results: int = 3) -> str:
        """
        Perform a web search using Google Custom Search API.
        
        Args:
            query (str): The search query.
            num_results (int): The number of search results to return.
            
        Returns:
            str: A formatted string of search results with snippets and links.
        """
        try:
            print(f"Performing web search for: {query}")
            
            result = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=num_results
            ).execute()
            
            items = result.get('items', [])
            
            if not items:
                return f"No web search results found for '{query}'."

            # Format the results
            formatted_results = []
            for i, item in enumerate(items):
                title = item.get('title', 'No Title')
                snippet = item.get('snippet', 'No Snippet')
                link = item.get('link', '#')
                formatted_results.append(f"{i+1}. {title}\n   - Snippet: {snippet}\n   - Source: {link}")
            
            return "\n\n".join(formatted_results)

        except Exception as e:
            print(f"Error in web search: {str(e)}")
            return f"Unable to retrieve web information due to an error: {e}"

if __name__ == "__main__":
    agent = WebAgent()
    result = agent.get_info("current corporate bond market trends")
    print(result) 