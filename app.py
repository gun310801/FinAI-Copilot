import sys
print("🔍 Running Python from:", sys.executable)
import streamlit as st
import os, json
import openai
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain import hub
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from chain_scoo import get_data_from_docs
from financial_model import financial_model
from tools.extractor import Extract_Tool
from tools.graphgenerator import GenerateGraph_Tool
from tools.graphgenerator import ExecuteGraph_Tool
from tools.reportwriter import ReportWriter_Tool
import pandas as pd

# Import for adding system messages
from langchain_core.messages import SystemMessage

def load_api_key(env_file="key.env"):
    load_dotenv(env_file)
    return os.getenv('OPEN_AI_API_KEY')

st.title("FinAI Co-Pilot")

def initialize_tools():
    tools = [Extract_Tool,GenerateGraph_Tool,ExecuteGraph_Tool,ReportWriter_Tool]
        
    return tools

def flatten_json(json_obj, parent_key='', sep='_'):
    """Flattens a nested JSON object into a single dictionary."""
    items = []
    for k, v in json_obj.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def save_data_to_json(data, filename="financial_data.json"):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    return filename

def load_and_process_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    text_data = json.dumps(data, indent=2)
    return text_data

def open_modal():
    st.session_state['show_modal'] = True

def main():
    api_key = load_api_key()
    # --- Session State Initialization ---
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "data" not in st.session_state:
        st.session_state.data = None
    if 'show_modal' not in st.session_state:
        st.session_state['show_modal'] = False

    st.sidebar.title("10-K Reports")
    pdf_files = st.sidebar.file_uploader(
        "Upload your 10-K PDF files", type=['pdf'], accept_multiple_files=True)
    
    if pdf_files:
        data = get_data_from_docs(pdf_files)
        processed_data = {}
        for item in data:
            report_date = item['report_date']
            item.pop("metadata")
            item.pop("section")
            flattened_item = flatten_json(item)
            if 'report_date' in flattened_item:
                del flattened_item['report_date']
            processed_data[report_date] = flattened_item
        initial_output = {"processed_data": processed_data}
        with open("output.json", "w") as f:
            json.dump(initial_output, f, indent=4)
            
        kpis = financial_model(data)
        table_data = []
        for key, value_dict in kpis.items():
            row = {"Metric": key}
            row.update(value_dict)
            table_data.append(row)

        df_kpis = pd.DataFrame(table_data).set_index("Metric")
        df = pd.DataFrame.from_dict(processed_data, orient='index').T
        kpi_json = json.loads(df_kpis.to_json(orient='index'))
        with open("output.json", "r") as f:
            existing_data = json.load(f)

        existing_data["kpis"] = kpi_json
        with open("output.json", "w") as f:
            json.dump(existing_data, f, indent=4)

    st.write("Ask questions about the 10-K reports")
    st.button("Open Details", on_click=open_modal)
    if st.session_state['show_modal']:
        st.write("Extracted Financial Data")
        st.dataframe(df)
        st.write("Extracted Financial KPIs")
        st.dataframe(df_kpis)

    # --- Display Chat History ---
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # --- Agent Initialization ---
    if "agent_executor" not in st.session_state:
        tools = initialize_tools()
        prompt = hub.pull("hwchase17/structured-chat-agent")
        llm_agent = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)
        # Create memory and add an initial system message
        agent_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        initial_message = (
            """
You are an AI assistant that answers questions about 10-K reports with precision and minimal commentary.

Your job is to retrieve and summarize financial information **only using the available tools**. Always respond with clean, concise outputs — do not return full Python dictionaries, JSON, or any unnecessary explanation.

---

📊 **When the user asks for a financial metric**, use the `Extract_Tool`:

Determine the correct section based on the metric mentioned:

1. Use section `"kpis"` for these KPI metrics:
   - `sales_growth`: Year-over-year sales growth
   - `gross_margin`: Gross margin %
   - `COGS_perc_sales`: COGS as '%' of sales
   - `rnd_perc_sales`: R&D as '%' of sales
   - `rnd_growth`: R&D growth rate
   - `sng_perc_sales`: SG&A as '%' of sales
   - `income_margin`: Income margin %
   - `ebt`: Earnings Before Taxes
   - `tax_margin`: Tax margin %
   - `net_margin`: Net margin %
   - `margin_growth`: Margin growth rate
   - `eps_growth`: EPS growth rate

2. Use section `"processed_data"` for raw reported values like:
   - `net_sales_products`, `net_sales_services`, `net_sales_total`
   - `cost_of_sales_products`, `cost_of_sales_total`
   - `gross_margin`, `operating_expenses_*`, `operating_income`
   - `other_income_or_expense_net`, `income_before_tax`, `net_income`
   - `earnings_per_share_basic`, `earnings_per_share_diluted`
   - `shares_used_in_computing_eps_basic`, `shares_used_in_computing_eps_diluted`

Use the exact field names as inputs when calling the extractor.

---

📈 **When the user requests a graph**:

1. Use `GraphGeneratorTool` to generate Python code for the graph.
2. Use `ExecuteGraph_Tool` to run the code and produce a PNG image.
3. Return only the link to the image or an appropriate visualization preview.

---

📄 **When the user asks for a complete report**:

Use the `ReportWriter_Tool` to generate a hedge fund–style investment report based on available KPIs and graph images. You must:
- You need to call the graph_tool everytime for each kpi
- Pass a dictionary of KPI name-value pairs
- Optionally include a list of graph image paths
- Include a tone and purpose if provided by the user
- Return only the link to the pdf path or an appropriate visualization preview.

---

🛑 **Do NOT**:
- Return tool response as raw dictionaries or JSON
- Answer questions without using a tool


🎯 Your role is to act like a data-first financial assistant — accurate, efficient, and structured.
"""
        )
        agent_memory.chat_memory.add_message(SystemMessage(content=initial_message))
        # Create the agent using your tools and the provided prompt
        agent = create_structured_chat_agent(llm=llm_agent, tools=tools, prompt=prompt)
        st.session_state.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=agent_memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=50
        )

    # --- User Input and Agent Call ---
    user_question = st.chat_input("Ask a question about the 10-K reports...")
    if user_question:
        with st.chat_message("user"):
            st.write(user_question)
        st.session_state.chat_history.append({"role": "user", "content": user_question})

        with st.spinner("Processing using the agent..."):
            result = st.session_state.agent_executor.invoke({
                "input": user_question,
                "chat_history": st.session_state.chat_history
            })
            ai_response = result.get("output", "No response returned.")
            if isinstance(ai_response, dict):
                ai_response_str = json.dumps(ai_response, indent=2)
            else:
                ai_response_str = ai_response
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response_str})
            
            # --- File Output Handling ---
            if isinstance(ai_response, str) and (
                ai_response.startswith("/tmp/") or ai_response.startswith("sandbox:/tmp/")
            ) and os.path.exists(ai_response):
                if ai_response.endswith(".png"):
                    # Display the image using st.image() wrapped in a chat message
                    with st.chat_message("assistant"):
                        st.image(ai_response, caption="Generated Graph", use_column_width=True)
                elif ai_response.endswith(".pdf"):
                    with st.chat_message("assistant"):
                        with open(ai_response, "rb") as file:
                            # Get a clean filename by removing /tmp/ prefix and adding a descriptive name
                            clean_filename = os.path.basename(ai_response).replace("sandbox:", "")
                            descriptive_name = f"financial_analysis_{clean_filename}"
                            st.download_button(
                                label="Download CSV",
                                data=file,
                                file_name=descriptive_name,
                                mime="text/csv"
                            )
            else:
                with st.chat_message("assistant"):
                    st.write(ai_response_str)

if __name__ == "__main__":
    main()