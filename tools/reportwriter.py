# === 📦 IMPORTS ===
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader
from langchain.chat_models import ChatOpenAI
import tempfile
import os
from dotenv import load_dotenv
import openai

# Load API key from the environment file
load_dotenv("key.env")
key_string = os.getenv('OPEN_AI_API_KEY')
openai.api_key = key_string

class ReportWriterToolArgs(BaseModel):
    kpis: Dict[str, str] = Field(
        ..., description="Key performance indicators extracted from a company's 10-K filing"
    )
    graph_paths: List[str] = Field(
        ..., description="List of file paths to graph images (PNG or JPG)"
    )
    tone: Optional[str] = Field(
        None, description="Optional tone for the report, e.g., 'formal', 'concise'"
    )
    purpose: Optional[str] = Field(
        None, description="Optional purpose of the report, e.g., 'for internal use'"
    )
def report_writer_logic(
    kpis: Dict[str, str],
    graph_paths: List[str],
    tone: Optional[str] = None,
    purpose: Optional[str] = None
) -> str:
    from langchain.chat_models import ChatOpenAI
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.utils import ImageReader
    import tempfile

    llm = ChatOpenAI(model="gpt-4o",temperature=0.4,openai_api_key=key_string)

    # Build KPI block
    kpi_text = "\n".join(f"- {k}: {v}" for k, v in kpis.items())

    # Final Prompt
    prompt = f"""You are a professional financial analyst tasked with creating a hedge fund investment report. Your report will be based on thorough financial analysis of KPIs extracted from a company's 10-K SEC filing. This report will be converted into a downloadable PDF using the PDF Report Generator tool.

Please follow these steps to complete your task:

1. Analyze the provided financial KPIs to evaluate the company's performance.
2. Write a detailed hedge fund–style investment report based on your findings.
3. Ensure your report is well-structured and formatted for PDF delivery.

Here is the financial data for the analysis:
<financial_kpis>
{kpi_text}
</financial_kpis>

{f"Use a {tone} tone in your writing." if tone else ""}
{f"This report is intended {purpose}." if purpose else ""}

Before writing the report, conduct your analysis inside <financial_analysis> tags. Cover the following:

1. Interpret the key KPIs provided.
2. Identify trends, fluctuations, and performance outliers.
3. Summarize the company's financial strengths and weaknesses.
4. Outline risks, opportunities, and provide a final financial health assessment.
5. these are the graph links:{graph_paths}


Your final report should follow this structure:

1. Executive Summary  
2. Company Overview  
3. Filing Highlights  
4. Financial Performance Analysis    
5. Conclusion

Be clear, data-driven, and insightful. When finished, your report will be passed to the PDF Report Generator tool. Begin your analysis and report writing now.
"""

    report_body = llm.predict(prompt)

    # Generate PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file_path = tmp.name
        c = canvas.Canvas(file_path, pagesize=LETTER)
        width, height = LETTER

        text_obj = c.beginText(40, height - 50)
        text_obj.setFont("Helvetica", 11)

        for line in report_body.split("\n"):
            if text_obj.getY() < 60:
                c.drawText(text_obj)
                c.showPage()
                text_obj = c.beginText(40, height - 50)
                text_obj.setFont("Helvetica", 11)
            text_obj.textLine(line.strip())
        c.drawText(text_obj)

        # Add graphs
        y = text_obj.getY() - 20
        for path in graph_paths:
            try:
                img = ImageReader(path)
                iw, ih = img.getSize()
                aspect = ih / float(iw)
                w = width - 80
                h = w * aspect

                if y - h < 60:
                    c.showPage()
                    y = height - 60

                c.drawImage(img, 40, y - h, width=w, height=h)
                y -= (h + 20)
            except Exception as e:
                print(f"Could not load image {path}: {e}")

        c.save()

    return f"Report saved at: {file_path}"

from langchain.tools import StructuredTool

ReportWriter_Tool = StructuredTool.from_function(
    func=report_writer_logic,
    name="ReportWriter_Tool",
    description="Generates a hedge fund–style investment report from KPIs and graphs, then saves it as a PDF.",
    args_schema=ReportWriterToolArgs
)
