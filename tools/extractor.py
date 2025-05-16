
import json
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

class ExtractToolArgs(BaseModel):
    metric: str = Field(
        ...,
        description="Metric name (e.g., 'sales_growth', 'gross_margin', 'net_sales_total')"
    )
    year_start: int = Field(
        ...,
        description="Starting year (e.g., 2018)"
    )
    year_end: int = Field(
        ...,
        description="Ending year (e.g., 2020)"
    )
    section: str = Field(
        ...,
        description="Section to extract data from. Set to 'kpis' for KPI values or 'processed_data' for raw processed data."
    )

def extract_tool_logic(metric: str, year_start: int, year_end: int, section: str) -> str:
    """
    Retrieves values for a given metric from 'output.json' based on a specified section.
    
    The agent must provide the section:
      - 'kpis': Search within the KPIs data.
      - 'processed_data': Search within the raw processed data.
    
    The function then filters the results by the specified year range (user provides only the year).
    Returns a JSON string instead of a dictionary to ensure compatibility with LangChain memory.
    """
    try:
        with open("output.json", "r") as f:
            data = json.load(f)
            
        metric_lower = metric.strip().lower()
        start, end = sorted([year_start, year_end])
        section = section.strip().lower()
        
        # Validate section input.
        if section not in ["kpis", "processed_data"]:
            result = {
                "success": False,
                "data": None,
                "error": f"Invalid section '{section}'. Choose 'kpis' or 'processed_data'."
            }
            return json.dumps(result, indent=2)
        
        results = None
        
        if section == "kpis":
            if "kpis" not in data or not isinstance(data["kpis"], dict):
                result = {
                    "success": False,
                    "data": None,
                    "error": "No KPIs data found in the file."
                }
                return json.dumps(result, indent=2)
            
            matching_record = None
            # Look for an exact match (case-insensitive) among KPI keys.
            for key, record in data["kpis"].items():
                if key.strip().lower() == metric_lower:
                    matching_record = record
                    break
            
            if matching_record is None:
                result = {
                    "success": False,
                    "data": None,
                    "error": f"No KPI data found for metric '{metric}'."
                }
                return json.dumps(result, indent=2)
            
            years = []
            values = []
            # matching_record is expected to be a dictionary with year strings as keys.
            for yr_str, val in matching_record.items():
                try:
                    yr = int(yr_str)
                except ValueError:
                    continue
                if start <= yr <= end:
                    years.append(yr)
                    values.append(val)
                    
            if not years:
                result = {
                    "success": False,
                    "data": None,
                    "error": f"No KPI data available for years {start}-{end} for metric '{metric}'."
                }
                return json.dumps(result, indent=2)
            
            results = {"year_data": years, "values": values}
        
        elif section == "processed_data":
            if "processed_data" not in data or not isinstance(data["processed_data"], dict):
                result = {
                    "success": False,
                    "data": None,
                    "error": "No processed_data found in the file."
                }
                return json.dumps(result, indent=2)
            
            years = []
            values = []
            # The keys in processed_data are dates, assumed to be in 'YYYY-MM-DD' format.
            for date_str, record in data["processed_data"].items():
                yr_str = date_str[:4]
                try:
                    yr = int(yr_str)
                except ValueError:
                    continue
                if start <= yr <= end:
                    # Check if the requested metric exists in the record.
                    if metric in record:
                        years.append(yr)
                        values.append(record[metric])
            
            if not years:
                result = {
                    "success": False,
                    "data": None,
                    "error": f"No processed data available for metric '{metric}' in years {start}-{end}."
                }
                return json.dumps(result, indent=2)
            
            results = {"year_data": years, "values": values}
        
        final_result = {"success": True, "data": results, "error": None}
        return json.dumps(final_result, indent=2)
    
    except Exception as e:
        error_result = {"success": False, "data": None, "error": f"Unexpected error: {str(e)}"}
        return json.dumps(error_result, indent=2)

# Create the LangChain structured tool from the function using the Pydantic args schema.
Extract_Tool = StructuredTool.from_function(
    func=extract_tool_logic,
    name="Extract_Tool",
    description=(
        "Extracts financial metric data from 'output.json' for a given year range. "
        "The agent must specify the 'section' from which to extract the data: "
        "'kpis' for pre-calculated KPI data or 'processed_data' for raw data. "
        "This tool then filters the results based on the provided metric and year range."
    ),
    args_schema=ExtractToolArgs
)