import logging

logger = logging.getLogger(__name__)


def fetch_commits(repo_name: str, branch: str = "main"):
    # This is a stub. Use PyGithub or httpx to fetch from GitHub API.
    return [{"id": "abc1234", "message": "fix: bug in login"}]


def fetch_pull_requests(repo_name: str):
    # This is a stub.
    return []


def analyze_pr_size(pr_id: int):
    # This is a stub.
    return {"files_changed": 5, "lines_added": 120}
