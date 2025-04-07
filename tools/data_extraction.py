from langchain.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
import re
from sec_api import ExtractorApi

# Import the URL finder tool
from url_finder_tool import find_filing_urls

# Load environment variables
load_dotenv("key.env")
SEC_API_KEY = os.getenv("SEC_API_KEY")

class SecSectionExtractionInput(BaseModel):
    filing_url: str = Field(..., description="URL to the SEC filing document")
    output_format: str = Field("text", description="Output format: 'text' or 'html'")

@tool(args_schema=SecSectionExtractionInput)
def extract_sec_section(
    filing_url: str,
    output_format: str = "text"
) -> Dict[str, Any]:
    """
    Extracts Item 8 (financial statements) section from an SEC filing.
    
    Args:
        filing_url: URL to the SEC filing document
        output_format: Output format - 'html'
        
    Returns:
        Dictionary containing the extracted section and metadata
    """
    # Initialize API client
    extractor_api = ExtractorApi(SEC_API_KEY)
    
    # Always use item 8 (financial statements)
    item = "8"
    
    try:
        # Extract company and filing info from URL
        company_match = re.search(r'data/([^/]+)', filing_url)
        company_cik = company_match.group(1) if company_match else "Unknown"
        
        doc_match = re.search(r'/([^/]+)\.htm', filing_url)
        doc_name = doc_match.group(1) if doc_match else "Unknown"
        
        # Extract the specified section
        section_content = extractor_api.get_section(filing_url, item, output_format)
        
        # Process tables if format is HTML
        tables = []
        if output_format == "html":
            tables = re.findall(r'<table[\s\S]*?<\/table>', section_content)
        
        return {
            "filing_url": filing_url,
            "item": item,
            "company_cik": company_cik,
            "document": doc_name,
            "content": section_content,
            "table_count": len(tables),
            "tables": tables[:5] if tables else [],  # Include first 5 tables as sample
            "status": "success"
        }
    except Exception as e:
        return {
            "filing_url": filing_url,
            "content": None,
            "status": "error",
            "message": str(e)
        }

# Example usage with automatic URL fetching
if __name__ == "__main__":
    # Get URLs first
    company_name = "Apple Inc."
    url_finder_tool = find_filing_urls.bind()
    url_results = url_finder_tool.invoke({
        "company_name": company_name,
        "filing_type": "10-K",
        "year_start": 2020,
        "year_end": 2023,
        "limit": 3
    })
    
    # Extract section from each URL
    if url_results["status"] == "success" and url_results["urls"]:
        print(f"Found {len(url_results['urls'])} URLs for {company_name}. Processing...")
        
        for i, filing_info in enumerate(url_results["urls"]):
            url = filing_info["url"]
            year = filing_info["year"]
            print(f"\nProcessing {i+1}/{len(url_results['urls'])}: {year} filing")
            
            result = extract_sec_section(
                filing_url=url,
                output_format="text"
            )
            
            if result["status"] == "success":
                content_length = len(result.get("content", ""))
                print(f"Successfully extracted Item 8 ({content_length} characters)")
                print(f"Table count: {result.get('table_count', 0)}")
                # Uncomment to save to file
                # with open(f"{company_name.replace(' ', '_')}_{year}_item8.txt", "w") as f:
                #     f.write(result.get("content", ""))
            else:
                print(f"Failed: {result.get('message', 'Unknown error')}")
    else:
        print(f"No URLs found for {company_name}")