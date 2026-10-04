from src.agent.agent import apply_model_armor
class DummyContext:
    pass
class DummyResponse:
    class Content:
        class Part:
            text = "Testing MGRS 30UGC9914906064"
        parts = [Part()]
    content = Content()

# Test
print(apply_model_armor(DummyContext(), DummyResponse()))
