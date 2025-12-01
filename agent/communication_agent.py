# agent/communication_agent.py
from agent.enterprise_tools import EmailGeneratorTool
from agent.memory_service import MemoryService

class CommunicationAgent:
    def __init__(self):
        self.email_tool = EmailGeneratorTool()
        self.memory = MemoryService()
        self.session_id = self.memory.start_session()

    def handle(self, user_input: str):
        # Save user input
        self.memory.add_message(self.session_id, "user", user_input)

        # Generate email content using LLM mock
        subject = "Automated Business Email"
        body = f"[Simulated LLM Response] {user_input[:150]}"
        email = self.email_tool.generate_email(subject, body)

        # Save agent response
        self.memory.add_message(self.session_id, "agent", email)
        return {"agent": "Communication Agent", "result": email}
