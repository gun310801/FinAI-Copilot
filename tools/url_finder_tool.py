from extract_tool import company_to_ticker
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import os
from sec_api import QueryApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv("key.env")

# Load SEC API key
SEC_API_KEY = os.getenv("SEC_API_KEY")

class FindFilingUrlInput(BaseModel):
    company_name: str = Field(..., description="Company name to search for")
    filing_type: str = Field("10-K", description="Type of filing to search for (default: 10-K)")
    year_start: int = Field(2020, description="Start year for search (default: 2020)")
    year_end: int = Field(2024, description="End year for search (default: 2024)")
    limit: int = Field(3, description="Maximum number of URLs to return (default: 3)")

@tool(args_schema=FindFilingUrlInput)
def find_filing_urls(
    company_name: str,
    filing_type: str = "10-K",
    year_start: int = 2020,
    year_end: int = 2024,
    limit: int = 3
) -> Dict[str, Any]:
    """
    Find SEC filing URLs for a given company.
    
    Args:
        company_name: The name of the company to search for
        filing_type: Type of filing to search for (default: 10-K)
        year_start: Start year for the search range (default: 2020)
        year_end: End year for the search range (default: 2024)
        limit: Maximum number of URLs to return (default: 3)
        
    Returns:
        Dictionary containing company information and filing URLs
    """
    # Step 1: Find the ticker symbol for the company using extract_tool
    # Create a proper instance of the tool first then invoke it
    company_ticker_tool = company_to_ticker.bind()
    ticker_result = company_ticker_tool.invoke(company_name)
    
    # Initialize API client for SEC
    query_api = QueryApi(SEC_API_KEY)
    
    # Step 2: Construct the query based on the ticker result
    if ticker_result["status"] == "success" and ticker_result["ticker"]:
        ticker = ticker_result["ticker"]
        query_string = f"ticker:{ticker} AND formType:\"{filing_type}\""
    else:
        # Fallback to company name search if ticker lookup fails
        query_string = f"companyName:\"{company_name}\" AND formType:\"{filing_type}\""
    
    # Complete query with date range
    query = {
        "query": f"{query_string} AND filedAt:{{{year_start}-01-01 TO {year_end}-12-31}}",
        "from": "0",
        "size": str(limit)
    }
    
    # Step 3: Execute SEC API search
    try:
        filings = query_api.get_filings(query)
        
        # Extract filing URLs and metadata
        urls = []
        if "filings" in filings and filings["filings"]:
            for filing in filings["filings"][:limit]:
                urls.append({
                    "url": filing.get("linkToFilingDetails"),
                    "company_name": filing.get("companyName"),
                    "ticker": filing.get("ticker"),
                    "filing_date": filing.get("filedAt"),
                    "form_type": filing.get("formType")
                })
        
        # Return the final result
        return {
            "company_name": company_name,
            "ticker": ticker_result.get("ticker"),
            "filing_type": filing_type,
            "year_range": f"{year_start}-{year_end}",
            "urls": urls,
            "count": len(urls),
            "status": "success" if urls else "no_urls_found"
        }
        
    except Exception as e:
        return {
            "company_name": company_name,
            "ticker": ticker_result.get("ticker"),
            "filing_type": filing_type,
            "year_range": f"{year_start}-{year_end}",
            "urls": [],
            "count": 0,
            "status": "error",
            "message": str(e)
        }

# Example usage
if __name__ == "__main__":
    # Create instance of the tool
    url_finder_tool = find_filing_urls.bind()
    
    # Example: Find 10-K filings for Apple
    result = url_finder_tool.invoke({
        "company_name": "Apple Inc.",
        "filing_type": "10-K",
        "year_start": 2015,
        "year_end": 2024,
        "limit": 11
    })
    print("Apple 10-K filings result:")
    print(result)