from tests.helpers import signup_and_login


def test_create_centre_requires_auth(client):
    resp = client.post("/centres", json={"name": "No Auth", "location": "Nowhere"})
    assert resp.status_code == 401


def test_create_and_get_centre(client):
    headers = signup_and_login(client)
    create_resp = client.post(
        "/centres",
        json={"name": "City Diagnostics", "location": "Indore"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    centre_id = create_resp.json()["id"]

    get_resp = client.get(f"/centres/{centre_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "City Diagnostics"
    assert get_resp.json()["tests"] == []


def test_get_nonexistent_centre_404(client):
    resp = client.get("/centres/99999")
    assert resp.status_code == 404


def test_add_test_to_centre(client):
    headers = signup_and_login(client)
    centre_resp = client.post(
        "/centres", json={"name": "Centre A", "location": "City A"}, headers=headers
    )
    centre_id = centre_resp.json()["id"]

    test_resp = client.post(
        f"/centres/{centre_id}/tests",
        json={"name": "CBC", "price": "499.00"},
        headers=headers,
    )
    assert test_resp.status_code == 201
    assert test_resp.json()["name"] == "CBC"


def test_add_test_to_nonexistent_centre_404(client):
    headers = signup_and_login(client)
    resp = client.post(
        "/centres/99999/tests", json={"name": "CBC", "price": "499.00"}, headers=headers
    )
    assert resp.status_code == 404


def test_list_centres_supports_location_filter(client):
    headers = signup_and_login(client)
    client.post(
        "/centres",
        json={"name": "Indore Centre", "location": "Indore"},
        headers=headers,
    )
    client.post(
        "/centres",
        json={"name": "Mumbai Centre", "location": "Mumbai"},
        headers=headers,
    )

    resp = client.get("/centres", params={"location": "Indore"})
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Indore Centre" in names
    assert "Mumbai Centre" not in names
