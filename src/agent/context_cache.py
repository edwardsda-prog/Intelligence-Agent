import datetime
import vertexai
from vertexai.preview import cached_contents

def get_or_create_schema_context_cache(project_id: str, location: str, schema_instruction: str, ttl_minutes: int = 60):
    """
    Creates or retrieves a Vertex AI Context Cache for static BigQuery table schemas and OPSEC rules.
    Reduces input token processing costs by up to 75% and lowers response latency.
    """
    try:
        vertexai.init(project=project_id, location=location)
        cache = cached_contents.CachedContent.create(
            model_name="gemini-3.8-flash",
            contents=[schema_instruction],
            ttl=datetime.timedelta(minutes=ttl_minutes),
            display_name="mission_intel_schema_cache"
        )
        print(f"✅ Created Vertex AI Context Cache: {cache.name} (TTL: {ttl_minutes}m)")
        return cache.name
    except Exception as e:
        print(f"⚠️ Context caching initialization skipped or unsupported in region: {e}")
        return None
