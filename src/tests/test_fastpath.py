import sys
sys.path.append("/usr/local/google/home/edwardsda/Documents/Intelligence-Agent/src")
from agent.agent import apply_fast_path

class DummyContext:
    def __init__(self, msg):
        self.request = type('obj', (object,), {'message': msg})

print(apply_fast_path(callback_context=DummyContext("Hello, what are your operational capabilities?")))

from tests.test_prompts import E2EPromptTestSuite
import time
# Let's override apply_fast_path temporarily in the test
import agent.agent
def custom_fast_path(*args, **kwargs):
    print("FAST PATH ARGS:", args)
    print("FAST PATH KWARGS:", kwargs)
    return agent.agent.apply_fast_path(*args, **kwargs)

# Actually, I can't easily patch it since it's passed to Agent during initialization.
# Let's just modify agent.py temporarily to print them.
