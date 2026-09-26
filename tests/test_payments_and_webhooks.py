from datetime import datetime, timedelta

from tests.helpers import signup_and_login, create_centre_and_test


def future_time(days=10):
    return (datetime.now() + timedelta(days=days)).isoformat()


def _create_pending_booking(client, headers):
    centre_id, test_id = create_centre_and_test(client, headers)
    resp = client.post(
        "/bookings",
        json={
            "test_id": test_id,
            "centre_id": centre_id,
            "appointment_time": future_time(),
        },
        headers=headers,
    )
    return resp.json()["id"]


def test_payment_updates_booking_status(client):
    headers = signup_and_login(client)
    booking_id = _create_pending_booking(client, headers)

    resp = client.post("/payments", json={"booking_id": booking_id}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["status"] in ("SUCCESS", "FAILED")

    booking_resp = client.get(f"/bookings/{booking_id}", headers=headers)
    assert booking_resp.json()["status"] in ("CONFIRMED", "FAILED")


def test_cannot_pay_for_confirmed_booking_twice(client, monkeypatch):
    import app.services.payment_simulator as sim

    monkeypatch.setattr(
        sim,
        "simulate_payment_result",
        lambda success_rate=0.8: sim.PaymentStatus.SUCCESS,
    )

    headers = signup_and_login(client)
    booking_id = _create_pending_booking(client, headers)

    first = client.post("/payments", json={"booking_id": booking_id}, headers=headers)
    assert first.status_code == 201
    assert first.json()["status"] == "SUCCESS"

    second = client.post("/payments", json={"booking_id": booking_id}, headers=headers)
    assert second.status_code == 400


def test_webhook_confirms_booking(client, monkeypatch):
    import app.services.payment_simulator as sim

    monkeypatch.setattr(
        sim,
        "simulate_payment_result",
        lambda success_rate=0.8: sim.PaymentStatus.FAILED,
    )

    headers = signup_and_login(client)
    booking_id = _create_pending_booking(client, headers)

    payment_resp = client.post(
        "/payments", json={"booking_id": booking_id}, headers=headers
    )
    assert payment_resp.json()["status"] == "FAILED"
    provider_reference = payment_resp.json()["provider_reference"]

    webhook_resp = client.post(
        "/payments/webhook",
        json={
            "event_id": "evt_test_001",
            "provider_reference": provider_reference,
            "status": "SUCCESS",
        },
    )
    assert webhook_resp.status_code == 200
    assert webhook_resp.json()["booking_status"] == "CONFIRMED"

    booking_resp = client.get(f"/bookings/{booking_id}", headers=headers)
    assert booking_resp.json()["status"] == "CONFIRMED"


def test_webhook_is_idempotent_on_duplicate_event(client):
    headers = signup_and_login(client)
    booking_id = _create_pending_booking(client, headers)

    payment_resp = client.post(
        "/payments", json={"booking_id": booking_id}, headers=headers
    )
    provider_reference = payment_resp.json()["provider_reference"]

    payload = {
        "event_id": "evt_dup_001",
        "provider_reference": provider_reference,
        "status": "SUCCESS",
    }

    first = client.post("/payments/webhook", json=payload)
    assert first.status_code == 200
    assert (
        "duplicate" not in first.json()["detail"] if "detail" in first.json() else True
    )

    second = client.post("/payments/webhook", json=payload)
    assert second.status_code == 200
    assert "already processed" in second.json()["detail"]

    # Booking status must be identical after the duplicate — not re-flipped or corrupted.
    booking_resp = client.get(f"/bookings/{booking_id}", headers=headers)
    assert booking_resp.json()["status"] == "CONFIRMED"


def test_webhook_unknown_provider_reference_404(client):
    resp = client.post(
        "/payments/webhook",
        json={
            "event_id": "evt_ghost",
            "provider_reference": "sim_doesnotexist",
            "status": "SUCCESS",
        },
    )
    assert resp.status_code == 404


def test_webhook_invalid_status_rejected(client):
    resp = client.post(
        "/payments/webhook",
        json={
            "event_id": "evt_bad_status",
            "provider_reference": "sim_whatever",
            "status": "GARBAGE",
        },
    )
    assert resp.status_code == 422
