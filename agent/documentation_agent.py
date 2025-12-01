from agent.enterprise_tools import BusinessSummaryTool, FileReaderTool
from agent.memory_service import MemoryService
import re

class DocumentationAgent:
    def __init__(self):
        self.summary_tool = BusinessSummaryTool()
        self.file_tool = FileReaderTool()
        self.memory = MemoryService()
        self.session_id = self.memory.start_session()

    def handle(self, user_input: str):
        # Save user message
        self.memory.add_message(self.session_id, "user", user_input)

        user_lower = user_input.lower()

        # ------------------------------------
        # CASE 1: Summarization tasks
        # ------------------------------------
        if (
            "summarize" in user_lower
            or "report" in user_lower
            or "sop" in user_lower
            or "documentation" in user_lower
        ):
            try:
                # Use AI or summary tool safely
                result = self.summary_tool.generate_summary(user_input)
                if not result:
                    result = "[Summary Tool returned nothing]"
            except Exception as e:
                # Catch AI/tool errors to avoid timeout
                result = f"[Error in summarization tool: {e}]"

        # ------------------------------------
        # CASE 2: Read file
        # ------------------------------------
        elif "read file" in user_lower:
            match = re.search(r"read file (.+)", user_input, re.IGNORECASE)
            if match:
                filepath = match.group(1).strip()
                try:
                    result = self.file_tool.read_file(filepath)
                except Exception as e:
                    result = f"❌ Failed to read file: {e}"
            else:
                result = "❌ No file path found. Example: 'read file data/sample.txt'"

        # ------------------------------------
        # CASE 3: Default fallback
        # ------------------------------------
        else:
            result = f"[Simulated Documentation Response] {user_input[:150]}"

        # Save agent response
        self.memory.add_message(self.session_id, "agent", str(result))

        return {"agent": "Documentation Agent", "result": result}