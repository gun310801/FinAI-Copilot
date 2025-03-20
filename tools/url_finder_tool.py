# # from tools.ticker import company_to_ticker
# # from langchain.tools import tool
# # from pydantic import BaseModel, Field
# # from typing import Dict, Any, List
# # import os
# # from sec_api import QueryApi
# # from dotenv import load_dotenv

# # # Load environment variables
# # load_dotenv("key.env")

# # # Load SEC API key
# # SEC_API_KEY = os.getenv("SEC_API_KEY")

# # class FindFilingUrlInput(BaseModel):
# #     company_name: str = Field(..., description="Company name to search for")
# #     filing_type: str = Field("10-K", description="Type of filing to search for (default: 10-K)")
# #     year_start: int = Field(2020, description="Start year for search (default: 2020)")
# #     year_end: int = Field(2024, description="End year for search (default: 2024)")
# #     limit: int = Field(3, description="Maximum number of URLs to return (default: 3)")

# # @tool(args_schema=FindFilingUrlInput)
# # def find_filing_urls(
# #     company_name: str,
# #     filing_type: str = "10-K",
# #     year_start: int = 2020,
# #     year_end: int = 2024,
# #     limit: int = 3
# # ) -> Dict[str, Any]:
# #     """
# #     Find SEC filing URLs for a given company.
    
# #     Args:
# #         company_name: The name of the company to search for
# #         filing_type: Type of filing to search for (default: 10-K)
# #         year_start: Start year for the search range (default: 2020)
# #         year_end: End year for the search range (default: 2024)
# #         limit: Maximum number of URLs to return (default: 3)
        
# #     Returns:
# #         Dictionary containing company information and filing URLs
# #     """
# #     # Step 1: Find the ticker symbol for the company using extract_tool
# #     # Create a proper instance of the tool first then invoke it
# #     company_ticker_tool = company_to_ticker.bind()
# #     ticker_result = company_ticker_tool.invoke(company_name)
    
# #     # Initialize API client for SEC
# #     query_api = QueryApi(SEC_API_KEY)
    
# #     # Step 2: Construct the query based on the ticker result
# #     if ticker_result["status"] == "success" and ticker_result["ticker"]:
# #         ticker = ticker_result["ticker"]
# #         query_string = f"ticker:{ticker} AND formType:\"{filing_type}\""
# #     else:
# #         # Fallback to company name search if ticker lookup fails
# #         query_string = f"companyName:\"{company_name}\" AND formType:\"{filing_type}\""
    
# #     # Complete query with date range
# #     query = {
# #         "query": f"{query_string} AND filedAt:{{{year_start}-01-01 TO {year_end}-12-31}}",
# #         "from": "0",
# #         "size": str(limit)
# #     }
    
# #     # Step 3: Execute SEC API search
# #     try:
# #         filings = query_api.get_filings(query)
        
# #         # Extract filing URLs and metadata
# #         urls = []
# #         if "filings" in filings and filings["filings"]:
# #             for filing in filings["filings"][:limit]:
# #                 urls.append({
# #                     "url": filing.get("linkToFilingDetails"),
# #                     "company_name": filing.get("companyName"),
# #                     "ticker": filing.get("ticker"),
# #                     "filing_date": filing.get("filedAt"),
# #                     "form_type": filing.get("formType")
# #                 })
        
# #         # Return the final result
# #         return {
# #             "company_name": company_name,
# #             "ticker": ticker_result.get("ticker"),
# #             "filing_type": filing_type,
# #             "year_range": f"{year_start}-{year_end}",
# #             "urls": urls,
# #             "count": len(urls),
# #             "status": "success" if urls else "no_urls_found"
# #         }
        
# #     except Exception as e:
# #         return {
# #             "company_name": company_name,
# #             "ticker": ticker_result.get("ticker"),
# #             "filing_type": filing_type,
# #             "year_range": f"{year_start}-{year_end}",
# #             "urls": [],
# #             "count": 0,
# #             "status": "error",
# #             "message": str(e)
# #         }

# # # Example usage
# # if __name__ == "__main__":
# #     # Create instance of the tool
# #     url_finder_tool = find_filing_urls.bind()
    
# #     # Example: Find 10-K filings for Apple
# #     result = url_finder_tool.invoke({
# #         "company_name": "Apple Inc.",
# #         "filing_type": "10-K",
# #         "year_start": 2015,
# #         "year_end": 2024,
# #         "limit": 11
# #     })
# #     print("Apple 10-K filings result:")
# #     print(result)
# import sys
# import os
# from langchain.tools import tool
# from pydantic import BaseModel, Field
# from typing import Dict, Any, List
# from sec_api import QueryApi
# from dotenv import load_dotenv
# import math

# # Add the parent directory to the path if needed
# # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # For the current directory structure, use a relative import
# from ticker import company_to_ticker

# # Load environment variables
# load_dotenv("key.env")

# # Load SEC API key
# SEC_API_KEY = os.getenv("SEC_API_KEY")

# class FindFilingUrlInput(BaseModel):
#     company_name: str = Field(..., description="Company name to search for")
#     filing_type: str = Field("10-K", description="Type of filing to search for (default: 10-K)")
#     year_start: int = Field(2020, description="Start year for search (default: 2020)")
#     year_end: int = Field(2024, description="End year for search (default: 2024)")
#     limit: int = Field(10, description="Maximum number of URLs to return (default: 10)")

# @tool(args_schema=FindFilingUrlInput)
# def find_filing_urls(
#     company_name: str,
#     filing_type: str = "10-K",
#     year_start: int = 2020,
#     year_end: int = 2024,
#     limit: int = 10
# ) -> Dict[str, Any]:
#     """
#     Find SEC filing URLs for a given company using optimized modulo-3 filtering.
#     Makes a single API call for the entire range and filters to get minimum documents.
#     Each 10-K filing contains data for the filing year and the previous two years.
    
#     Args:
#         company_name: The name of the company to search for
#         filing_type: Type of filing to search for (default: 10-K)
#         year_start: Start year for the search range (default: 2020)
#         year_end: End year for the search range (default: 2024)
#         limit: Maximum number of URLs to return (default: 10)
        
#     Returns:
#         Dictionary containing company information and filing URLs
#     """
#     # Step 1: Find the ticker symbol for the company
#     company_ticker_tool = company_to_ticker().bind()  # Assuming this is how your function is defined
#     ticker_result = company_ticker_tool.invoke(company_name)
    
#     # Initialize API client for SEC
#     query_api = QueryApi(SEC_API_KEY)
    
#     # Step 2: Construct the query based on the ticker result
#     if ticker_result["status"] == "success" and ticker_result["ticker"]:
#         ticker = ticker_result["ticker"]
#         query_string = f"ticker:{ticker} AND formType:\"{filing_type}\""
#     else:
#         # Fallback to company name search if ticker lookup fails
#         query_string = f"companyName:\"{company_name}\" AND formType:\"{filing_type}\""
    
#     # Step 3: Make a single API call for the entire date range
#     query = {
#         "query": f"{query_string} AND filedAt:{{{year_start}-01-01 TO {year_end}-12-31}}",
#         "from": "0",
#         "size": str(limit * 3)  # Request extra to ensure we have enough to filter
#     }
    
#     try:
#         # Execute SEC API search
#         filings = query_api.get_filings(query)
        
#         # Step 4: Process filings and apply modulo-3 filtering logic
#         all_filings = []
#         if "filings" in filings and filings["filings"]:
#             # Sort filings by date (newest first)
#             sorted_filings = sorted(filings["filings"], key=lambda x: x.get("filedAt", ""), reverse=True)
            
#             # Create a mapping of filing year to filing details for easier access
#             year_to_filing = {}
#             for filing in sorted_filings:
#                 filing_date = filing.get("filedAt", "")
#                 if filing_date:
#                     filing_year = int(filing_date.split("-")[0])
#                     # Only keep the first (most recent) filing for each year
#                     if filing_year not in year_to_filing and year_start <= filing_year <= year_end:
#                         year_to_filing[filing_year] = filing
            
#             # Apply the modulo-3 filtering logic to determine which years to include
#             target_years = []
#             years_diff = year_end - year_start
            
#             # UPDATED LOGIC: Each filing covers its own year and two previous years
#             # For example, a 2024 filing covers 2024, 2023, 2022
            
#             if years_diff % 3 == 0:
#                 # Range is perfectly divisible by 3
#                 current = year_end
#                 while current >= year_start:
#                     target_years.append(current)
#                     current -= 3
#             else:
#                 # Range not perfectly divisible by 3
#                 # Start from the upper end and work backward
#                 current = year_end
#                 while current > year_start:
#                     target_years.append(current)
#                     current -= 3
                
#                 # Add the start year if needed for complete coverage
#                 if current < year_start and target_years and (year_start not in target_years):
#                     target_years.append(year_start)
            
#             # Filter and format the filings based on target years
#             for year in target_years:
#                 if year in year_to_filing:
#                     filing = year_to_filing[year]
#                     filing_year = int(filing.get("filedAt", "").split("-")[0])
                    
#                     # UPDATED: Calculate years covered by this filing (current year and two previous)
#                     covered_years = [filing_year - i for i in range(0, 3) 
#                                     if year_start <= filing_year - i <= year_end]
                    
#                     all_filings.append({
#                         "url": filing.get("linkToFilingDetails"),
#                         "company_name": filing.get("companyName"),
#                         "ticker": filing.get("ticker"),
#                         "filing_date": filing.get("filedAt"),
#                         "form_type": filing.get("formType"),
#                         "year": filing_year,
#                         "years_covered": ", ".join(str(year) for year in covered_years)
#                     })
                    
#                     # Limit number of results
#                     if len(all_filings) >= limit:
#                         break
        
#         # Calculate years covered by our results
#         years_covered = set()
#         for filing_info in all_filings:
#             filing_year = int(filing_info.get("filing_date", "").split("-")[0])
#             # UPDATED: Each filing covers its own year and two previous years
#             for i in range(0, 3):
#                 covered_year = filing_year - i
#                 if year_start <= covered_year <= year_end:
#                     years_covered.add(covered_year)
        
#         # Return the final result
#         expected_years = set(range(year_start, year_end + 1))
#         missing_years = expected_years - years_covered
        
#         return {
#             "company_name": company_name,
#             "ticker": ticker_result.get("ticker"),
#             "filing_type": filing_type,
#             "year_range": f"{year_start}-{year_end}",
#             "urls": all_filings,
#             "count": len(all_filings),
#             "years_covered": sorted(list(years_covered)),
#             "missing_years": sorted(list(missing_years)) if missing_years else None,
#             "status": "success" if all_filings else "no_urls_found"
#         }
        
#     except Exception as e:
#         return {
#             "company_name": company_name,
#             "ticker": ticker_result.get("ticker"),
#             "filing_type": filing_type,
#             "year_range": f"{year_start}-{year_end}",
#             "urls": [],
#             "count": 0,
#             "status": "error",
#             "message": str(e)
#         }

# # Example usage
# if __name__ == "__main__":
#     # Create instance of the tool
#     url_finder_tool = find_filing_urls.bind()  # No need to bind as it's already a tool
    
#     # Example: Find 10-K filings for Apple
#     result = url_finder_tool.invoke({
#         "company_name": "Apple Inc.",
#         "filing_type": "10-K",
#         "year_start": 2015,
#         "year_end": 2024,
#         "limit": 5
#     })
#     print("Apple 10-K filings result:")
#     print(result)
from ticker import company_to_ticker
from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import os
from sec_api import QueryApi
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv("key.env")

# Load SEC API key
SEC_API_KEY = os.getenv("SEC_API_KEY")

class FindFilingUrlInput(BaseModel):
    company_name: str = Field(..., description="Company name to search for")
    filing_type: str = Field("10-K", description="Type of filing to search for (default: 10-K)")
    year_start: int = Field(2020, description="Start year for search (default: 2020)")
    year_end: int = Field(2024, description="End year for search (default: 2024)")
    limit: int = Field(10, description="Maximum number of URLs to return (default: 10)")

@tool(args_schema=FindFilingUrlInput)
def find_filing_urls(
    company_name: str,
    filing_type: str = "10-K",
    year_start: int = 2020,
    year_end: int = 2024,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Find SEC filing URLs for a given company using optimized modulo-3 filtering.
    Makes a single API call for the entire range and filters to get minimum documents.
    
    Args:
        company_name: The name of the company to search for
        filing_type: Type of filing to search for (default: 10-K)
        year_start: Start year for the search range (default: 2020)
        year_end: End year for the search range (default: 2024)
        limit: Maximum number of URLs to return (default: 10)
        
    Returns:
        Dictionary containing company information and filing URLs
    """
    # Step 1: Find the ticker symbol for the company
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
    
    # Step 3: Make a single API call for the entire date range
    query = {
        "query": f"{query_string} AND filedAt:{{{year_start}-01-01 TO {year_end}-12-31}}",
        "from": "0",
        "size": str(limit * 3)  # Request extra to ensure we have enough to filter
    }
    
    try:
        # Execute SEC API search
        filings = query_api.get_filings(query)
        
        # Step 4: Process filings and apply modulo-3 filtering logic
        all_filings = []
        if "filings" in filings and filings["filings"]:
            # Sort filings by date (newest first)
            sorted_filings = sorted(filings["filings"], key=lambda x: x.get("filedAt", ""), reverse=True)
            
            # Create a mapping of filing year to filing details for easier access
            year_to_filing = {}
            for filing in sorted_filings:
                filing_date = filing.get("filedAt", "")
                if filing_date:
                    filing_year = int(filing_date.split("-")[0])
                    # Only keep the first (most recent) filing for each year
                    if filing_year not in year_to_filing and year_start <= filing_year <= year_end:
                        year_to_filing[filing_year] = filing
            
            # Apply the modulo-3 filtering logic to determine which years to include
            target_years = []
            years_diff = year_end - year_start
            
            if years_diff % 3 == 0:
                # Range is perfectly divisible by 3
                current = year_end
                while current >= year_start + 3:
                    target_years.append(current)
                    current -= 3
            else:
                # Range not perfectly divisible by 3
                # Start from the upper end and work backward
                current = year_end
                while current > year_start:
                    target_years.append(current)
                    current -= 3
                
                # Add the start year if needed for complete coverage
                if current < year_start and target_years:
                    target_years.append(year_start)
            
            # Filter and format the filings based on target years
            for year in target_years:
                if year in year_to_filing:
                    filing = year_to_filing[year]
                    filing_year = int(filing.get("filedAt", "").split("-")[0])
                    
                    # Calculate years covered by this filing
                    covered_years = [filing_year - i for i in range(0, 3) 
                                    if year_start <= filing_year - i <= year_end]
                    
                    all_filings.append({
                        "url": filing.get("linkToFilingDetails"),
                        "company_name": filing.get("companyName"),
                        "ticker": filing.get("ticker"),
                        "filing_date": filing.get("filedAt"),
                        "form_type": filing.get("formType"),
                        "year": filing_year,
                        "years_covered": ", ".join(str(year) for year in covered_years)
                    })
                    
                    # Limit number of results
                    if len(all_filings) >= limit:
                        break
        
        # Calculate years covered by our results
        years_covered = set()
        for filing_info in all_filings:
            filing_year = int(filing_info.get("filing_date", "").split("-")[0])
            for i in range(0, 3):
                covered_year = filing_year - i
                if year_start <= covered_year <= year_end:
                    years_covered.add(covered_year)
        
        # Return the final result
        expected_years = set(range(year_start, year_end + 1))
        missing_years = expected_years - years_covered
        
        return {
            "company_name": company_name,
            "ticker": ticker_result.get("ticker"),
            "filing_type": filing_type,
            "year_range": f"{year_start}-{year_end}",
            "urls": all_filings,
            "count": len(all_filings),
            "years_covered": sorted(list(years_covered)),
            "missing_years": sorted(list(missing_years)) if missing_years else None,
            "status": "success" if all_filings else "no_urls_found"
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
        "year_start": 2008,
        "year_end": 2024,
        "limit": 10
    })
    print("Apple 10-K filings result:")
    print(result)