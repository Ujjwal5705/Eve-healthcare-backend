# EVE Healthcare — Diagnostic Test Booking & Payments API

A backend service for booking diagnostic tests at diagnostic centres, with a simulated
payment flow and an idempotent payment webhook.

## Tech Stack

- **FastAPI** (Python 3.11) — async web framework with automatic OpenAPI/Swagger docs
- **PostgreSQL** + **SQLAlchemy 2.0** — data layer
- **Alembic** — database migrations
- **JWT** (via `python-jose`) — authentication
- **bcrypt** (via `passlib`) — password hashing
- **Pytest** — automated tests (25 tests, isolated test database, transactional rollback per test)

## Running Locally (without Docker)

### Prerequisites
- Python 3.11+
- PostgreSQL running locally

### Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

createdb eve_healthcare
createdb eve_healthcare_test     # only needed to run the test suite
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/eve_healthcare
SECRET_KEY=some-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Run migrations:

```bash
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger docs.

### Running Tests

```bash
pytest -v
```

Tests use a separate `eve_healthcare_test` database and each test runs inside a transaction
that's rolled back afterward, so tests never leak state into one another.

## Running with Docker

```bash
docker compose up --build
```

This starts Postgres and the API, and automatically runs `alembic upgrade head` before the
server starts. The API is available at `http://127.0.0.1:8000`.

## Authentication

Most endpoints require a JWT. Get one via `/auth/login`, then pass it as:

```text
Authorization: Bearer <token>
```

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Create a new user |
| POST | `/auth/login` | No | Get a JWT access token |

**Signup example:**
```bash
curl -X POST [http://127.0.0.1:8000/auth/signup](http://127.0.0.1:8000/auth/signup) \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123", "full_name": "Test User"}'
```

**Login example:**
```bash
curl -X POST [http://127.0.0.1:8000/auth/login](http://127.0.0.1:8000/auth/login) \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

### Diagnostic Centres & Tests
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/centres` | Yes | Create a diagnostic centre |
| GET | `/centres` | No | List centres (supports `?location=` filter, `?skip=`, `?limit=`) |
| GET | `/centres/{id}` | No | Get a centre with its tests |
| POST | `/centres/{id}/tests` | Yes | Add a test to a centre |
| GET | `/centres/{id}/tests` | No | List tests for a centre |

**Create a centre:**
```bash
curl -X POST [http://127.0.0.1:8000/centres](http://127.0.0.1:8000/centres) \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "City Diagnostics", "location": "Indore"}'
```

**Add a test to a centre:**
```bash
curl -X POST [http://127.0.0.1:8000/centres/1/tests](http://127.0.0.1:8000/centres/1/tests) \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "Complete Blood Count", "price": 499.00}'
```

### Bookings
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/bookings` | Yes | Create a booking (status starts as `PENDING`) |
| GET | `/bookings` | Yes | List the current user's bookings |
| GET | `/bookings/{id}` | Yes | Get a specific booking (owner only) |
| POST | `/bookings/{id}/cancel` | Yes | Cancel a `PENDING` or `CONFIRMED` booking |

**Create a booking:**
```bash
curl -X POST [http://127.0.0.1:8000/bookings](http://127.0.0.1:8000/bookings) \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"test_id": 1, "centre_id": 1, "appointment_time": "2026-12-01T10:00:00"}'
```

### Payments
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/payments` | Yes | Simulate a payment for a booking |
| POST | `/payments/webhook` | No* | Idempotent webhook for payment-status updates |

\* In a real system this would be secured with a signature/HMAC check from the payment provider,
not left fully open. See "What I'd improve" below.

**Simulate a payment:**
```bash
curl -X POST [http://127.0.0.1:8000/payments](http://127.0.0.1:8000/payments) \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"booking_id": 1}'
```

**Send a webhook event:**
```bash
curl -X POST [http://127.0.0.1:8000/payments/webhook](http://127.0.0.1:8000/payments/webhook) \
  -H "Content-Type: application/json" \
  -d '{"event_id": "evt_001", "provider_reference": "sim_abc123", "status": "SUCCESS"}'
```

## Database Schema

- **`users`**: `id`, `email` (unique), `hashed_password`, `full_name`, `created_at`
- **`diagnostic_centres`**: `id`, `name`, `location`, `created_at`
- **`diagnostic_tests`**: `id`, `name`, `price`, `centre_id` (FK -> `diagnostic_centres`, cascade delete), `created_at`
- **`bookings`**: `id`, `user_id` (FK -> `users`), `test_id` (FK -> `diagnostic_tests`), `centre_id` (FK -> `diagnostic_centres`), `appointment_time`, `amount`, `status` (PENDING | CONFIRMED | FAILED | CANCELLED), `created_at`, `updated_at`
- **`payments`**: `id`, `booking_id` (FK -> `bookings`), `amount`, `status` (SUCCESS | FAILED), `provider_reference` (unique), `created_at`
- **`webhook_events`**: `id`, `event_id` (unique), `payload` (raw JSON, for audit), `received_at`

**Key design decisions:**

- **`Booking.amount` is a snapshot of `DiagnosticTest.price` at booking time**, not a live
  lookup. If a centre changes a test's price later, existing bookings keep their original
  amount. This mirrors how real invoicing systems work.
- **`WebhookEvent.event_id` is unique** and is the single source of truth for idempotency.
  Every webhook first checks whether its `event_id` has been seen; if so, it's a no-op. The
  check-then-insert isn't fully atomic on its own, so a `try/except IntegrityError` around the
  final commit catches the rare race where two identical webhooks are processed concurrently
  before either commits — the unique constraint is what actually guarantees correctness.
- **`Payment.provider_reference` is unique** and simulates the transaction ID a real payment
  gateway (Stripe, Razorpay, etc.) would issue. The webhook uses it to find which payment/
  booking it refers to — this is how real webhook integrations work.
- Booking and payment status updates that happen together (e.g., in the webhook handler) are
  committed in a single transaction, so a payment can never be recorded as `SUCCESS` while its
  booking is stuck at `PENDING`, or any other inconsistent combination.

## Important Assumptions

- Any authenticated user can create diagnostic centres and tests (no admin/role system). In a
  real product, centre/test management would likely be restricted to an admin or centre-staff
  role — the brief didn't call for role-based access, so I kept it simple and noted this instead
  of over-engineering.
- Browsing centres and tests is public (no auth required); booking and paying require auth.
- A user can only view, cancel, or pay for their own bookings — enforced with 403s.
- The payment webhook is not authenticated/signed in this simulation. A production system would
  verify a signature header from the payment provider before trusting the payload.
- `/payments` (the direct simulate-payment call) and `/payments/webhook` can disagree — the
  webhook is treated as the authoritative final word, since that's how real gateways behave
  (an immediate API response can differ from the async settlement outcome).
- A user cannot create two active (`PENDING`/`CONFIRMED`) bookings for the same test, centre,
  and exact appointment time.

## What I'd Improve With More Time

- Role-based access control (admin vs. patient) for managing centres/tests.
- HMAC/signature verification on the webhook endpoint, as real payment providers require.
- Rate limiting on auth and payment endpoints.
- Redis caching for the centre/test listing endpoints.
- Celery (or similar) for retrying failed webhook deliveries asynchronously instead of relying
  on the caller to retry.
- Structured (JSON) logging instead of default uvicorn logs.
- Pagination on `/bookings` (currently only `/centres` is paginated).
- Soft deletes / audit trail on bookings instead of hard status transitions only.