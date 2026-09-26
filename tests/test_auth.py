def test_signup_success(client):
    resp = client.post(
        "/auth/signup",
        json={
            "email": "new@example.com",
            "password": "securepass1",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_signup_duplicate_email_rejected(client):
    client.post(
        "/auth/signup", json={"email": "dup@example.com", "password": "securepass1"}
    )
    resp = client.post(
        "/auth/signup", json={"email": "dup@example.com", "password": "anotherpass"}
    )
    assert resp.status_code == 400


def test_signup_invalid_email_rejected(client):
    resp = client.post(
        "/auth/signup", json={"email": "not-an-email", "password": "securepass1"}
    )
    assert resp.status_code == 422


def test_login_success(client):
    client.post(
        "/auth/signup", json={"email": "login@example.com", "password": "securepass1"}
    )
    resp = client.post(
        "/auth/login", json={"email": "login@example.com", "password": "securepass1"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/signup",
        json={"email": "wrongpass@example.com", "password": "securepass1"},
    )
    resp = client.post(
        "/auth/login", json={"email": "wrongpass@example.com", "password": "nope"}
    )
    assert resp.status_code == 401


def test_login_nonexistent_user_rejected(client):
    resp = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "whatever"}
    )
    assert resp.status_code == 401
