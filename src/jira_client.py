import requests
import time
from .logger import get_logger
from .config import Config

logger = get_logger(__name__)

class JiraClient:
    """
    Jira REST API client to fetch issues from Apache's public Jira instance.
    Handles pagination, retries, and rate limits.
    """

    BASE_URL = "https://issues.apache.org/jira/rest/api/2"

    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    
    # Core Issue Fetching

    def search_issues(self, jql, start_at=0, max_results=50, project_key=None):
        """
        Fetches a batch of Jira issues from the specified project.
        Handles 429 and 5xx responses with retries.
        """

        url = f"{self.BASE_URL}/search" 

        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }

        attempt = 0
        while attempt < 5:
            try:
                response = self.session.get(url, params=params, timeout=15)

                if response.status_code == 429:
                    wait_time = int(response.headers.get("Retry-After", 10))
                    logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    attempt += 1
                    continue

                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}. Retry in 10s...")
                    time.sleep(10)
                    attempt += 1
                    continue

                response.raise_for_status()
                data = response.json() 
                return data.get("issues", [])

            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.error(f"Request failed (attempt {attempt}/5): {e}")
                time.sleep(5)

        logger.error(f"Failed to fetch issues for project {project_key} after 5 attempts.")
        return []
    
    def get_issue(self, issue_key):
        url = f"{self.BASE_URL}/issue/{issue_key}"
        res = self.session.get(url)
        if res.status_code == 200:
            return res.json()
        else:
            logger.error(f"Failed to fetch issue {issue_key}: {res.status_code} - {res.text}")
            return None


    # Single Issue Fetching (for checkpoint-based resume)

    def fetch_issue_by_index(self, project_key, index):
        """
        Fetch a single issue at the given index (used for checkpoint resume).
        Returns None if not found or request fails.
        """
        issues = self.fetch_issues(project_key, start_at=index, limit=1)
        if not issues:
            logger.warning(f"[{project_key}] No issue found at index {index}")
            return None
        return issues[0]

    # Utility

    def fetch_total_issues(self, project_key):
        """
        Returns total number of issues for a given project.
        """
        url = f"{self.BASE_URL}/search"
        params = {"jql": f"project={project_key}", "maxResults": 1}
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("total", 0)
        except Exception as e:
            logger.error(f"Failed to fetch total issue count for {project_key}: {e}")
            return 0
