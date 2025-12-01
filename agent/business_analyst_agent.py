# agent/business_analyst_agent.py

from .enterprise_tools import KPITool
from .memory_service import MemoryService
import re

class BusinessAnalystAgent:
    def __init__(self):
        self.kpi_tool = KPITool()
        self.memory = MemoryService()
        self.session_id = self.memory.start_session()

    def handle(self, user_input: str):
        # Save user input
        self.memory.add_message(self.session_id, "user", user_input)

        # Automatically extract numeric values from input
        sales = float(re.search(r"sales\s*=\s*(\d+)", user_input).group(1)) if "sales" in user_input else 0
        expense = float(re.search(r"expense\s*=\s*(\d+)", user_input).group(1)) if "expense" in user_input else 0
        leads = int(re.search(r"leads\s*=\s*(\d+)", user_input).group(1)) if "leads" in user_input else 1
        customers = int(re.search(r"customers\s*=\s*(\d+)", user_input).group(1)) if "customers" in user_input else 1

        result = self.kpi_tool.calculate(sales, expense, leads, customers)

        # Save agent response
        self.memory.add_message(self.session_id, "agent", str(result))
        return {"agent": "Business Analyst Agent", "result": result}