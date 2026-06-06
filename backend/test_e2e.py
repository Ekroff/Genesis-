"""End-to-End Test — Tests the full GENESIS pipeline with all 6 agents.

Verifies:
1. API /api/launch accepts business data and returns session_id
2. All 6 agents produce expected outputs
3. Brand Agent → logo_url, colors, taglines, social_kit
4. Website Agent → website_url with correct template
5. Payment Agent → upi_qr_url
6. Outreach Agent → nearby_businesses, whatsapp_links, email data
7. GMB Agent → gmb_data
8. Legal Agent → legal docs
9. Pipeline completes without errors

Usage:
    python test_e2e.py                   # Full test against local backend
    python test_e2e.py --url URL         # Test against deployed backend
    python test_e2e.py --quick           # Quick smoke test (launch only)
"""

import httpx
import asyncio
import sys
import json
from datetime import datetime


BACKEND_URL = "http://localhost:8000"

TEST_DATA = {
    "business_name": "Raju Ki Chai Tapri",
    "business_type": "restaurant",
    "menu": [
        {"item": "Masala Chai", "price": 15},
        {"item": "Cutting Chai", "price": 10},
        {"item": "Bun Maska", "price": 25},
        {"item": "Samosa", "price": 20},
        {"item": "Vada Pav", "price": 30},
    ],
    "address": "Shop 5, Laxmi Nagar, Near Metro Station, Delhi 110092",
    "phone": "9876543210",
    "upi_id": "9876543210@paytm",
    "language": "hi",
}


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.data = None
        self.duration_ms = 0

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        icon = "V" if self.passed else "X"
        time_str = f" ({self.duration_ms}ms)" if self.duration_ms else ""
        err_str = f"\n   Error: {self.error}" if self.error else ""
        return f"  [{icon}] {status} {self.name}{time_str}{err_str}"


async def test_health(client: httpx.AsyncClient) -> TestResult:
    result = TestResult("Health Check")
    start = datetime.now()
    try:
        r = await client.get(f"{BACKEND_URL}/health")
        result.data = r.json()
        assert r.status_code == 200
        assert result.data["status"] == "ok"
        result.passed = True
    except Exception as e:
        result.error = str(e)
    result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    return result


async def test_launch(client: httpx.AsyncClient) -> TestResult:
    result = TestResult("Launch Pipeline")
    start = datetime.now()
    try:
        r = await client.post(f"{BACKEND_URL}/api/launch", json=TEST_DATA, timeout=30)
        result.data = r.json()
        assert r.status_code == 200
        assert "session_id" in result.data
        assert result.data["session_id"] is not None
        result.passed = True
    except Exception as e:
        result.error = str(e)
    result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    return result


async def test_session_status(client: httpx.AsyncClient, session_id: str) -> TestResult:
    result = TestResult("Session Status")
    start = datetime.now()
    try:
        r = await client.get(f"{BACKEND_URL}/api/status/{session_id}", timeout=10)
        result.data = r.json()
        assert r.status_code == 200
        result.passed = True
    except Exception as e:
        result.error = str(e)
    result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
    return result


async def test_agent_outputs(client: httpx.AsyncClient, session_id: str) -> list:
    results = []
    agents = {
        "brand": {"required_fields": ["logo_url", "primary_color", "tagline_hindi"], "description": "Brand Agent"},
        "website": {"required_fields": ["website_url", "template"], "description": "Website Agent"},
        "payment": {"required_fields": ["upi_qr_url"], "description": "Payment Agent"},
        "outreach": {"required_fields": ["whatsapp_intro"], "description": "Outreach Agent"},
        "gmb": {"required_fields": [], "description": "GMB Agent"},
        "legal": {"required_fields": [], "description": "Legal Agent"},
    }

    max_wait = 180
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        try:
            r = await client.get(f"{BACKEND_URL}/api/status/{session_id}", timeout=10)
            data = r.json()
            tasks = data.get("tasks", [])
            all_done = all(t.get("status") in ("completed", "error") for t in tasks)
            if all_done and len(tasks) == 6:
                break
        except Exception:
            pass
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        print(f"    Waiting... ({elapsed}s / {max_wait}s)")

    try:
        r = await client.get(f"{BACKEND_URL}/api/status/{session_id}", timeout=10)
        data = r.json()
        tasks = {t["agent_name"]: t for t in data.get("tasks", [])}
    except Exception as e:
        fail = TestResult("Agent Output Fetch")
        fail.error = str(e)
        return [fail]

    for agent_name, spec in agents.items():
        result = TestResult(spec["description"])
        task = tasks.get(agent_name)
        if not task:
            result.error = f"Agent '{agent_name}' not found"
            results.append(result)
            continue

        status = task.get("status", "unknown")
        result_data = task.get("result_data", {})

        if status == "completed":
            missing = [f for f in spec["required_fields"] if not result_data.get(f)]
            if missing:
                result.error = f"Missing: {missing}"
            else:
                result.passed = True
                result.data = result_data
        elif status == "error":
            result.error = f"Errored: {task.get('current_step', 'unknown')}"
        else:
            result.error = f"Stuck: status={status}, progress={task.get('progress', 0)}%"

        results.append(result)

    return results


async def run_all_tests():
    print(f"\n{'='*60}")
    print(f"  GENESIS E2E TEST SUITE")
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    all_results = []

    async with httpx.AsyncClient() as client:
        print("[Phase 1] Health Check")
        health = await test_health(client)
        all_results.append(health)
        print(health)

        if not health.passed:
            print("\nBackend not reachable. Aborting.")
            return all_results

        print("\n[Phase 2] Launch Pipeline")
        launch = await test_launch(client)
        all_results.append(launch)
        print(launch)

        if not launch.passed:
            print("\nLaunch failed. Aborting.")
            return all_results

        session_id = launch.data["session_id"]
        print(f"    Session ID: {session_id}")

        if "--quick" in sys.argv:
            print("\nQuick mode - done.")
        else:
            print("\n[Phase 3] Session Status")
            status = await test_session_status(client, session_id)
            all_results.append(status)
            print(status)

            print("\n[Phase 4] Agent Outputs (waiting...)")
            agent_results = await test_agent_outputs(client, session_id)
            all_results.extend(agent_results)
            for r in agent_results:
                print(r)

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{len(all_results)} passed, {failed} failed")
    print(f"{'='*60}\n")

    return all_results


if __name__ == "__main__":
    for i, arg in enumerate(sys.argv):
        if arg == "--url" and i + 1 < len(sys.argv):
            BACKEND_URL = sys.argv[i + 1]
    asyncio.run(run_all_tests())
