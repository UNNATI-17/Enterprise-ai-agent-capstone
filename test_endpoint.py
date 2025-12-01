import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:8000"

# -------------------------------
# Define test cases for each endpoint
# -------------------------------
test_cases = {
    "documentation": {"message": "Summarize the project documentation."},
    "research": {"message": "Provide research data on AI agent capabilities in enterprises."},
    "business_analyst": {"message": "sales=120000 expense=50000 leads=200 customers=150"},
    "chat": {"message": "Hello, how are you?"},
    "ask": {"message": "Tell me about Unnati's role in the company."},
}

# -------------------------------
# Function to call an endpoint
# -------------------------------
def call_endpoint(endpoint, payload):
    url = BASE_URL + endpoint
    try:
        response = requests.post(url, json=payload, timeout=60)  # 1 min timeout
        response.raise_for_status()
        return endpoint, response.json()
    except requests.exceptions.Timeout:
        return endpoint, {"error": "Timeout: The server took too long to respond."}
    except requests.exceptions.RequestException as e:
        return endpoint, {"error": str(e)}

# -------------------------------
# Run all tests concurrently
# -------------------------------
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(call_endpoint, f"/{ep}", payload) for ep, payload in test_cases.items()]
    for future in as_completed(futures):
        endpoint, result = future.result()
        print(f"\n--- Testing endpoint: {endpoint} ---")
        print(json.dumps(result, indent=4))