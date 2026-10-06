import sys
sys.path.append("/usr/local/google/home/edwardsda/Documents/Intelligence-Agent/src")
from tests.test_prompts import E2EPromptTestSuite
import time

suite = E2EPromptTestSuite(mode='live', project_id='antig-dave', location='us-central1')
suite.results = []
session_id = f"scenario-1-session-{int(time.time())}"

print("Testing S1-P2 (BigQuery MCP)")
p2 = "List all friendly assets and ew_intercepts frequencies in dataset mission_data."
start = time.time()
resp2 = suite._query_agent(p2, session_id=session_id)
print(f"Response: {resp2}")
print(f"Elapsed: {time.time() - start}")
