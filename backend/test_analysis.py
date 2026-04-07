import asyncio
import json
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        req = {
            "repo_name": "user-service",
            "commit_count": 12,
            "files_changed": 5,
            "code_churn": 350,
            "test_coverage": 70,
            "dependency_updates": 3,
            "historical_failures": 4,
            "deployment_frequency": 3,
            "changed_files": ["src/auth.py", "tests/demo.py"]
        }
        res = await client.post("http://127.0.0.1:8000/api/analysis/analyze", json=req)
        print("Status", res.status_code)
        print(json.dumps(res.json(), indent=2))

asyncio.run(test())
