from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tools_endpoint() -> None:
    response = client.get("/tools")
    assert response.status_code == 200
    assert any(tool["name"] == "echo" for tool in response.json())


def test_create_and_run_agent() -> None:
    agent = {
        "id": "api-demo-agent",
        "name": "API Demo Agent",
        "description": "Phase 1 smoke agent",
        "steps": [{"id": "echo-step", "tool": "echo"}],
    }
    response = client.post("/agents", json=agent)
    assert response.status_code == 200

    response = client.post("/agents/api-demo-agent/run", json={"request": "echo", "inputs": {"value": 7}})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"

    events = client.get(f"/runs/{body['id']}/events")
    assert events.status_code == 200
    assert any(event["status"] == "completed" for event in events.json())
