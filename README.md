# SubLedger

SubLedger is a backend for managing SaaS subscriptions and billing. It covers plans, customers, subscriptions, invoices and payment attempts, plus an append-only financial ledger for each customer.

It is a REST API built with a layered architecture (routes → services → repositories → models). Billing rules are enforced in the service layer and backed by database constraints. See [DESIGN.md](DESIGN.md) for the low-level design: ERD, responsibilities, workflows and patterns.

## Technology Stack

- Python 3.11+ (Docker image uses 3.12)
- FastAPI + Uvicorn
- SQLAlchemy 2.0 ORM
- PostgreSQL 16 (driver: psycopg 3)
- Pydantic v2 / pydantic-settings
- Alembic
- Pytest
- Docker / Docker Compose

## Project Structure

```
.
├── app/
│   ├── main.py                 # FastAPI app factory, router + error handler registration
│   ├── core/                   # config (env settings), clock, domain exceptions, error handlers
│   ├── db/                     # declarative Base, engine/session, get_db dependency, transaction()
│   ├── models/                 # SQLAlchemy models + enums
│   ├── schemas/                # Pydantic request/response models
│   ├── repositories/           # database read/write operations
│   ├── services/               # business logic (Plan, Customer, Subscription, Invoice, Payment, Ledger)
│   └── routes/                 # API endpoints + dependency-injection wiring
├── alembic/                    # migration environment and versions
├── tests/                      # pytest suite
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── DESIGN.md
└── README.md
```

## Installation (local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # then edit credentials
```

You need a running PostgreSQL instance. The easiest option is `docker compose up -d db`.

## Environment Configuration

Settings are read from environment variables or a `.env` file. Nothing is hard-coded.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | — (required) | Database user |
| `POSTGRES_PASSWORD` | — (required) | Database password |
| `POSTGRES_DB` | `subledger` | Database name |
| `POSTGRES_HOST` | `localhost` | Database host (`db` inside Docker Compose) |
| `POSTGRES_PORT` | `5432` | Database port |
| `DATABASE_URL` | — | Full SQLAlchemy URL; overrides the `POSTGRES_*` parts |
| `INVOICE_DUE_DAYS` | `14` | Days from invoice issue to due date |
| `APP_NAME` / `DEBUG` | `SubLedger` / `false` | App metadata |
| `POSTGRES_HOST_PORT` / `API_PORT` | `5432` / `8000` | Host ports published by Docker Compose |
| `TEST_DATABASE_URL` | in-memory SQLite | Database used by the test suite |

## Database Migrations

```bash
alembic upgrade head                              # apply all migrations
alembic downgrade -1                              # roll back the last migration
alembic revision --autogenerate -m "describe change"   # create a new migration from model changes
alembic check                                     # verify models and migrations are in sync
```

On PostgreSQL, the initial migration also installs triggers that reject `UPDATE`, `DELETE` and `TRUNCATE` on `ledger_entries`.

## Running the Application

**With Docker Compose (recommended)**

```bash
cp .env.example .env
docker compose up --build
```

The API container applies migrations on startup (`alembic upgrade head`) and then serves on <http://localhost:8000>.

**Locally**

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Interactive docs: <http://localhost:8000/docs> (Swagger) and <http://localhost:8000/redoc>.

## API Endpoints

Amounts are decimal strings with 2 decimal places (e.g. `"49.99"`). Currencies are 3-letter ISO codes. List endpoints accept `skip` and `limit` query parameters.

| Method | Endpoint | Description | Success | Errors |
|---|---|---|---|---|
| POST | `/plans` | Create a plan | 201 | 422 |
| GET | `/plans?status=active` | List plans (optional status filter) | 200 | |
| PATCH | `/plans/{plan_id}` | Update name/description/price, or activate/deactivate via `status` | 200 | 404, 422 |
| POST | `/customers` | Create a customer | 201 | 409, 422 |
| GET | `/customers` | List customers | 200 | |
| GET | `/customers/{customer_id}` | Customer details | 200 | 404 |
| GET | `/customers/{customer_id}/ledger` | Chronological ledger history | 200 | 404 |
| POST | `/subscriptions` | Create a subscription | 201 | 404, 409, 422 |
| GET | `/subscriptions?customer_id=&status=` | List subscriptions | 200 | |
| GET | `/subscriptions/{subscription_id}` | Subscription details | 200 | 404 |
| POST | `/subscriptions/{subscription_id}/cancel` | Cancel a subscription | 200 | 404, 409 |
| POST | `/invoices/generate` | Generate an invoice for an active subscription's current period | 201 | 404, 409, 422 |
| GET | `/invoices/{invoice_id}` | Invoice details, including payment attempts | 200 | 404 |
| POST | `/payments/record` | Record a successful or failed payment attempt | 201 | 404, 422 |
| GET | `/health` | Liveness check | 200 | |

### Example flow

```bash
curl -X POST localhost:8000/plans -H 'Content-Type: application/json' \
  -d '{"name":"Pro","billing_cycle":"monthly","price":"49.99","currency":"USD"}'

curl -X POST localhost:8000/customers -H 'Content-Type: application/json' \
  -d '{"name":"Ada Lovelace","email":"ada@example.com","company":"Analytical Engines","contact_details":{"phone":"+44 20 0000"}}'

curl -X POST localhost:8000/subscriptions -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"plan_id":1}'

curl -X POST localhost:8000/invoices/generate -H 'Content-Type: application/json' \
  -d '{"subscription_id":1}'

# Partial payment -> invoice status "partially_paid"
curl -X POST localhost:8000/payments/record -H 'Content-Type: application/json' \
  -d '{"invoice_id":1,"amount":"20.00","status":"success","provider_reference":"ch_001"}'

# Failed attempt -> recorded and ledgered, amount_paid unchanged
curl -X POST localhost:8000/payments/record -H 'Content-Type: application/json' \
  -d '{"invoice_id":1,"amount":"29.99","status":"failed","failure_reason":"card_declined"}'

curl localhost:8000/customers/1/ledger
```

`POST /payments/record` response:

```json
{
  "payment": {"id": 1, "invoice_id": 1, "amount": "20.00", "currency": "USD", "status": "success",
              "provider_reference": "ch_001", "failure_reason": null, "created_at": "..."},
  "invoice": {"id": 1, "amount_due": "49.99", "amount_paid": "20.00", "balance_due": "29.99",
              "status": "partially_paid", "...": "..."}
}
```

Errors use one envelope:

```json
{"error": {"code": "business_rule_violation", "message": "Payment amount 60.00 exceeds the remaining invoice balance 29.99.", "details": null}}
```

### Business rules enforced

1. Plan price must be greater than zero.
2. Customer email is unique (case-insensitive).
3. Inactive plans cannot be subscribed to.
4. A customer can't have two active subscriptions to the same plan. Cancelling frees the slot.
5. An invoice copies the plan price at generation time. Later price changes don't affect it.
6. A successful payment can't exceed the remaining balance.
7. A fully paid invoice gets status `paid`.
8. A partially paid invoice gets status `partially_paid`.
9. Failed payments are stored with their reason and never change `amount_paid`.
10. Ledger entries are append-only (ORM guard plus PostgreSQL trigger) and traceable through `reference_id` (`invoice:{id}`, `payment_attempt:{id}`).

Also note:

- Each billing period is invoiced once. Generating again after the period has ended renews the subscription into the next period.
- Unpaid invoices past their `due_date` are marked `overdue` when fetched.
- Plans keep their `billing_cycle` and `currency` fixed after creation.

## Running Tests

```bash
pytest                 # fast: isolated in-memory SQLite DB per test
pytest -v tests/test_payments.py
```

To run the same suite against PostgreSQL, create an empty test database and set:

```bash
TEST_DATABASE_URL=postgresql+psycopg://subledger:change-me@localhost:5432/subledger_test pytest
```

Inside Docker:

```bash
docker compose run --rm api pytest
```

The suite covers all required scenarios: non-positive plan price, duplicate email, inactive-plan subscription, duplicate active subscription, payment status/amount updates, failed payments leaving `amount_paid` unchanged, and overpayment rejection. It also covers invoice price snapshots, period renewal, ledger traceability and append-only enforcement.
