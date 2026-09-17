import { defineConfig } from '@playwright/test';

/** Run browser journeys against the Angular dev server and a PostgreSQL-backed API. */
export default defineConfig({
  testDir: './e2e',
  timeout: 45_000,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4200',
    trace: 'retain-on-failure'
  },
  webServer: [
    {
      command: "sudo -u postgres psql -c \"DROP DATABASE IF EXISTS bookmyshow_e2e WITH (FORCE);\" && $HOME/venvs/bookmyshow/bin/python -c \"import asyncio; from app.core.database import ensure_database_exists; asyncio.run(ensure_database_exists())\" && $HOME/venvs/bookmyshow/bin/python -m alembic upgrade head && $HOME/venvs/bookmyshow/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/api/health',
      timeout: 120_000,
      reuseExistingServer: false,
      env: {
        DATABASE_URL: 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres',
        DB_NAME: 'bookmyshow_e2e',
        JWT_SECRET: 'bookmyshow-playwright-real-postgres-secret',
        JWT_ISSUER: 'bookmyshow-api',
        JWT_AUDIENCE: 'bookmyshow-web',
        JWT_EXPIRES_SECONDS: '1800',
        DEMO_OTP: '1234',
        CORS_ORIGINS: 'http://127.0.0.1:4200',
        E2E_UNMAPPED_MOVIE_TITLE: 'E2E Unmapped Movie',
        PYTHONPATH: '.'
      }
    },
    {
      command: 'node node_modules/@angular/cli/bin/ng.js serve --host 127.0.0.1 --port 4200',
      url: 'http://127.0.0.1:4200',
      timeout: 120_000,
      reuseExistingServer: false
    }
  ]
});
