from langchain.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from pydantic import BaseModel, Field
from typing import Dict, Any
import os
import re
from dotenv import load_dotenv

load_dotenv("key.env")

# Load Serper API key
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

class CompanyToTickerInput(BaseModel):
    company_name: str = Field(..., description="Company name to convert to ticker (e.g., 'Apple Inc.')")

@tool(args_schema=CompanyToTickerInput)
def company_to_ticker(company_name: str) -> Dict[str, Any]:
    """
    Converts a company name to its stock ticker symbol using Serper search.
    
    Args:
        company_name: The name of the company to look up
        
    Returns:
        Dictionary with ticker symbol and company information
    """
    try:
        # Initialize the Serper search wrapper
        search = GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY)
        
        # Search for the ticker symbol
        search_query = f"{company_name} stock ticker symbol NYSE NASDAQ"
        search_results = search.results(search_query)
        
        # Extract potential ticker symbols
        ticker_pattern = r'\b[A-Z]{1,5}\b'  # Basic pattern for ticker symbols (1-5 uppercase letters)
        
        # Process organic search results
        if "organic" in search_results:
            for result in search_results["organic"]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                content = f"{title} {snippet}"
                
                # Look for ticker patterns
                potential_tickers = re.findall(ticker_pattern, content)
                
                # Filter out common non-ticker uppercase words
                filtered_tickers = [t for t in potential_tickers if t not in 
                                   ["NYSE", "NASDAQ", "SEC", "CEO", "CFO", "US", "USA", "API"]]
                
                if filtered_tickers:
                    # Prioritize tickers that appear in patterns like "ABC:", "ABC)", "(ABC)"
                    for pattern in [r'\(([A-Z]{1,5})\)', r'([A-Z]{1,5}):', r'([A-Z]{1,5})\)']:
                        special_matches = re.findall(pattern, content)
                        if special_matches:
                            ticker = special_matches[0]
                            return {
                                "ticker": ticker,
                                "company_name": company_name,
                                "status": "success",
                                "source": "serper_search_pattern"
                            }
                    
                    # If no special pattern, use the first filtered ticker
                    ticker = filtered_tickers[0]
                    return {
                        "ticker": ticker,
                        "company_name": company_name,
                        "status": "success",
                        "source": "serper_search"
                    }
        
        # If no ticker found, try an alternative search
        alt_search_query = f"{company_name} stock symbol"
        alt_search_results = search.results(alt_search_query)
        
        if "organic" in alt_search_results:
            for result in alt_search_results["organic"]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                content = f"{title} {snippet}"
                
                # Look for ticker patterns
                potential_tickers = re.findall(ticker_pattern, content)
                filtered_tickers = [t for t in potential_tickers if t not in 
                                   ["NYSE", "NASDAQ", "SEC", "CEO", "CFO", "US", "USA", "API"]]
                
                if filtered_tickers:
                    ticker = filtered_tickers[0]
                    return {
                        "ticker": ticker,
                        "company_name": company_name,
                        "status": "success",
                        "source": "serper_alt_search"
                    }
        
        # If still no ticker found
        return {
            "ticker": None,
            "company_name": company_name,
            "status": "not_found",
            "message": f"Could not find ticker for {company_name}"
        }
    
    except Exception as e:
        return {
            "ticker": None,
            "company_name": company_name,
            "status": "error",
            "message": f"Error finding ticker: {str(e)}"
        }

# Example usage
if __name__ == "__main__":
    # Create a proper instance of the tool
    company_ticker_tool = company_to_ticker.bind()
    
    # Call the tool using the invoke method
    result = company_ticker_tool.invoke("Apple Inc.")
    print(result)