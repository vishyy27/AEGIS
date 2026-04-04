import httpx


async def fetch_github_repo_data(repo_name: str) -> dict:
    """
    Fetches real or mock deployment metrics from GitHub API.
    For production, this needs a valid GITHUB_TOKEN.
    """
    url = f"https://api.github.com/repos/{repo_name}/commits"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"per_page": 10},
                headers={"Accept": "application/vnd.github.v3+json"},
            )

            if response.status_code == 200:
                commits = response.json()
                commit_count = len(commits)
                # Mocking computation of churn/files based on commits for now
                files_changed = commit_count * 3
                code_churn = commit_count * 45
            else:
                commit_count = 5
                files_changed = 15
                code_churn = 120

    except httpx.RequestError:
        # Fallback values if network fails
        commit_count = 5
        files_changed = 15
        code_churn = 120

    return {
        "repo_name": repo_name,
        "commit_count": commit_count,
        "files_changed": files_changed,
        "code_churn": code_churn,
        "test_coverage": 78.5,  # Mock CI metric
        "dependency_updates": 2,  # Mock
        "historical_failures": 1,  # Mock DB lookup
        "deployment_frequency": 4,  # Mock
    }
