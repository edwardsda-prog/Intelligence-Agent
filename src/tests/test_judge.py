import sys
sys.path.append("/usr/local/google/home/edwardsda/Documents/Intelligence-Agent/src")
from tests.test_prompts import E2EPromptTestSuite
import time

suite = E2EPromptTestSuite(mode='live', project_id='antig-dave', location='us-central1')
print("Testing judge")
start = time.time()
res = suite._evaluate_with_llm("test prompt", "test response", "test objective")
print(f"Result: {res}")
print(f"Elapsed: {time.time() - start}")
