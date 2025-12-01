# agent/research_agent.py

from .enterprise_tools import JSONExtractorTool
from .memory_service import MemoryService
import re

class ResearchAgent:
    def __init__(self):
        self.json_tool = JSONExtractorTool()
        self.memory = MemoryService()
        self.session_id = self.memory.start_session()

    def handle(self, user_input: str):
        # Save user input
        self.memory.add_message(self.session_id, "user", user_input)

        # Mock web search or competitor research
        research_data = f"[Simulated Research Data] {user_input[:150]}"

        # Extract structured JSON if possible
        extracted_json = self.json_tool.extract_json(f'{{"research": "{research_data}"}}')

        # Save agent response
        self.memory.add_message(self.session_id, "agent", str(extracted_json))

        return {"agent": "Research Agent", "result": extracted_json}