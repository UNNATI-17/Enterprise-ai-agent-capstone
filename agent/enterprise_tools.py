import json
import re
from datetime import datetime


# ================================================
# ENTERPRISE CUSTOM TOOLS
# ================================================

class JSONExtractorTool:
    """
    Extracts valid JSON from LLM outputs.
    Useful when LLM outputs are messy or non-structured.
    """

    def extract_json(self, text: str):
        # Try direct JSON loading
        try:
            json_data = json.loads(text)
            return {"status": "success", "data": json_data}
        except:
            pass

        # Try extracting JSON substring
        try:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                cleaned = json_match.group()
                return {"status": "success", "data": json.loads(cleaned)}
        except:
            pass

        return {"status": "failed", "reason": "Invalid JSON format"}


class KPITool:
    """
    Converts business numbers into meaningful KPIs (profit, margin, conversion, etc.)
    """

    def calculate(self, sales: float, expense: float, leads: int, customers: int):
        try:
            profit = sales - expense
            conversion_rate = (customers / leads) if leads > 0 else 0
            margin = (profit / sales) if sales > 0 else 0
            avg_revenue = (sales / customers) if customers > 0 else 0

            return {
                "sales": sales,
                "expense": expense,
                "profit": profit,
                "profit_margin": round(margin, 4),
                "conversion_rate": round(conversion_rate, 4),
                "avg_revenue_per_customer": round(avg_revenue, 4)
            }

        except Exception as e:
            return {"error": str(e)}


class BusinessSummaryTool:
    """
    Summarizes text in a clean business-friendly format.
    (No AI calls — instant result, no blocking.)
    """

    def generate_summary(self, text: str):
        try:
            # basic summarization (first 3 sentences)
            sentences = text.split('.')
            summary = sentences[:3]

            return {
                "summary": " ".join([s.strip() for s in summary if s.strip()]),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "summary": "",
                "error": str(e)
            }


class EmailGeneratorTool:
    """
    Generates clean enterprise-style email templates.
    """

    def generate_email(self, subject: str, body: str, recipient="Team"):
        return f"""
To: {recipient}
Subject: {subject}

{body}

Regards,
Enterprise AI Agent
"""


class FileReaderTool:
    """
    Simple text file reader.
    (Supports TXT files — extendable for PDF, DOCX later.)
    """

    def read_file(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
