from pathlib import Path
import json
import os
from .logger import get_logger

logger = get_logger(__name__)

# Directory & File Paths

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
RAW_DIR = OUTPUT_DIR / "raw"
PROC_DIR = OUTPUT_DIR / "processed"
STATE_DIR = BASE_DIR / "state"
STATE_FILE = STATE_DIR / "checkpoints.json"

for path in [OUTPUT_DIR, RAW_DIR, PROC_DIR, STATE_DIR]:
    os.makedirs(path, exist_ok=True)

# Jira and Environment Configurations

JIRA_BASE = os.getenv("JIRA_BASE", "https://issues.apache.org/jira")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 50)) 
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 30))

# Checkpoint Management

class Config:
    """
    Manages configuration and checkpoint states for each project.
    Tracks requested limits, successful fetches, and current checkpoints.
    """

    CHECKPOINT_FILE = STATE_FILE

    def __init__(self):
        self.state = self._load_checkpoint_file()

    
    # File Handling
    def _load_checkpoint_file(self):
        if not os.path.exists(self.CHECKPOINT_FILE):
            logger.info("No existing checkpoint file found. Creating a new one.")
            return {}
        try:
            with open(self.CHECKPOINT_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Checkpoint file corrupted. Resetting...")
            return {}

    def _save_checkpoint_file(self):
        with open(self.CHECKPOINT_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    # Project State Management

    def init_project(self, project_key):
        """Initialize default tracking for a new project."""
        if project_key not in self.state:
            self.state[project_key] = {
                "last_successful": 0,
                "last_requested": 0,
                "current_checkpoint": 0
            }
            self._save_checkpoint_file()

    def get_project_state(self, project_key):
        """Retrieve checkpoint info for a project."""
        return self.state.get(project_key, {
            "last_successful": 0,
            "last_requested": 0,
            "current_checkpoint": 0
        })

    def update_state(self, project_key, last_successful=None, last_requested=None, current_checkpoint=None):
        """Update checkpoint values."""
        self.init_project(project_key)
        project_state = self.state[project_key]

        if last_successful is not None:
            project_state["last_successful"] = last_successful
        if last_requested is not None:
            project_state["last_requested"] = last_requested
        if current_checkpoint is not None:
            project_state["current_checkpoint"] = current_checkpoint

        self._save_checkpoint_file()
        logger.info(f"[{project_key}] Updated state → {project_state}")

    def reset_project(self, project_key):
        """Clear saved progress for a project."""
        if project_key in self.state:
            del self.state[project_key]
            self._save_checkpoint_file()
            logger.info(f"Reset checkpoint for {project_key}")

    def reset_all(self):
        """Clear all checkpoints."""
        self.state = {}
        self._save_checkpoint_file()
        logger.info("All checkpoints reset successfully.")

    # Consistency & Validation
    def needs_resume(self, project_key):
        """
        Checks if last run was incomplete.
        Returns True if last_successful < last_requested.
        """
        project_state = self.get_project_state(project_key)
        incomplete = project_state["last_successful"] < project_state["last_requested"]

        if incomplete:
            logger.warning(
                f"[{project_key}] Incomplete previous run detected. "
                f"Last successful: {project_state['last_successful']} / "
                f"Last requested: {project_state['last_requested']}"
            )
        else:
            logger.info(f"[{project_key}] All previous runs completed successfully.")

        return incomplete


# Simple Helper Methods

def load_checkpoint():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_checkpoint(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_project_checkpoint(project_key, last_requested, last_successful):
    data = load_checkpoint()
    data[project_key] = {
        "last_requested": last_requested,
        "last_successful": last_successful
    }
    save_checkpoint(data)

def get_project_checkpoint(project_key):
    data = load_checkpoint()
    return data.get(project_key, {"last_requested": 0, "last_successful": 0})
