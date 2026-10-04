import json
from google.adk.agents import Agent
from src.agent.agent import root_agent, agent_runner

def test_callback(context, response):
    print("CONTEXT DIR:")
    print(dir(context))
    if hasattr(context, 'request'):
        print("REQUEST DIR:")
        print(dir(context.request))
        if hasattr(context.request, 'message'):
            print("MESSAGE:", context.request.message)
    return response

root_agent.after_model_callback = test_callback
res = agent_runner.invoke("Test prompt with MGRS 30UGC9914906064")
print(res)
