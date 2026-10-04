import os
import sys

os.environ["PROJECT_ID"] = "antig-dave"
os.environ["GOOGLE_CLOUD_PROJECT"] = "antig-dave"

from src.agent.agent import root_agent
from google.adk.runner import Runner
from google.adk.sessions import InMemorySessionService

query = "A2A_QUERY: Output the exact MGRS format coordinates for radar tracks TRK-901 and TRK-903."

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

session = session_service.create_session(app_name="test", user_id="test_user")

print("Running query locally with Runner...")
try:
    events = list(runner.run(session_id=session.session_id, input=query))
    print("DONE")
except Exception as e:
    import traceback
    traceback.print_exc()

