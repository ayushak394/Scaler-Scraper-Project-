from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
RAW_DIR = OUTPUT_DIR / "raw"
PROC_DIR = OUTPUT_DIR / "processed"
STATE_FILE = BASE_DIR / "state" / "checkpoints.json"

# Jira base URL (Apache public JIRA)
JIRA_BASE = os.getenv("JIRA_BASE", "https://issues.apache.org/jira")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 50))   # Jira maxResults per call (<=100 typically)
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 30))
