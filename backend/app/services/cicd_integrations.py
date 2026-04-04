from typing import Dict, Any, List
from ..schemas.analysis_schema import AnalysisRequest


def detect_cicd_platform(headers: Dict[str, str]) -> str:
    """Detect platform from headers (case-insensitive)."""
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    if "x-github-event" in headers_lower:
        return "github"
    if "x-gitlab-event" in headers_lower:
        return "gitlab"
    
    user_agent = headers_lower.get("user-agent", "")
    if "jenkins" in user_agent.lower():
        return "jenkins"
        
    return "generic"


def parse_github_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from GitHub push webhook."""
    repo = payload.get("repository", {})
    commits = payload.get("commits", [])
    
    repo_name = repo.get("full_name", payload.get("repository_name", "unknown/repo"))
    branch_name = payload.get("ref", "").replace("refs/heads/", "")
    commit_hash = payload.get("after", "")
    
    files_changed = set()
    commit_messages = []
    lines_added = 0
    lines_deleted = 0
    
    for commit in commits:
        commit_messages.append(commit.get("message", ""))
        for add in commit.get("added", []):
            files_changed.add(add)
            lines_added += 50  # approximation if lines aren't provided by the hook
        for mod in commit.get("modified", []):
            files_changed.add(mod)
            lines_added += 20
            lines_deleted += 10
        for rem in commit.get("removed", []):
            files_changed.add(rem)
            lines_deleted += 50

    return {
        "pipeline_source": "github",
        "repo_name": repo_name,
        "branch_name": branch_name,
        "commit_hash": commit_hash,
        "commit_count": len(commits),
        "files_changed": len(files_changed),
        "changed_files": list(files_changed),
        "commit_messages": commit_messages,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
    }


def parse_gitlab_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from GitLab push webhook."""
    repo = payload.get("project", {})
    commits = payload.get("commits", [])
    
    repo_name = repo.get("path_with_namespace", "unknown/repo")
    branch_name = payload.get("ref", "").replace("refs/heads/", "")
    commit_hash = payload.get("after", "")
    
    files_changed = set()
    commit_messages = []
    lines_added = 0
    lines_deleted = 0
    
    for commit in commits:
        commit_messages.append(commit.get("message", ""))
        for add in commit.get("added", []):
            files_changed.add(add)
            lines_added += 50
        for mod in commit.get("modified", []):
            files_changed.add(mod)
            lines_added += 20
            lines_deleted += 10
        for rem in commit.get("removed", []):
            files_changed.add(rem)
            lines_deleted += 50

    return {
        "pipeline_source": "gitlab",
        "repo_name": repo_name,
        "branch_name": branch_name,
        "commit_hash": commit_hash,
        "commit_count": len(commits),
        "files_changed": len(files_changed),
        "changed_files": list(files_changed),
        "commit_messages": commit_messages,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
    }


def parse_jenkins_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from Jenkins pipeline webhook."""
    # Custom structure usually defined in Jenkinsfile.
    return {
        "pipeline_source": "jenkins",
        "repo_name": payload.get("repository_name", "unknown/repo"),
        "branch_name": payload.get("branch_name", "main"),
        "commit_hash": payload.get("commit_hash", ""),
        "commit_count": payload.get("commit_count", 1),
        "files_changed": payload.get("files_changed", 0),
        "changed_files": payload.get("changed_files", []),
        "commit_messages": payload.get("commit_messages", []),
        "lines_added": payload.get("lines_added", 0),
        "lines_deleted": payload.get("lines_deleted", 0),
    }


def parse_generic_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from generic webhook."""
    return {
        "pipeline_source": "generic",
        "repo_name": payload.get("repository_name", "unknown/repo"),
        "branch_name": payload.get("branch_name", "main"),
        "commit_hash": payload.get("commit_hash", ""),
        "commit_count": payload.get("commit_count", 1),
        "files_changed": payload.get("files_changed", 0),
        "changed_files": payload.get("changed_files", []),
        "commit_messages": payload.get("commit_messages", []),
        "lines_added": payload.get("lines_added", 0),
        "lines_deleted": payload.get("lines_deleted", 0),
    }


def normalize_pipeline_payload(platform: str, payload: Dict[str, Any]) -> AnalysisRequest:
    """Normalize payload into AnalysisRequest model."""
    if platform == "github":
        data = parse_github_webhook(payload)
    elif platform == "gitlab":
        data = parse_gitlab_webhook(payload)
    elif platform == "jenkins":
        data = parse_jenkins_webhook(payload)
    else:
        data = parse_generic_webhook(payload)
        
    # Calculate synthetic inputs code_churn
    code_churn = data["lines_added"] + data["lines_deleted"]
    
    # Analyze commit messages for dependency updates
    dependency_updates = sum(1 for msg in data["commit_messages"] if "bump" in msg.lower() or "update" in msg.lower())

    # Safely mock missing historical tracking data usually collected via periodic sync jobs
    # Assuming baseline healthy values for these CI/CD triggers:
    test_coverage = float(payload.get("test_coverage", 90.0))
    historical_failures = int(payload.get("historical_failures", 0))
    deployment_frequency = int(payload.get("deployment_frequency", 5))
    deployment_environment = payload.get("deployment_environment", "staging")

    return AnalysisRequest(
        repo_name=data["repo_name"],
        commit_count=data["commit_count"],
        files_changed=data["files_changed"],
        code_churn=code_churn,
        test_coverage=test_coverage,
        dependency_updates=dependency_updates,
        historical_failures=historical_failures,
        deployment_frequency=deployment_frequency,
        changed_files=data["changed_files"],
        commit_messages=data["commit_messages"],
        lines_added=data["lines_added"],
        lines_deleted=data["lines_deleted"],
        pipeline_source=data["pipeline_source"],
        branch_name=data["branch_name"],
        commit_hash=data["commit_hash"],
        deployment_environment=deployment_environment
    )
