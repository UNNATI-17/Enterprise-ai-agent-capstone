import json
from datetime import datetime
from .enterprise_tools import (
    JSONExtractorTool,
    KPITool,
    BusinessSummaryTool,
    EmailGeneratorTool,
    FileReaderTool,
)
from .memory_service import SessionMemory, MemoryBank, MemoryService

# ======================================================================
# MAIN ENTERPRISE AGENT
# ======================================================================

class EnterpriseAgent:

    def __init__(self):
        # Load tools
        self.json_tool = JSONExtractorTool()
        self.kpi_tool = KPITool()
        self.summary_tool = BusinessSummaryTool()
        self.email_tool = EmailGeneratorTool()
        self.file_tool = FileReaderTool()

        # Load memory
        self.memory = MemoryService()
        self.session_id = self.memory.start_session()

    def call_llm(self, prompt: str) -> str:
        return f"[Simulated LLM Response] {prompt[:150]}"

    def process_request(self, user_input: str):
        self.memory.add_message(self.session_id, "user", user_input)
        if "summarize" in user_input.lower():
            return self._handle_summary(user_input)
        elif "kpi" in user_input.lower() or "conversion" in user_input.lower() or "profit" in user_input.lower():
            return self._handle_kpi(user_input)
        elif "email" in user_input.lower():
            return self._handle_email(user_input)
        elif "extract json" in user_input.lower() or "json" in user_input.lower():
            return self._handle_json(user_input)
        elif "read file" in user_input.lower():
            return self._handle_file(user_input)
        else:
            response = self.call_llm(f"Process this: {user_input}")
            self.memory.add_message(self.session_id, "agent", response)
            return response

    def _handle_summary(self, text):
        result = self.summary_tool.summarize(text)
        self.memory.add_message(self.session_id, "agent", str(result))
        return result

    def _handle_kpi(self, user_input: str):
        import re
        sales = float(re.search(r"sales\s*=\s*(\d+)", user_input).group(1)) if "sales" in user_input else 0
        expense = float(re.search(r"expense\s*=\s*(\d+)", user_input).group(1)) if "expense" in user_input else 0
        leads = int(re.search(r"leads\s*=\s*(\d+)", user_input).group(1)) if "leads" in user_input else 1
        customers = int(re.search(r"customers\s*=\s*(\d+)", user_input).group(1)) if "customers" in user_input else 1
        result = self.kpi_tool.calculate(sales, expense, leads, customers)
        self.memory.add_message(self.session_id, "agent", str(result))
        return result

    def _handle_email(self, user_input: str):
        subject = "Automated Business Update"
        body = self.call_llm(f"Write a professional email about: {user_input}")
        email = self.email_tool.generate_email(subject, body)
        self.memory.add_message(self.session_id, "agent", email)
        return email

    def _handle_json(self, text):
        extracted = self.json_tool.extract_json(text)
        self.memory.add_message(self.session_id, "agent", str(extracted))
        return extracted

    def _handle_file(self, user_input: str):
        import re
        match = re.search(r"read file (.+)", user_input)
        if not match:
            return "No filepath found."
        path = match.group(1).strip()
        content = self.file_tool.read_text_file(path)
        self.memory.add_message(self.session_id, "agent", content)
        return content

    def get_conversation_history(self):
        return self.memory.get_session_history(self.session_id)

# ======================================================================
# DEMO
# ======================================================================
if __name__ == "__main__":
    agent = EnterpriseAgent()
    print(agent.process_request("Summarize this document. Today the sales increased sharply."))
    print(agent.process_request("Calculate KPI for sales=50000 expense=20000 leads=400 customers=50"))
    print(agent.process_request("Generate email informing client about KPI results."))
