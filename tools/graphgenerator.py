import json
import traceback
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
import io
import os
from dotenv import load_dotenv
import openai

# Load API key from the environment file
load_dotenv("key.env")
key_string = os.getenv('OPEN_AI_API_KEY')
openai.api_key = key_string
#############################################
# Generate Graph Tool
#############################################
class GenerateGraphToolArgs(BaseModel):
    data: list = Field(
        ...,
        description="List of numerical values or metrics to plot."
    )
    labels: list = Field(
        ...,
        description="List of labels (e.g., years, categories) corresponding to the data."
    )
    graph_type: str = Field(
        ...,
        description="Type of graph, such as 'bar chart', 'line graph', or 'scatter plot'."
    )
    title: str = Field(
        ...,
        description="Title of the graph."
    )

def generate_graph_logic(data: list, labels: list, graph_type: str, title: str) -> str:
    """
    Generates Python code to create a graph using matplotlib based on user input.
    The function calls the OpenAI API to generate the code, then returns a JSON string
    containing the generated code.
    """
    prompt = (
        f"Generate Python code to create an interactive '{graph_type}' using plotly. "
        f"The graph should have the title '{title}', the X-axis labels as {labels}, "
        f"and the Y-axis values as {data}. Return only the code. "
        f"Always replace plt.show() with plt.savefig(buffer, format='png')"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            
            messages=[
                {"role": "system", "content": "You are an assistant that generates Python graph code using matplotlib."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
            
        )
        code = response.choices[0].message.content.strip()
        # Remove any markdown code block delimiters if present
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.splitlines()[1:-1])
        result = {"success": True, "data": {"code": code}, "error": None}
    except Exception as e:
        result = {"success": False, "data": None, "error": f"Error generating graph code: {str(e)}"}
    return json.dumps(result, indent=2)

# Convert the generate_graph_logic function to a StructuredTool.
GenerateGraph_Tool = StructuredTool.from_function(
    func=generate_graph_logic,
    name="GenerateGraph_Tool",
    description=(
        "Generates Python code for a graph using matplotlib. "
        "Accepts a list of data values, labels, graph type, and title, then returns code that creates the graph. "
        "The output code replaces plt.show() with plt.savefig(buffer, format='png')."
    ),
    args_schema=GenerateGraphToolArgs
)

#############################################
# Execute Graph Tool
#############################################
class ExecuteGraphToolArgs(BaseModel):
    code: str = Field(
        ...,
        description="The Python code to execute and display the graph."
    )
    filename: str = Field(
        ...,
        description="A relevant name for the visualization file (without extension)."
    )

def execute_graph_logic(code: str, filename: str) -> str:
    """
    Executes the provided Python code to display the graph.
    The code is executed in a controlled namespace. Any markdown code block delimiters are stripped.
    On success, the function saves the graph to a temporary file and returns a JSON string containing the file path under the key 'link'.
    """
    try:
        # Remove any Python code block delimiters if present
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.splitlines()[1:-1])
        code = code.replace("plt.show()", "")
            
        namespace = {"plt": plt, "io": io}
        exec(code, namespace)
        
        # Save plot to a temporary file
        file_path = f"/tmp/{filename}.png"
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.savefig(file_path)
        plt.close()
        result = {"success": True, "data": {"link": file_path}, "error": None}
    except Exception as e:
        result = {"success": False, "data": None, "error": "An error occurred while executing the graph code.\n" + traceback.format_exc()}
    return json.dumps(result, indent=2)

# Convert the execute_graph_logic function to a StructuredTool.
ExecuteGraph_Tool = StructuredTool.from_function(
    func=execute_graph_logic,
    name="ExecuteGraph_Tool",
    description=(
        "Executes Python code to produce a graph visualization using plotly. "
        "The tool saves the generated graph to a temporary file and returns its file path."
    ),
    args_schema=ExecuteGraphToolArgs
)