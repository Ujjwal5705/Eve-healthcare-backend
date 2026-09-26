import random
import uuid

from app.models.payment import PaymentStatus


def generate_provider_reference() -> str:
    """Simulates the transaction reference a real payment gateway would return."""
    return f"sim_{uuid.uuid4().hex}"


def simulate_payment_result(success_rate: float = 0.8) -> PaymentStatus:
    """
    Simulates a payment gateway's decision.
    Defaults to an 80% success rate, purely for demo purposes.
    """
    return (
        PaymentStatus.SUCCESS
        if random.random() < success_rate
        else PaymentStatus.FAILED
    )
