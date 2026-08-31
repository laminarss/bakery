# Billing System Mini Task

A production-oriented FastAPI implementation of the recruitment mini task.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL 17
- Pydantic v2
- Jinja2
- BackgroundTasks for asynchronous invoice delivery
- Pytest

## Features

- Product CRUD with stock, unit price and tax percentage, including a simple management page.
- Billing form with dynamic product rows.
- Shop denomination counts: 500, 50, 20, 10, 5, 2, 1.
- Bill calculation and tax calculation.
- Limited-denomination change calculation.
- Atomic stock deduction during bill creation.
- Invoice email dispatched in the background.
- Purchase history by customer email.
- Purchase detail view.
- API validation and automated tests.
- Basic HTML UI; no framework/CSS dependency is required.

## Assumptions

1. Money is stored as PostgreSQL `NUMERIC(12,2)` rather than binary floating point. The task describes price/tax as floats, but decimal arithmetic avoids monetary rounding errors.
2. A bill is created only when the customer has paid at least the final payable amount.
3. The task's "rounded down" value is implemented as the floor of the net payable amount to the nearest whole rupee. The customer change is calculated from that rounded-down payable value, matching the supplied Page 2 example.
4. Change must use the entered shop denomination inventory. If an exact combination is impossible, bill creation fails and stock is not changed.
5. Product stock is decremented when a bill is successfully created. Denomination inventory entered on the billing form is stored as a snapshot for auditability; it is not globally depleted because the task treats denomination counts as the shop's available values at checkout.
6. Customer identity is represented by email. No separate customer table is necessary for the requested behavior.
7. Invoice delivery is asynchronous using FastAPI `BackgroundTasks`. For a multi-instance/high-volume deployment, this can be replaced with a durable queue such as Celery/RQ without changing the billing service contract.
8. SMTP is disabled by default so the project can run without external mail credentials. Set `EMAIL_ENABLED=true` and SMTP settings to send real invoices.

## Run with PostgreSQL

```bash
docker compose up -d db
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

## Run without PostgreSQL

For a quick evaluation, set:

```text
DATABASE_URL=sqlite:///./billing.sqlite3
```

Then run the application. Tests automatically use an isolated SQLite database.

## Tests

```bash
pytest -q
```

## Product API

- `GET /api/products`
- `POST /api/products`
- `GET /api/products/{product_id}`
- `PUT /api/products/{product_id}`
- `DELETE /api/products/{product_id}`

Products can also be seeded with `python -m scripts.seed`.

## Billing API

`POST /api/bills`

Example request:

```json
{
  "customer_email": "customer@example.com",
  "items": [
    {"product_id": "P1001", "quantity": 2},
    {"product_id": "P1002", "quantity": 1}
  ],
  "denominations": [
    {"value": 500, "count": 2},
    {"value": 50, "count": 4},
    {"value": 20, "count": 3},
    {"value": 10, "count": 5},
    {"value": 5, "count": 2},
    {"value": 2, "count": 5},
    {"value": 1, "count": 10}
  ],
  "amount_paid": "1000.00"
}
```

## Screenshots for submission

The evaluator can use the billing page and generated bill page directly. The repository contains no third-party UI framework so the screenshots remain focused on functionality.
