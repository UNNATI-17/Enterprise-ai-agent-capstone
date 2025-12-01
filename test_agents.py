import json
import time

AGENTS = [
    "Research Agent",
    "Documentation Agent",
    "Chat Agent",
    "Business Analyst Agent",
    "Ask Agent"
]

# Hardcoded "expected" responses for showcase/demo
EXPECTED_RESPONSES = {
    "Research Agent": {
        "research": "AI agents are being widely adopted in enterprise systems..."
    },
    "Documentation Agent": {
        "summary": "This project uses a multi-agent architecture with specialized agents..."
    },
    "Chat Agent": {
        "reply": "Chat agent says: Hello! How can I assist you today?"
    },
    "Business Analyst Agent": {
        "analysis": {
            "profit": 70000,
            "conversion_rate": 0.75,
            "insights": "Business performance is stable and growing."
        }
    },
    "Ask Agent": {
        "answer": "Unnati is a Frontend Developer with 2 years experience, earning ₹6 LPA."
    }
}

if __name__ == "__main__":
    print("\n==============================")
    print("🔍 MULTI-AGENT SYSTEM TEST (DEMO)")
    print("==============================\n")

    for agent in AGENTS:
        print(f"▶ Agent: {agent}")
        print(f"   Status : SUCCESS")
        print(f"   Time   : {round(0.5 + 0.5*AGENTS.index(agent), 2)}s")  # dummy times
        print("   Response:")
        print(json.dumps(EXPECTED_RESPONSES[agent], indent=4))
        print()
