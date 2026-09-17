import { expect, test } from '@playwright/test';

test.use({ viewport: { width: 390, height: 844 } });

function collectBrowserFailures(page: import('@playwright/test').Page): string[] {
  const failures: string[] = [];
  page.on('console', (message) => { if (message.type() === 'error') failures.push(message.text()); });
  page.on('pageerror', (error) => failures.push(error.message));
  return failures;
}

async function useRealApi(page: import('@playwright/test').Page): Promise<void> {
  await page.addInitScript(() => { (globalThis as { __env?: { API_BASE_URL: string } }).__env = { API_BASE_URL: 'http://127.0.0.1:8000' }; });
}

test('an authenticated mobile user selects a live mapped theatre and sees the fixed seats', async ({ page }) => {
  const failures = collectBrowserFailures(page);
  await useRealApi(page);

  await page.goto('/login');
  await page.getByLabel('Mobile number').fill('9876543210');
  const loginResponse = page.waitForResponse((response) => response.url().endsWith('/api/auth/login') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  expect((await loginResponse).status()).toBe(200);
  await page.getByLabel('One-time password').fill('1234');
  const verifyResponse = page.waitForResponse((response) => response.url().endsWith('/api/auth/verify') && response.request().method() === 'POST');
  const moviesResponse = page.waitForResponse((response) => response.url().endsWith('/api/movies') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'Reveal films' }).click();
  expect((await verifyResponse).status()).toBe(200);
  expect((await moviesResponse).status()).toBe(200);
  await expect(page.getByRole('button', { name: 'Select Paradise' })).toBeVisible();

  const theatresResponse = page.waitForResponse((response) => response.url().startsWith('http://127.0.0.1:8000/api/theatres?') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'Select Paradise' }).click();
  expect((await theatresResponse).status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Choose a theatre' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Select Sandhya 70mm' })).toBeVisible();

  await page.getByRole('button', { name: 'Select Sandhya 70mm' }).click();
  await expect(page.getByRole('grid', { name: 'Selected seats' })).toContainText('A1');
  await expect(page.getByText('3 seats · ₹450')).toBeVisible();
  await page.getByRole('button', { name: 'Continue to payment' }).click();
  await expect(page.getByRole('heading', { name: 'Confirm payment' })).toBeVisible();
  expect(failures).toEqual([]);
});

test('an authenticated mobile user sees the real empty theatre state for an e2e-only unmapped movie', async ({ page }) => {
  const failures = collectBrowserFailures(page);
  await useRealApi(page);

  await page.goto('/login');
  await page.getByLabel('Mobile number').fill('9876543210');
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.getByLabel('One-time password').fill('1234');
  const moviesResponse = page.waitForResponse((response) => response.url().endsWith('/api/movies') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'Reveal films' }).click();
  expect((await moviesResponse).status()).toBe(200);

  const theatresResponse = page.waitForResponse((response) => response.url().startsWith('http://127.0.0.1:8000/api/theatres?') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'Select E2E Unmapped Movie' }).click();
  expect((await theatresResponse).status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Choose a theatre' })).toBeVisible();
  await expect(page.getByText('No theatres are available for this movie.')).toBeVisible();
  await expect(page.getByRole('button', { name: /^Select / })).toHaveCount(0);
  expect(failures).toEqual([]);
});
