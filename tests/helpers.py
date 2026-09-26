def signup_and_login(client, email="user@example.com", password="testpass123"):
    client.post(
        "/auth/signup",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    resp = client.post("/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_centre_and_test(client, headers, price="500.00"):
    centre_resp = client.post(
        "/centres",
        json={"name": "Test Centre", "location": "Test City"},
        headers=headers,
    )
    centre_id = centre_resp.json()["id"]

    test_resp = client.post(
        f"/centres/{centre_id}/tests",
        json={"name": "Sample Test", "price": price},
        headers=headers,
    )
    test_id = test_resp.json()["id"]

    return centre_id, test_id
