import json
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

class ExtractToolArgs(BaseModel):
    metric: str = Field(..., description="Metric name (e.g., 'sales_growth', 'gross_margin')")
    year_start: int = Field(..., description="Starting year (e.g., 2018)")
    year_end: int = Field(..., description="Ending year (e.g., 2020)")

def extract_tool_logic(metric: str, year_start: int, year_end: int) -> Dict[str, Any]:
    """
    Retrieves pre-calculated values for a given metric from the 'output.json' file.
    Searches for a dictionary in the file where the 'Metric' field matches the provided value.
    Then, for each year in the specified range, it collects the corresponding value.
    """
    try:
        # Open the data file that contains pre-calculated financial model data.
        with open("output.json", "r") as f:
            data = json.load(f)

        # Find the record that matches the given metric (case-insensitive).
        matching_record = None
        for record in data:
            if record.get("Metric", "").strip().lower() == metric.strip().lower():
                matching_record = record
                break

        if matching_record is None:
            return {"success": False, "data": None, "error": f"No data found for metric '{metric}'."}

        # Ensure the year_start is less than or equal to year_end.
        start, end = sorted([year_start, year_end])
        years = []
        values = []

        # Iterate over the requested range of years.
        for year in range(start, end + 1):
            year_str = str(year)
            if year_str in matching_record:
                years.append(year)
                values.append(matching_record[year_str])

        if not values:
            return {"success": False, "data": None, "error": f"No data available for years {start}-{end} for metric '{metric}'."}

        return {"success": True, "data": {"year_data": years, "values": values}, "error": None}

    except Exception as e:
        return {"success": False, "data": None, "error": f"Unexpected error: {str(e)}"}

# Create the LangChain structured tool from the function using the Pydantic args schema.
Extract_Tool = StructuredTool.from_function(
    func=extract_tool_logic,
    name="Extract_Tool",
    description = (
    "Extracts pre-calculated financial metric data from 'output.json' for a given year range. "
    "The tool searches for a record where the 'Metric' key matches the requested metric. "
    "Make sure you are querying for the right 'Metric' using the descriptions provided below"
    "It utilizes a KPI dictionary that includes the following metrics: "
    "'sales growth' (Year-over-year sales growth), "
    "'gross margin' (Gross margin percentage), "
    "'COGS_perc_sales' (Cost of Goods Sold as a percentage of sales), "
    "'rnd_perc_sales' (Research & Development expenses as a percentage of sales), "
    "'rnd_growth' (R&D growth rate), "
    "'sng_perc_sales' (Selling & General expenses as a percentage of sales), "
    "'income_margin' (Income margin percentage), "
    "'ebt' (Earnings Before Taxes), "
    "'tax_margin' (Tax margin percentage), "
    "'net_margin' (Net margin percentage), "
    "'margin_growth' (Overall margin growth rate), and "
    "'eps_growth' (Earnings Per Share growth rate)."
 ),
    args_schema=ExtractToolArgs
)