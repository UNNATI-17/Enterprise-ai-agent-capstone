# api/server.py
import sys
import os
import json
import asyncio
from functools import partial
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- optional import for Gemini (only used inside worker) ---
import google.generativeai as genai

# -------------------------------
# ADD PROJECT ROOT TO PYTHON PATH
# -------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# -------------------------------
# FASTAPI SETUP
# -------------------------------
app = FastAPI(title="Enterprise AI Agent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# REQUEST MODEL
# -------------------------------
class Query(BaseModel):
    message: str

# -------------------------------
# LAZY GLOBALS (no heavy work at import)
# -------------------------------
_doc_agent = None
_research_agent = None
_ba_agent = None
_orchestrator = None

# simple fake DB used by the /ask tool-call example
_database = {
    "Unnati": {"role": "Frontend Developer", "experience": "2 years", "salary": "₹6 LPA"},
    "Priyanka": {"role": "Team Lead", "experience": "5 years", "salary": "₹12 LPA"},
    "Bhoomi": {"role": "Backend Developer", "experience": "3 years", "salary": "₹9 LPA"},
}

# -------------------------------
# HELPERS: lazy create agents
# -------------------------------
def get_doc_agent():
    global _doc_agent
    if _doc_agent is None:
        from agent.documentation_agent import DocumentationAgent
        print("Instantiating DocumentationAgent...")
        _doc_agent = DocumentationAgent()
    return _doc_agent

def get_research_agent():
    global _research_agent
    if _research_agent is None:
        from agent.research_agent import ResearchAgent
        print("Instantiating ResearchAgent...")
        _research_agent = ResearchAgent()
    return _research_agent

def get_ba_agent():
    global _ba_agent
    if _ba_agent is None:
        from agent.business_analyst_agent import BusinessAnalystAgent
        print("Instantiating BusinessAnalystAgent...")
        _ba_agent = BusinessAnalystAgent()
    return _ba_agent

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from agent.multi_agent_orchestrator import MultiAgentOrchestrator
        print("Instantiating MultiAgentOrchestrator...")
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator

def get_employee_details(name: str):
    return _database.get(name)

# -------------------------------
# RUN BLOCKING FUNCTIONS SAFELY
# -------------------------------
async def run_blocking(func, *args):
    """
    Run blocking function in default ThreadPoolExecutor.
    Returns the function result (or raises exception).
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args))

# -------------------------------
# GEMINI / GENAI WRAPPER (runs in worker thread)
# - constructs/configures model inside the worker
# - applies a safe timeout externally via requests timeout or asyncio.wait_for if needed
# -------------------------------
def gemini_generate_blocking(prompt: str, model_name: str = "gemini-2.0-flash-thinking-exp", timeout_seconds: int = 20):
    """
    This function runs entirely in a background thread to avoid blocking the event loop.
    It configures genai using env GOOGLE_API_KEY (must be set), creates the model and calls generate_content.
    It intentionally catches exceptions and returns a dict-like fallback to the caller.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "GOOGLE_API_KEY environment variable not set."}

        # configure (idempotent)
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(model_name=model_name, tools=[{
            "function_declarations": [
                {
                    "name": "get_employee_details",
                    "description": "Fetch details like role, experience, salary for an employee.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Employee name"},
                        },
                        "required": ["name"],
                    },
                }
            ]
        }])

        # NOTE: generate_content can block depending on network; we rely on the caller's timeout.
        resp = model.generate_content(prompt, tools=model.tools)
        return resp

    except Exception as e:
        # return structured error to the async caller so it can respond quickly
        return {"error": f"Gemini call failed: {e}"}

# -------------------------------
# ENDPOINTS
# -------------------------------

@app.get("/")
async def root():
    # simple sanity-check endpoint; nothing heavy here
    return {"message": "Enterprise AI Agent API Running 🚀"}

@app.post("/documentation")
async def documentation_endpoint(data: Query):
    agent = get_doc_agent()
    try:
        result = await run_blocking(agent.handle, data.message)
        return result
    except Exception as e:
        return {"agent": "Documentation Agent", "error": f"{e}", "fallback": f"[Simulated] {data.message[:120]}"}

@app.post("/research")
async def research_endpoint(data: Query):
    agent = get_research_agent()
    try:
        result = await run_blocking(agent.handle, data.message)
        return result
    except Exception as e:
        return {"agent": "Research Agent", "error": f"{e}", "fallback": f"[Simulated Research] {data.message[:120]}"}

@app.post("/business_analyst")
async def business_analyst_endpoint(data: Query):
    agent = get_ba_agent()
    try:
        result = await run_blocking(agent.handle, data.message)
        return result
    except Exception as e:
        return {"agent": "Business Analyst Agent", "error": f"{e}", "fallback": f"[Simulated BA] {data.message[:120]}"}

@app.post("/chat")
async def chat_endpoint(data: Query):
    # very fast echo chat
    return {"reply": f"Chat agent says: {data.message}"}

@app.post("/ask")
async def ask_agent(query: Query):
    """
    Routing first to orchestrator; if orchestrator says no suitable agent,
    we call Gemini in a worker thread using gemini_generate_blocking.
    """
    orch = get_orchestrator()
    try:
        local_response = await run_blocking(orch.route, query.message)

        # If orchestrator explicitly indicates no suitable agent (string), fallback to Gemini
        if isinstance(local_response, str) and local_response.startswith("No suitable agent"):
            # run Gemini generation in a worker thread (this returns quickly with an error dict on failure)
            resp = await run_blocking(gemini_generate_blocking, query.message)
            if isinstance(resp, dict) and resp.get("error"):
                return {"answer": f"[Gemini error] {resp['error']}"}

            # attempt to extract tool function call from response safely
            try:
                for part in getattr(resp.candidates[0].content, "parts", []):
                    if hasattr(part, "function_call") and part.function_call:
                        fn = part.function_call
                        args = json.loads(fn.args)
                        if fn.name == "get_employee_details":
                            emp = get_employee_details(args["name"])
                            if emp:
                                return {
                                    "answer": f"{args['name']} is a {emp['role']} with {emp['experience']} experience, earning {emp['salary']}."
                                }
                            else:
                                return {"answer": "⚠️ Employee not found."}
                # fallback to text
                return {"answer": getattr(resp, "text", "")}
            except Exception as e:
                return {"answer": f"[Gemini parse error] {e}"}

        # orchestrator returned something usable
        return {"answer": local_response}

    except Exception as e:
        # ensure we never hang forever
        return {"answer": f"[Server error] {e}"}
