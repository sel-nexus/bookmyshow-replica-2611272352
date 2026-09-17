import { expect, test } from '@playwright/test';

function collectBrowserFailures(page: import('@playwright/test').Page): string[] {
  const failures: string[] = [];
  page.on('console', (message) => {
    const text = message.text();
    if (message.type() === 'error' && !text.includes('status of 401 (Unauthorized)')) failures.push(text);
  });
  page.on('pageerror', (error) => failures.push(error.message));
  return failures;
}

async function useRealApi(page: import('@playwright/test').Page): Promise<void> {
  await page.addInitScript(() => { (globalThis as { __env?: { API_BASE_URL: string } }).__env = { API_BASE_URL: 'http://127.0.0.1:8000' }; });
}

test('an unauthenticated protected-route visitor is redirected to the accessible sign-in form', async ({ page }) => {
  const failures = collectBrowserFailures(page);
  await useRealApi(page);

  await page.goto('/movies');

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'Sign in.' })).toBeVisible();
  expect(failures).toEqual([]);
});

test('invalid mobile and wrong OTP responses are shown to the customer', async ({ page }) => {
  const failures = collectBrowserFailures(page);
  await useRealApi(page);

  await page.goto('/login');
  await page.getByLabel('Mobile number').fill('not-a-mobile');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.getByRole('alert')).toContainText('Enter exactly ten digits.');

  await page.getByLabel('Mobile number').fill('9876543210');
  const loginResponse = page.waitForResponse((response) => response.url().endsWith('/api/auth/login') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  expect((await loginResponse).status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Verify code.' })).toBeVisible();

  const verifyResponse = page.waitForResponse((response) => response.url().endsWith('/api/auth/verify') && response.request().method() === 'POST');
  await page.getByLabel('One-time password').fill('9999');
  await page.getByRole('button', { name: 'Reveal films' }).click();
  expect((await verifyResponse).status()).toBe(401);
  await expect(page.getByRole('alert')).toContainText('Invalid OTP');
  expect(failures).toEqual([]);
});

test('a valid live login and OTP issue a token, navigate to films, and clear the memory session on refresh', async ({ page }) => {
  const failures = collectBrowserFailures(page);
  await useRealApi(page);

  await page.goto('/login');
  await page.getByLabel('Mobile number').fill('9876543210');
  const loginResponse = page.waitForResponse((response) => response.url().endsWith('/api/auth/login') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  expect((await loginResponse).status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Verify code.' })).toBeVisible();

  await page.getByLabel('One-time password').fill('1234');
  const verifyResponse = page.waitForResponse((response) => response.url().endsWith('/api/auth/verify') && response.request().method() === 'POST');
  const moviesResponse = page.waitForResponse((response) => response.url().endsWith('/api/movies') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'Reveal films' }).click();
  expect((await verifyResponse).status()).toBe(200);
  expect((await moviesResponse).status()).toBe(200);
  await expect(page.getByRole('heading', { name: 'Choose a movie' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Select Paradise' })).toBeVisible();

  await page.reload();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'Sign in.' })).toBeVisible();
  expect(failures).toEqual([]);
});
