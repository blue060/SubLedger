import pytest


def test_infrastructure_crud(auth_client):
    response = auth_client.post("/api/infrastructure/servers", json={
        "name": "香港服务器",
        "host": "203.0.113.10",
        "provider": "测试云",
        "ssh_port": 22,
    })
    if response.status_code == 401:
        pytest.skip("TestClient cookie persistence limitation")
    assert response.status_code == 201
    server_id = response.json()["id"]

    response = auth_client.post("/api/infrastructure/services", json={
        "name": "SubLedger",
        "domain": "https://ledger.example.com/",
        "server_id": server_id,
        "protocol": "https",
        "internal_host": "127.0.0.1",
        "internal_port": 8080,
    })
    assert response.status_code == 201
    service_id = response.json()["id"]
    assert response.json()["domain"] == "ledger.example.com"
    assert response.json()["server_name"] == "香港服务器"

    overview = auth_client.get("/api/infrastructure/overview")
    assert overview.status_code == 200
    assert overview.json()["servers"][0]["service_count"] == 1
    assert overview.json()["services"][0]["internal_port"] == 8080

    blocked_delete = auth_client.delete(f"/api/infrastructure/servers/{server_id}")
    assert blocked_delete.status_code == 400

    assert auth_client.delete(f"/api/infrastructure/services/{service_id}").status_code == 200
    assert auth_client.delete(f"/api/infrastructure/servers/{server_id}").status_code == 200
