# import time
# from urllib.parse import urljoin
# import requests
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry
# from .config import JIRA_BASE, REQUEST_TIMEOUT
# from .logger import get_logger

# logger = get_logger(__name__)

# class JiraClient:
#     def __init__(self):
#         self.session = requests.Session()
#         retry_strategy = Retry(
#             total=3,
#             status_forcelist=[500, 502, 503, 504],
#             allowed_methods=["GET", "POST"],
#             backoff_factor=0.5,
#             raise_on_status=False
#         )
#         adapter = HTTPAdapter(max_retries=retry_strategy)
#         self.session.mount("https://", adapter)
#         self.session.mount("http://", adapter)

#     def _get(self, path, params=None):
#         url = JIRA_BASE.rstrip("/") + "/" + path.lstrip("/")
#         print("DEBUG: Fetching from", url)
#         tries = 0
#         while True:
#             tries += 1
#             try:
#                 r = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
#             except requests.RequestException as e:
#                 logger.warning("Request error %s on %s (try %d)", e, url, tries)
#                 if tries >= 5:
#                     raise
#                 time.sleep(2 ** tries)
#                 continue

#             if r.status_code == 429:
#                 retry_after = r.headers.get("Retry-After")
#                 try:
#                     wait = int(retry_after) if retry_after and retry_after.isdigit() else (2 ** tries)
#                 except Exception:
#                     wait = (2 ** tries)
#                 logger.warning("429 Too Many Requests. Waiting %s seconds (try %d)", wait, tries)
#                 time.sleep(wait)
#                 if tries >= 8:
#                     r.raise_for_status()
#                 continue

#             if 500 <= r.status_code < 600:
#                 logger.warning("Server error %d on %s (try %d)", r.status_code, url, tries)
#                 if tries >= 5:
#                     r.raise_for_status()
#                 time.sleep(2 ** tries)
#                 continue

#             if not r.ok:
#                 # other non-200s (4xx)
#                 logger.error("HTTP error %d: %s", r.status_code, r.text[:400])
#                 r.raise_for_status()

#             try:
#                 return r.json()
#             except ValueError:
#                 logger.error("Failed to parse JSON from %s", url)
#                 raise

#     def search_issues(self, jql, start_at=0, max_results=50):
#         path = "rest/api/2/search"
#         params = {"jql": jql, "startAt": start_at, "maxResults": max_results}
#         return self._get(path, params=params)

#     def get_issue(self, issue_key, fields="*all"):
#         path = f"rest/api/2/issue/{issue_key}"
#         params = {"fields": fields}
#         return self._get(path, params=params)

import time
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import JIRA_BASE, REQUEST_TIMEOUT
from .logger import get_logger

logger = get_logger(__name__)


class JiraClient:
    """Minimal JIRA REST API client with retries and backoff."""

    def __init__(self):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            backoff_factor=0.5,
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get(self, path, params=None):
        """Generic GET request with retry and exponential backoff."""
        url = urljoin(JIRA_BASE.rstrip("/") + "/", path.lstrip("/"))
        tries = 0

        while True:
            tries += 1
            try:
                r = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            except requests.RequestException as e:
                logger.warning("Request error %s on %s (try %d)", e, url, tries)
                if tries >= 5:
                    raise
                time.sleep(min(2 ** tries, 60))
                continue

            # Handle rate-limiting
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                try:
                    wait = int(retry_after) if retry_after and retry_after.isdigit() else min(2 ** tries, 60)
                except Exception:
                    wait = min(2 ** tries, 60)
                logger.warning("429 Too Many Requests. Waiting %s seconds (try %d)", wait, tries)
                time.sleep(wait)
                if tries >= 8:
                    r.raise_for_status()
                continue

            # Retry on transient server errors
            if 500 <= r.status_code < 600:
                logger.warning("Server error %d on %s (try %d)", r.status_code, url, tries)
                if tries >= 5:
                    r.raise_for_status()
                time.sleep(min(2 ** tries, 60))
                continue

            # Handle other HTTP errors
            if not r.ok:
                logger.error("HTTP error %d: %s", r.status_code, r.text[:400])
                r.raise_for_status()

            # Try parsing JSON
            try:
                return r.json()
            except ValueError:
                logger.error("Failed to parse JSON from %s (response snippet: %s)", url, r.text[:300])
                if tries >= 3:
                    raise
                time.sleep(min(2 ** tries, 30))

    def search_issues(self, jql, start_at=0, max_results=50):
        """Search issues in JIRA using JQL query."""
        path = "rest/api/2/search"
        params = {"jql": jql, "startAt": start_at, "maxResults": max_results}
        return self._get(path, params=params)

    def get_issue(self, issue_key, fields="*all"):
        """Fetch full issue details by key."""
        path = f"rest/api/2/issue/{issue_key}"
        params = {"fields": fields}
        return self._get(path, params=params)
