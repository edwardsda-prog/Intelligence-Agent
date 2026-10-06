import sys
import os
sys.path.append("/usr/local/google/home/edwardsda/Documents/Intelligence-Agent/src")
import time
from tests.test_prompts import E2EPromptTestSuite

suite = E2EPromptTestSuite(mode='live', project_id='antig-dave', location='us-central1')
suite.results = []
print("Testing query agent S1")
start = time.time()
resp = suite._query_agent("Hello, what are your operational capabilities?", session_id=f"scenario-1-s1-{int(time.time())}")
print(f"Response: {resp}")
print(f"Elapsed: {time.time() - start}")
