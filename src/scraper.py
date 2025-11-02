# src/scraper.py
import json
import argparse
from pathlib import Path
from tqdm import tqdm
from .config import RAW_DIR, STATE_FILE
from .jira_client import JiraClient
from .logger import get_logger
from .utils import atomic_write, load_state, save_state

logger = get_logger(__name__)

# ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


class Scraper:
    """
    Scraper with robust checkpointing that:
     - keeps per-project 'start_at', 'pending', 'total_fetched', 'last_status'
     - when user passes --limit N, N is added to pending for that project
     - always tries to clear pending (i.e., outstanding requested items) first
     - saves state after each successful issue saved (atomic)
    """

    def __init__(self, projects, max_issues=None, batch_size=None):
        self.projects = projects
        self.max_issues = max_issues
        self.batch_size = batch_size
        self.client = JiraClient()
        self.state = load_state(STATE_FILE)

    # checkpoint helpers
    def _ensure_project_state(self, project: str) -> None:
        if project not in self.state or not isinstance(self.state[project], dict):
            self.state[project] = {
                "start_at": 0,
                "pending": 0,
                "total_fetched": 0,
                "last_status": "unknown"
            }

    def _save_state(self) -> None:
        save_state(STATE_FILE, self.state)

    # raw save helper
    def _save_raw_issue(self, project: str, issue_key: str, data: dict) -> None:
        proj_dir = RAW_DIR / project
        proj_dir.mkdir(parents=True, exist_ok=True)
        target = proj_dir / f"{issue_key}.json"
        atomic_write(target, json.dumps(data, ensure_ascii=False))

    # main logic
    def run_project(self, project: str, add_pending: int = 0):
        """
        Runs fetch for a single project.

        add_pending: how many NEW records the user asked for in this run
                     (this number will be *added* to the project's pending counter)
        """
        logger.info("Starting project %s", project)
        self._ensure_project_state(project)

        if add_pending and isinstance(add_pending, int) and add_pending > 0:
            self.state[project]["pending"] = int(self.state[project].get("pending", 0)) + int(add_pending)
            logger.info("Added %d pending for %s (now pending=%d)", add_pending, project, self.state[project]["pending"])
            self._save_state()

        start_at = int(self.state[project].get("start_at", 0))
        pending = int(self.state[project].get("pending", 0))
        total_fetched = int(self.state[project].get("total_fetched", 0))
        jql = f'project = {project} ORDER BY created ASC'

        unlimited_mode = (pending == 0 and (self.max_issues is None))

        try:
            while True:
                if not unlimited_mode:
                    effective_batch = min(self.batch_size, pending) if pending > 0 else 0
                    if self.max_issues:
                        left = self.max_issues - total_fetched if not pending else pending
                        if left <= 0:
                            logger.info("Legacy max_issues reached for %s", project)
                            break
                        effective_batch = min(effective_batch or self.batch_size, max(1, left))
                else:
                    effective_batch = self.batch_size

                if not unlimited_mode and pending == 0:
                    logger.info("No pending items for %s — done for this run.", project)
                    break

                logger.info("Fetching %s startAt=%d (batch=%d) pending=%d total_fetched=%d", project, start_at, effective_batch, pending, total_fetched)
                res = self.client.search_issues(jql, start_at=start_at, max_results=effective_batch, project_key=project)
                issues = res if isinstance(res, list) else res.get("issues", [])

                if not issues:
                    logger.info("API returned no issues for %s (startAt=%d). End of issues.", project, start_at)
                    break

                to_process = issues
                if not unlimited_mode and pending > 0:
                    to_process = issues[:pending]

                for issue_meta in to_process:
                    key = issue_meta.get("key")
                    if not key:
                        start_at += 1
                        continue

                    target_file = RAW_DIR / project / f"{key}.json"
                    if target_file.exists():
                        logger.debug("Skipping existing issue file %s", target_file)
                        start_at += 1
                        if pending > 0:
                            pending -= 1
                        continue

                    try:
                        full = self.client.get_issue(key)
                        self._save_raw_issue(project, key, full)
                        start_at += 1
                        total_fetched += 1
                        if pending > 0:
                            pending -= 1
                        self.state[project]["start_at"] = start_at
                        self.state[project]["pending"] = pending
                        self.state[project]["total_fetched"] = total_fetched
                        self.state[project]["last_status"] = "running"
                        self._save_state()
                    except Exception as e:
                        logger.error("Failed to fetch full issue %s for %s: %s", key, project, e)
                        self.state[project]["start_at"] = start_at
                        self.state[project]["pending"] = pending
                        self.state[project]["total_fetched"] = total_fetched
                        self.state[project]["last_status"] = "failed"
                        self._save_state()
                        raise  


                self.state[project]["start_at"] = start_at
                self.state[project]["pending"] = pending
                self.state[project]["total_fetched"] = total_fetched
                self.state[project]["last_status"] = "running"
                self._save_state()

                if not unlimited_mode and pending == 0:
                    logger.info("Cleared pending for %s (fetched this run).", project)
                    break

                if len(issues) < effective_batch:
                    logger.info("API returned fewer items than requested; end reached for %s", project)
                    break


            # Completed fetching loop for project
            # set last_status success
            self.state[project]["last_status"] = "success"
            self.state[project]["start_at"] = start_at
            self.state[project]["pending"] = pending
            self.state[project]["total_fetched"] = total_fetched
            self._save_state()

            logger.info("Finished project %s (total_fetched=%s pending=%s start_at=%s)", project, total_fetched, pending, start_at)

        except Exception as e:
            logger.exception("Error while running project %s: %s", project, e)
            self.state[project]["start_at"] = start_at
            self.state[project]["pending"] = pending
            self.state[project]["total_fetched"] = total_fetched
            self.state[project]["last_status"] = "failed"
            self._save_state()

    def run(self, add_pending_per_project: dict = None):
        """
        Run the scraper for self.projects.
        add_pending_per_project: optional dict { project_key: add_pending_int }
        """
        add_pending_per_project = add_pending_per_project or {}
        for project in self.projects:
            add = int(add_pending_per_project.get(project, 0)) if project in add_pending_per_project else 0
            self.run_project(project, add_pending=add)