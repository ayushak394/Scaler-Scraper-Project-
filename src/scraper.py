
import json
import argparse
from pathlib import Path
from tqdm import tqdm
from .config import RAW_DIR, STATE_FILE
from .jira_client import JiraClient
from .logger import get_logger
from .utils import atomic_write

logger = get_logger(__name__)

RAW_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


class Scraper:
    def __init__(self, projects, max_issues=50, batch_size=50):
        """
        Initialize the scraper with configurable project list, limit, and batch size.
        """
        self.projects = projects
        self.max_issues = max_issues  # Limit total issues per project
        self.batch_size = batch_size  # Batch size per fetch
        self.client = JiraClient()
        self.state = self._load_state()

    def _load_state(self):
        """Load scraper progress state from disk."""
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Malformed checkpoints.json")
                return data
            except Exception as e:
                logger.warning("Failed to load state file (%s). Starting fresh.", e)
                return {}
        return {}

    def _save_state(self):
        """Safely write current scraper state."""
        atomic_write(STATE_FILE, json.dumps(self.state, indent=2, ensure_ascii=False))

    def _save_raw(self, project, issue_key, data):
        """Write one issue’s full JSON data."""
        proj_dir = RAW_DIR / project
        proj_dir.mkdir(parents=True, exist_ok=True)
        target = proj_dir / f"{issue_key}.json"
        atomic_write(target, json.dumps(data, ensure_ascii=False))

    def run_project(self, project):
        """Download all issues for one project with resume and limit support."""
        logger.info("Starting project %s", project)
        jql = f'project = {project} ORDER BY created ASC'
        start_at = int(self.state.get(project, 0))
        fetched_total = 0  # Track total fetched per project

        while True:
            # Stop if user-defined limit reached
            if self.max_issues and fetched_total >= self.max_issues:
                logger.info("Reached issue limit (%d) for %s", self.max_issues, project)
                break

            logger.info("Fetching %s startAt=%d", project, start_at)
            try:
                res = self.client.search_issues(
                    jql, start_at=start_at, max_results=self.batch_size
                )
            except Exception as e:
                logger.error("Failed to fetch batch for %s (startAt=%d): %s", project, start_at, e)
                break

            issues = res.get("issues", [])
            if not issues:
                logger.info("No more issues for %s (startAt=%d)", project, start_at)
                break
            remaining = (
            self.max_issues - fetched_total
            if self.max_issues
            else len(issues)
            )
            for issue_meta in tqdm(
                issues[:remaining],
                desc=f"{project} issues",
                unit="issue",
                total=min(len(issues), remaining)
            ):
                key = issue_meta.get("key")
                if not key:
                    continue
                try:
                    full = self.client.get_issue(key)
                    self._save_raw(project, key, full)
                    fetched_total += 1

                    # Stop early if reached limit mid-batch
                    if self.max_issues and fetched_total >= self.max_issues:
                        logger.info("Reached issue limit (%d) for %s", self.max_issues, project)
                        break
                except Exception as e:
                    logger.error("Failed to fetch issue %s: %s", key, e)
                    continue
            else:
                # Executed only if the inner for loop did NOT break
                start_at += len(issues)
                self.state[project] = start_at
                self._save_state()

                if len(issues) < self.batch_size:
                    logger.info("End of issues for %s.", project)
                    break
                continue  # Continue fetching next batch

            # Inner for loop broke (limit reached)
            break

        # ✅ Always save checkpoint after finishing project
        self.state[project] = start_at + fetched_total

        self._save_state()

        logger.info("Finished project %s (total fetched=%s)", project, fetched_total)

    def run(self):
        """Run all configured projects."""
        for project in self.projects:
            self.run_project(project)


# --- CLI entrypoint ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apache Jira Scraper")
    parser.add_argument(
        "--projects",
        nargs="+",
        default=["HADOOP", "HIVE", "SPARK"],
        help="List of Apache Jira project keys to scrape",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of issues to fetch per project (optional)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of issues to fetch per API call (default: 50)",
    )
    args = parser.parse_args()

    scraper = Scraper(args.projects, max_issues=args.limit, batch_size=args.batch_size)
    scraper.run()
