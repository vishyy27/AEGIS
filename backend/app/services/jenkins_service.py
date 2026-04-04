# Jenkins Stub
def fetch_build_status(job_name: str, build_id: str):
    return {"status": "SUCCESS"}


def get_recent_builds(job_name: str):
    return []
