# agent/multi_agent_orchestrator.py
import re
from typing import Any, Dict

from agent.enterprise_tools import (
    JSONExtractorTool,
    KPITool,
    BusinessSummaryTool,
    EmailGeneratorTool,
    FileReaderTool,
)
from agent.memory_service import MemoryService
from agent.main_agent import EnterpriseAgent

# Specialized Agents (these should use safe implementations similar to DocumentationAgent)
from agent.communication_agent import CommunicationAgent
from agent.documentation_agent import DocumentationAgent
from agent.research_agent import ResearchAgent
from agent.business_analyst_agent import BusinessAnalystAgent


class MultiAgentOrchestrator:
    """
    Safe Multi-Agent Orchestrator.

    - Uses local tools from enterprise_tools (no blocking LLM calls here).
    - Falls back to safe mock responses when an agent/tool fails.
    - Adds light debug prints to help you trace execution.
    """

    def __init__(self):
        self.memory = MemoryService()
        self.session_id = self.memory.start_session()

        # Tools (shared across main agent)
        self.tools = {
            "json": JSONExtractorTool(),
            "kpi": KPITool(),
            "summary": BusinessSummaryTool(),
            "email": EmailGeneratorTool(),
            "file": FileReaderTool(),
        }

        # Main agent (may internally call LLMs — we will call it with try/except)
        self.enterprise_agent = EnterpriseAgent()

        # 4 specialized agents (should be implemented safely elsewhere)
        self.agents = {
            "communication": CommunicationAgent(),
            "documentation": DocumentationAgent(),
            "research": ResearchAgent(),
            "business": BusinessAnalystAgent(),
        }

    # -------------------------
    # Public router
    # -------------------------
    def route(self, user_input: str) -> Dict[str, Any]:
        """
        Decide which agent or tool should handle the request.

        Returns a dict with at least {"agent": "...", "result": ...} or {"error": "..."}.
        """
        print("Orchestrator: route() received:", user_input)
        self.memory.add_message(self.session_id, "user", user_input)
        text = user_input.lower()

        try:
            # Tool-based shortcuts (fast, local)
            if any(x in text for x in ["kpi", "profit", "conversion"]):
                return self._run_kpi_agent(user_input)

            if "summarize" in text or "summary" in text:
                return self._run_summary_agent(user_input)

            if "email" in text or "mail" in text:
                return self._run_email_agent(user_input)

            if "json" in text:
                return self._run_json_agent(user_input)

            if "file" in text:
                return self._run_file_agent(user_input)

            # Specialized agent routing (call their .handle synchronously but safely)
            if any(x in text for x in ["research", "google", "market", "competitor"]):
                return self._safe_agent_call("research", user_input)

            if any(x in text for x in ["report", "sop", "documentation", "markdown"]):
                return self._safe_agent_call("documentation", user_input)

            if any(x in text for x in ["meeting", "message", "communication"]):
                return self._safe_agent_call("communication", user_input)

            if any(x in text for x in ["financial", "analysis", "kpi calculation"]):
                return self._safe_agent_call("business", user_input)

            # fallback to main agent (use safe wrapper)
            return self._run_enterprise_agent(user_input)

        except Exception as e:
            # Catch-all so orchestrator never crashes
            print("Orchestrator: unexpected error:", e)
            return {"agent": "Orchestrator", "error": f"Unexpected error: {e}"}

    # -------------------------
    # Safe wrappers / helpers
    # -------------------------
    def _safe_agent_call(self, agent_key: str, user_input: str) -> Dict[str, Any]:
        agent = self.agents.get(agent_key)
        if not agent:
            return {"agent": agent_key, "error": "Agent not found."}

        try:
            print(f"Orchestrator: calling agent '{agent_key}'")
            result = agent.handle(user_input)
            # ensure result is serializable
            self.memory.add_message(self.session_id, "agent", str(result))
            return {"agent": f"{agent_key.title()} Agent", "result": result}
        except Exception as e:
            print(f"Orchestrator: agent '{agent_key}' error:", e)
            return {
                "agent": f"{agent_key.title()} Agent",
                "error": f"Agent failed: {e}",
                "fallback": f"Simulated {agent_key} response for: {user_input[:120]}",
            }

    def _run_enterprise_agent(self, user_input: str) -> Dict[str, Any]:
        """
        Use the main enterprise agent as fallback. Call safely.
        """
        try:
            print("Orchestrator: calling main EnterpriseAgent.process_request()")
            # enterprise_agent.process_request might call LLMs — catch exceptions
            result = self.enterprise_agent.process_request(user_input)
            self.memory.add_message(self.session_id, "agent", str(result))
            return {"agent": "Enterprise Agent", "result": result}
        except Exception as e:
            print("Orchestrator: EnterpriseAgent failed:", e)
            return {
                "agent": "Enterprise Agent",
                "error": f"Enterprise agent failed: {e}",
                "fallback": f"Simulated enterprise response for: {user_input[:120]}",
            }

    # -------------------------
    # Tool handlers (instant, local)
    # -------------------------
    def _run_kpi_agent(self, user_input: str) -> Dict[str, Any]:
        try:
            # attempt to parse numbers from text (simple parser)
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", user_input)
            # mapping expects sales expense leads customers in that order if provided
            if len(nums) >= 4:
                sales = float(nums[0])
                expense = float(nums[1])
                leads = int(float(nums[2]))
                customers = int(float(nums[3]))
            else:
                # fallback sample values
                sales, expense, leads, customers = 0.0, 0.0, 0, 0

            result = self.tools["kpi"].calculate(sales, expense, leads, customers)
            self.memory.add_message(self.session_id, "agent", str(result))
            return {"agent": "KPI Agent", "result": result}
        except Exception as e:
            print("Orchestrator: KPI tool error:", e)
            return {"agent": "KPI Agent", "error": str(e)}

    def _run_summary_agent(self, user_input: str) -> Dict[str, Any]:
        try:
            result = self.tools["summary"].generate_summary(user_input)
            self.memory.add_message(self.session_id, "agent", str(result))
            return {"agent": "Summary Agent", "result": result}
        except Exception as e:
            print("Orchestrator: Summary tool error:", e)
            return {
                "agent": "Summary Agent",
                "error": str(e),
                "fallback": f"[Simulated Summary] {user_input[:150]}",
            }

    def _run_email_agent(self, user_input: str) -> Dict[str, Any]:
        try:
            # Generate a short local body using enterprise agent as helper (safe)
            try:
                # enterprise_agent.call_llm might be blocking — wrap in try
                body = self.enterprise_agent.call_llm(f"Write a short business email: {user_input}")
            except Exception as inner_e:
                print("Orchestrator: enterprise_agent.call_llm failed:", inner_e)
                body = f"[Auto-generated body] Regarding: {user_input[:120]}"

            subject = "Automated Email"
            email = self.tools["email"].generate_email(subject, body)
            self.memory.add_message(self.session_id, "agent", email)
            return {"agent": "Email Agent", "result": email}
        except Exception as e:
            print("Orchestrator: Email tool error:", e)
            return {
                "agent": "Email Agent",
                "error": str(e),
                "fallback": f"[Simulated Email] Subject: Automated Email\nBody: {user_input[:120]}",
            }

    def _run_json_agent(self, user_input: str) -> Dict[str, Any]:
        try:
            result = self.tools["json"].extract_json(user_input)
            self.memory.add_message(self.session_id, "agent", str(result))
            return {"agent": "JSON Extractor Agent", "result": result}
        except Exception as e:
            print("Orchestrator: JSON tool error:", e)
            return {"agent": "JSON Extractor Agent", "error": str(e)}

    def _run_file_agent(self, user_input: str) -> Dict[str, Any]:
        try:
            match = re.search(r"file (.+)", user_input, re.IGNORECASE)
            if not match:
                return {"agent": "File Agent", "error": "No file path found."}
            path = match.group(1).strip()
            # enterprise_tools.FileReaderTool has read_file method (fast)
            content = self.tools["file"].read_file(path)
            self.memory.add_message(self.session_id, "agent", content)
            return {"agent": "File Reader Agent", "content": content}
        except Exception as e:
            print("Orchestrator: File tool error:", e)
            return {"agent": "File Reader Agent", "error": str(e)}
