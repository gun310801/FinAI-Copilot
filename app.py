# import streamlit as st
# import os, json
# import openai
# from dotenv import load_dotenv
# from langchain.agents import AgentExecutor, create_structured_chat_agent
# from langchain import hub
# from langchain.memory import ConversationBufferMemory
# from langchain_openai import ChatOpenAI
# from chain_scoo import get_data_from_docs
# from financial_model import financial_model
# from tools.extractor import Extract_Tool
# import pandas as pd

# # Import for adding system messages
# from langchain_core.messages import SystemMessage


# # -------------------------------
# # Custom Memory Class
# # -------------------------------
# class StringifyConversationBufferMemory(ConversationBufferMemory):
#    class StringifyConversationBufferMemory(ConversationBufferMemory):
#     def _get_input_output(self, inputs: dict, outputs: dict):
#         # Ensure outputs is always a dictionary.
#         if not isinstance(outputs, dict):
#             outputs = {"output": outputs if isinstance(outputs, str) else json.dumps(outputs, indent=2)}
#         return super()._get_input_output(inputs, outputs)

#     def save_context(self, inputs: dict, outputs: dict) -> None:
#         # Ensure outputs is always a dictionary.
#         print("i reached here")
#         if not isinstance(outputs, dict):
#             outputs = {"output": outputs if isinstance(outputs, str) else json.dumps(outputs, indent=2)}
#         super().save_context(inputs, outputs)
#         print("I used this")

# def load_api_key(env_file="key.env"):
#     load_dotenv(env_file)
#     return os.getenv('OPEN_AI_API_KEY')

# st.title("FinAI Co-Pilot")

# def initialize_tools():
#     tools = [Extract_Tool]
        
#     return tools

# def flatten_json(json_obj, parent_key='', sep='_'):
#     """Flattens a nested JSON object into a single dictionary."""
#     items = []
#     for k, v in json_obj.items():
#         new_key = parent_key + sep + k if parent_key else k
#         if isinstance(v, dict):
#             items.extend(flatten_json(v, new_key, sep=sep).items())
#         else:
#             items.append((new_key, v))
#     return dict(items)

# def save_data_to_json(data, filename="financial_data.json"):
#     with open(filename, 'w') as f:
#         json.dump(data, f, indent=4)
#     return filename

# def load_and_process_json(filename):
#     with open(filename, 'r') as f:
#         data = json.load(f)
#     text_data = json.dumps(data, indent=2)
#     return text_data

# def open_modal():
#     st.session_state['show_modal'] = True

# def main():
#     api_key = load_api_key()
#     # --- Session State Initialization ---
#     if "conversation" not in st.session_state:
#         st.session_state.conversation = None
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []
#     if "data" not in st.session_state:
#         st.session_state.data = None
#     if 'show_modal' not in st.session_state:
#         st.session_state['show_modal'] = False

#     st.sidebar.title("10-K Reports")
#     pdf_files = st.sidebar.file_uploader(
#         "Upload your 10-K PDF files", type=['pdf'], accept_multiple_files=True)
    
#     if pdf_files:
#         data = get_data_from_docs(pdf_files)
#         processed_data = {}
#         for item in data:
#             report_date = item['report_date']
#             item.pop("metadata")
#             item.pop("section")
#             flattened_item = flatten_json(item)
#             if 'report_date' in flattened_item:
#                 del flattened_item['report_date']
#             processed_data[report_date] = flattened_item

#         initial_output = {"processed_data": processed_data}
#         with open("output.json", "w") as f:
#             json.dump(initial_output, f, indent=4)    
#         kpis = financial_model(data)
#         table_data = []
#         for key, value_dict in kpis.items():
#             row = {"Metric": key}
#             row.update(value_dict)
#             table_data.append(row)

#         df_kpis = pd.DataFrame(table_data).set_index("Metric")
#         df = pd.DataFrame.from_dict(processed_data, orient='index').T
#         kpi_json = json.loads(df_kpis.to_json(orient='index'))
#         with open("output.json", "r") as f:
#             existing_data = json.load(f)

#         existing_data["kpis"] = kpi_json
#         with open("output.json", "w") as f:
#             json.dump(existing_data, f, indent=4)

#     st.write("Ask questions about the 10-K reports")
#     st.button("Open Details", on_click=open_modal)
#     if st.session_state['show_modal']:
#         st.write("Extracted Financial Data")
#         st.dataframe(df)
#         st.write("Extracted Financial KPIs")
#         st.dataframe(df_kpis)

#     # --- Display Chat History ---
#     for message in st.session_state.chat_history:
#         with st.chat_message(message["role"]):
#             st.write(message["content"])

#     # --- Agent Initialization ---
#     if "agent_executor" not in st.session_state:
#         tools = initialize_tools()
#         prompt = hub.pull("hwchase17/structured-chat-agent")
#         llm_agent = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)
#         # Create memory and add an initial system message
#         agent_memory = StringifyConversationBufferMemory(memory_key="chat_history", return_messages=True)
#         initial_message = (
#             """
#             You are an AI assistant that provides helpful and concise answers about 10‑K reports. You must utilize the provided extractor tool to retrieve specific metric data when required. Always respond only with the essential output, using raw data from the reports without any unnecessary commentary.
#             When a user asks a question that involves specific metrics, use the extractor tool. Determine the appropriate section based on the metrics mentioned in the question as follows:
#             For KPI-related metrics, set the section to "Kpis". These include:
#             sales growth (Year‑over‑year sales growth)
#             gross margin (Gross margin percentage)
#             COGS_perc_sales (Cost of Goods Sold as a percentage of sales)
#             rnd_perc_sales (Research & Development expenses as a percentage of sales)
#             rnd_growth (R&D growth rate)
#             sng_perc_sales (Selling & General expenses as a percentage of sales)
#             income_margin (Income margin percentage)
#             ebt (Earnings Before Taxes)
#             tax_margin (Tax margin percentage)
#             net_margin (Net margin percentage)
#             margin_growth (Overall margin growth rate)
#             eps_growth (Earnings Per Share growth rate)

#             For raw processed data metrics, set the section to "processed_data". These include:
#             net_sales_products (net sales product),
#             net_sales_services (net sales services),
#             net_sales_total (net sales)
#             cost_of_sales_products (cogs products)
#             cost_of_sales_services (cogs services)
#             cost_of_sales_total (cogs)
#             gross_margin (gross margin)
#             operating_expenses_research_and_development (rnd)
#             operating_expenses_selling_general_and_administrative (sng)
#             operating_expenses_total (operating expenses)
#             operating_income (operating income)
#             other_income_or_expense_net (other income or expense net)
#             income_before_tax (income before tax)
#             tax_provision (tax provision)
#             net_income (net income)
#             earnings_per_share_basic (eps basic)
#             earnings_per_share_diluted (eps diluted)
#             shares_used_in_computing_eps_basic ( shares in computing eps basic)
#             shares_used_in_computing_eps_diluted (shares in computes eps diluted)


#             """
#         )
#         agent_memory.chat_memory.add_message(SystemMessage(content=initial_message))
#         # Create the agent using your tools and the provided prompt
#         agent = create_structured_chat_agent(llm=llm_agent, tools=tools, prompt=prompt)
#         st.session_state.agent_executor = AgentExecutor.from_agent_and_tools(
#             agent=agent,
#             tools=tools,
#             memory=agent_memory,
#             verbose=True,
#             handle_parsing_errors=True,
#             max_iterations=50
#         )

#     # --- User Input and Agent Call ---
#     user_question = st.chat_input("Ask a question about the 10-K reports...")
#     if user_question:
#         with st.chat_message("user"):
#             st.write(user_question)
#         st.session_state.chat_history.append({"role": "user", "content": user_question})

#         with st.spinner("Processing using the agent..."):
#             result = st.session_state.agent_executor.invoke({
#                 "input": user_question,
#                 "chat_history": st.session_state.chat_history
#             })
#             ai_response = result.get("output", "No response returned.")
#             if not isinstance(ai_response, str):
#                 ai_response_str = json.dumps(ai_response, indent=2)
#             else:
#                 ai_response_str = ai_response
#             st.session_state.chat_history.append({"role": "assistant", "content": ai_response_str})
            
#             # --- File Output Handling ---
#             if (ai_response_str.startswith("/tmp/") or ai_response_str.startswith("sandbox:/tmp/")) and os.path.exists(ai_response_str):
#                 if ai_response_str.endswith(".png"):
#                     with st.chat_message("assistant"):
#                         st.image(ai_response_str)
#                 elif ai_response_str.endswith(".csv"):
#                     with st.chat_message("assistant"):
#                         with open(ai_response_str, "rb") as file:
#                             st.download_button(
#                                 label="Download CSV",
#                                 data=file,
#                                 file_name=os.path.basename(ai_response_str),
#                                 mime="text/csv"
#                             )
#             else:
#                 with st.chat_message("assistant"):
#                     st.write(ai_response_str)

# if __name__ == "__main__":
#     main()
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
import pandas as pd

# Import for adding system messages
from langchain_core.messages import SystemMessage

def load_api_key(env_file="key.env"):
    load_dotenv(env_file)
    return os.getenv('OPEN_AI_API_KEY')

st.title("FinAI Co-Pilot")

def initialize_tools():
    tools = [Extract_Tool]
        
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
            You are an AI assistant that provides helpful and concise answers about 10‑K reports. You must utilize the provided extractor tool to retrieve specific metric data when required. Always respond only with the essential output, using raw data from the reports without any unnecessary commentary.Important:Do not return a dictionary.
            When a user asks a question that involves specific metrics, use the extractor tool. Determine the appropriate section based on the metrics mentioned in the question as follows:
            For KPI-related metrics, set the section to "Kpis". These include:
            sales growth (Year‑over‑year sales growth)
            gross margin (Gross margin percentage)
            COGS_perc_sales (Cost of Goods Sold as a percentage of sales)
            rnd_perc_sales (Research & Development expenses as a percentage of sales)
            rnd_growth (R&D growth rate)
            sng_perc_sales (Selling & General expenses as a percentage of sales)
            income_margin (Income margin percentage)
            ebt (Earnings Before Taxes)
            tax_margin (Tax margin percentage)
            net_margin (Net margin percentage)
            margin_growth (Overall margin growth rate)
            eps_growth (Earnings Per Share growth rate)

            For raw processed data metrics, set the section to "processed_data". These include:
            net_sales_products (net sales product),
            net_sales_services (net sales services),
            net_sales_total (net sales)
            cost_of_sales_products (cogs products)
            cost_of_sales_services (cogs services)
            cost_of_sales_total (cogs)
            gross_margin (gross margin)
            operating_expenses_research_and_development (rnd)
            operating_expenses_selling_general_and_administrative (sng)
            operating_expenses_total (operating expenses)
            operating_income (operating income)
            other_income_or_expense_net (other income or expense net)
            income_before_tax (income before tax)
            tax_provision (tax provision)
            net_income (net income)
            earnings_per_share_basic (eps basic)
            earnings_per_share_diluted (eps diluted)
            shares_used_in_computing_eps_basic ( shares in computing eps basic)
            shares_used_in_computing_eps_diluted (shares in computes eps diluted)


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
            if (ai_response.startswith("/tmp/") or ai_response.startswith("sandbox:/tmp/")) and os.path.exists(ai_response):
                if ai_response.endswith(".png"):
                    with st.chat_message("assistant"):
                        st.image(ai_response)
                elif ai_response.endswith(".csv"):
                    with st.chat_message("assistant"):
                        with open(ai_response, "rb") as file:
                            st.download_button(
                                label="Download CSV",
                                data=file,
                                file_name=os.path.basename(ai_response),
                                mime="text/csv"
                            )
            else:
                with st.chat_message("assistant"):
                    st.write(ai_response_str)

if __name__ == "__main__":
    main()