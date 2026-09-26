from datetime import datetime, timedelta

from tests.helpers import signup_and_login, create_centre_and_test


def future_time(days=10):
    return (datetime.now() + timedelta(days=days)).isoformat()


def test_create_booking_requires_auth(client):
    resp = client.post(
        "/bookings",
        json={"test_id": 1, "centre_id": 1, "appointment_time": future_time()},
    )
    assert resp.status_code == 401


def test_create_booking_success(client):
    headers = signup_and_login(client)
    centre_id, test_id = create_centre_and_test(client, headers, price="500.00")

    resp = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": future_time(),
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PENDING"
    assert body["amount"] == "500.00"


def test_create_booking_past_time_rejected(client):
    headers = signup_and_login(client)
    centre_id, test_id = create_centre_and_test(client, headers)

    resp = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": "2020-01-01T10:00:00",
        },
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_booking_mismatched_test_centre_rejected(client):
    headers = signup_and_login(client)
    _, test_id = create_centre_and_test(client, headers)
    other_centre_resp = client.post(
        "/centres",
        json={"name": "Other Centre", "location": "Elsewhere"},
        headers=headers,
    )
    other_centre_id = other_centre_resp.json()["id"]

    resp = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": other_centre_id,
            "appointment_time": future_time(),
        },
        headers=headers,
    )
    assert resp.status_code == 400


def test_duplicate_booking_rejected(client):
    headers = signup_and_login(client)
    centre_id, test_id = create_centre_and_test(client, headers)
    slot = future_time()

    payload = {"test_id": test_id, "centre_id": centre_id, "appointment_time": slot}
    first = client.post("/bookings", json=payload, headers=headers)
    second = client.post("/bookings", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409


def test_user_cannot_view_others_booking(client):
    headers_a = signup_and_login(client, email="a@example.com")
    headers_b = signup_and_login(client, email="b@example.com")
    centre_id, test_id = create_centre_and_test(client, headers_a)

    booking_resp = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": future_time(),
        },
        headers=headers_a,
    )
    booking_id = booking_resp.json()["id"]

    resp = client.get(f"/bookings/{booking_id}", headers=headers_b)
    assert resp.status_code == 403


def test_cancel_booking_and_double_cancel_rejected(client):
    headers = signup_and_login(client)
    centre_id, test_id = create_centre_and_test(client, headers)

    booking_resp = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": future_time(),
        },
        headers=headers,
    )
    booking_id = booking_resp.json()["id"]

    first_cancel = client.post(f"/bookings/{booking_id}/cancel", headers=headers)
    assert first_cancel.status_code == 200
    assert first_cancel.json()["status"] == "CANCELLED"

    second_cancel = client.post(f"/bookings/{booking_id}/cancel", headers=headers)
    assert second_cancel.status_code == 400
