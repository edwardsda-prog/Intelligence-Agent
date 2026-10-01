import os
import json
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

MY_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
ADK_DATA_DIR = os.path.join(MY_AGENT_DIR, ".adk")
MEMORY_BANK_FILE = os.path.join(ADK_DATA_DIR, "memory_bank.json")

class GroupMemoryProfile(BaseModel):
    """Durable group profile persisted in Agent Platform Memory Bank."""
    group_id: str = Field(default="intelligence_analysts", description="Group identifier")
    group_name: str = Field(default="UK Joint Command Intelligence Analysts", description="Human-readable group title")
    primary_threat_domains: list[str] = Field(default_factory=lambda: ["EW", "AIR_DEFENSE"], description="Active watch threat domains")
    default_classification: str = Field(default="UK EYES ONLY", description="Default security classification caveat")
    preferred_coordinates: str = Field(default="MGRS", description="Geospatial coordinate preference")
    active_watchlist_targets: list[str] = Field(default_factory=lambda: ["TEL-ALPHA-7", "RADAR-BRAVO-3"], description="Tracked target IDs")
    last_updated: float = Field(default_factory=time.time, description="Unix timestamp of last profile mutation")

class MissionTransactionState(BaseModel):
    """Request-scoped shared blackboard state passed across workflow graph nodes."""
    user_query: str = ""
    group_id: str = "intelligence_analysts"
    classified_intent: Optional[str] = None
    retrieved_telemetry: Optional[dict] = None
    retrieved_humint: Optional[list] = None
    model_armor_sanitized_output: Optional[str] = None
    execution_status: str = "INITIALIZED"

class MemoryServiceClient:
    """Client for managing Tier 3 Long-Term Memory (Memory Bank) profiles."""

    def __init__(self, storage_file: str = MEMORY_BANK_FILE):
        self.storage_file = storage_file
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        if not os.path.exists(self.storage_file):
            self._initialize_default_store()

    def _initialize_default_store(self):
        default_data = {
            "intelligence_analysts": GroupMemoryProfile(
                group_id="intelligence_analysts",
                group_name="UK Joint Command Intelligence Analysts",
                primary_threat_domains=["EW", "AIR_DEFENSE"],
                default_classification="UK EYES ONLY",
                preferred_coordinates="MGRS",
                active_watchlist_targets=["TEL-ALPHA-7", "RADAR-BRAVO-3"]
            ).model_dump()
        }
        with open(self.storage_file, "w") as f:
            json.dump(default_data, f, indent=2)

    def get_group_profile(self, group_id: str = "intelligence_analysts") -> GroupMemoryProfile:
        """Retrieves Tier 3 Group LTM Profile."""
        try:
            with open(self.storage_file, "r") as f:
                data = json.load(f)
            if group_id in data:
                return GroupMemoryProfile(**data[group_id])
        except Exception:
            pass
        return GroupMemoryProfile(group_id=group_id)

    def update_group_profile(self, group_id: str, updates: dict[str, Any]) -> GroupMemoryProfile:
        """Asynchronously updates persistent Tier 3 Group LTM Profile in Memory Bank."""
        profile = self.get_group_profile(group_id)
        current_data = profile.model_dump()
        current_data.update(updates)
        current_data["last_updated"] = time.time()
        
        updated_profile = GroupMemoryProfile(**current_data)
        
        try:
            with open(self.storage_file, "r") as f:
                store = json.load(f)
        except Exception:
            store = {}
            
        store[group_id] = updated_profile.model_dump()
        
        with open(self.storage_file, "w") as f:
            json.dump(store, f, indent=2)
            
        return updated_profile

    def save_group_profile(self, profile: GroupMemoryProfile) -> GroupMemoryProfile:
        """Saves a GroupMemoryProfile instance to persistent storage."""
        return self.update_group_profile(profile.group_id, profile.model_dump())


