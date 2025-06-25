# FinAI – AI-Powered Financial Report Assistant

**FinAI** is a multi-agent system designed to automate the analysis of SEC 10-K financial reports. It leverages **LangChain**, **LangGraph**, and **Streamlit** to extract key financial metrics, summarize insights, and generate customized visual reports.

🗓️ Presented at the **Stevens Analytics Expo** on **May 16, 2025**

---

## 📌 Project Overview

FinAI simplifies the manual effort required in parsing complex financial documents by using agentic logic powered by LLMs. It breaks down the 10-K report into sections, assigns each agent a task, and compiles the results into a visual, interactive dashboard.

Key capabilities include:

- KPI extraction across multiple fiscal years
- Year-over-year trend analysis
- Risk factor summarization
- Customized graphs and visual reporting
- Customized reports explaining the trends
- Interactive Streamlit front-end for end-user experience

---

## 🧠 Tech Stack

- **LangChain** – for orchestrating LLM behavior
- **OpenAI API** – for summarization and reasoning
- **Streamlit** – for building the user interface
- **Python** – core logic and data processing

---

## 🧬 Data Lineage

FinAI follows a structured and modular data flow to ensure transparency, scalability, and reproducibility:

1. **User Input**: Upload or link a 10-K filing.
2. **Agent Assignment**:
   - Extractor agent extracts the data from the 10-k report
   - KPI Agent computes structured metrics
   - Trend Agent performs comparative reasoning
   - Risk Agent summarizes forward-looking sections
4. **Graph Generator**: Builds custom graphs from tabular insights.
5. **Report Generator**: Builds customizable reports highlighting trends,custom explanation on KPI's from the data along with potential risks and rewards
6. **Final Output**: All outputs are rendered in a unified Streamlit dashboard. All the reports and graphs have download options.

This modular approach allows plug-and-play extension for additional financial insights or industry-specific modules.


---
[Fin AI team Poster.pdf](https://github.com/user-attachments/files/20896178/Fin.AI.team.Poster.pdf)



