# BookMyShow Replica

A private, demo-only cinema booking flow built with Angular, FastAPI, PostgreSQL, and Alembic.

## Prerequisites

- PostgreSQL 14+ running locally
- Python environment at `$HOME/venvs/bookmyshow` (or another Python 3.12-compatible virtual environment)
- Node.js 20+
- Docker Desktop/Compose (optional)

## PostgreSQL and backend setup

Create the database role used by the supplied environment settings if it does not exist:

```bash
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
cd backend
cp .env.example .env
$HOME/venvs/bookmyshow/bin/pip install -r requirements.txt
PYTHONPATH=. $HOME/venvs/bookmyshow/bin/python -m alembic upgrade head
PYTHONPATH=. $HOME/venvs/bookmyshow/bin/python -m uvicorn app.main:app --reload --port 8000
```

The API creates the configured application database when it is absent. Migrations create the schema; startup seeds the approved movies, theatres, and mappings.

## Frontend setup

```bash
cd frontend
cp .env.example .env
npm ci
node node_modules/@angular/cli/bin/ng.js serve
```

Open `http://localhost:4200`. The development API base defaults to the same origin; configure the development proxy/origin as appropriate for your local environment.

## Tests

Tests require a running real PostgreSQL service and use the `bookmyshow_test` database:

```bash
sudo service postgresql start || true
cd backend && PYTHONPATH=. $HOME/venvs/bookmyshow/bin/python -m pytest tests/test_bookings.py -q
cd backend && PYTHONPATH=. $HOME/venvs/bookmyshow/bin/python -m pytest tests/test_integration_flow.py -q
cd frontend && node node_modules/@angular/cli/bin/ng.js test --watch=false
cd frontend && node node_modules/@angular/cli/bin/ng.js build
```

The Playwright specifications in `frontend/e2e/` require the backend and frontend to be running against the same real PostgreSQL database.

## Docker Compose

```bash
docker compose up --build
```

Use the service environment variables in `docker-compose.yml` to point the API and UI at their deployed origins.

## Demo limitations

Authentication accepts the configured demo OTP (default `1234`). Payment fields are presentation-only demo inputs: no card, UPI, payment instrument, payment total, or confirmation input is ever sent to the API. The server validates the fixed seats, mapping, price, and confirmation itself.

## License

Private and proprietary. All rights reserved; no permission is granted to copy, distribute, modify, or use this software outside the authorised project context.
