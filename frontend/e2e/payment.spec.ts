import { expect, test } from '@playwright/test';

function collectBrowserFailures(page: import('@playwright/test').Page): string[] {
  const failures: string[] = [];
  page.on('console', (message) => { if (message.type() === 'error') failures.push(message.text()); });
  page.on('pageerror', (error) => failures.push(error.message));
  return failures;
}

async function useRealApi(page: import('@playwright/test').Page): Promise<void> {
  await page.addInitScript(() => { (globalThis as { __env?: { API_BASE_URL: string } }).__env = { API_BASE_URL: 'http://127.0.0.1:8000' }; });
}

test('an authenticated customer sees disabled processing then a real backend booking confirmation', async ({ page }, testInfo) => {
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
  const theatresResponse = page.waitForResponse((response) => response.url().includes('/api/theatres?movie_id=') && response.request().method() === 'GET');
  await page.getByRole('button', { name: 'Select Paradise' }).click();
  expect((await theatresResponse).status()).toBe(200);
  await page.getByRole('button', { name: 'Select Sandhya 70mm' }).click();
  await page.getByRole('button', { name: 'Continue to payment' }).click();

  await page.getByLabel('Demo card number').fill('4242 4242 4242 4242');
  const bookingResponse = page.waitForResponse((response) => response.url().endsWith('/api/bookings') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Pay ₹450' }).click();
  await expect(page.getByRole('button', { name: 'Processing…' })).toBeDisabled();
  await expect(page.getByText('Processing your payment…')).toBeVisible();
  expect((await bookingResponse).status()).toBe(201);

  await expect(page.getByRole('heading', { name: "You're booked." })).toBeVisible();
  const confirmationId = (await page.getByText(/BMS-\d{8}-[A-Z0-9]{6}/).textContent())!;
  await expect(page.getByText('Paradise')).toBeVisible();
  await expect(page.getByText('Sandhya 70mm')).toBeVisible();
  await expect(page.getByText('A1, A2, A3')).toBeVisible();
  await expect(page.getByText('₹450.00')).toBeVisible();

  await page.getByRole('button', { name: 'Start new booking' }).click();
  await expect(page.getByRole('heading', { name: 'Choose a movie' })).toBeVisible();
  const persistedRead = page.waitForResponse((response) => response.url().endsWith(`/api/bookings/${confirmationId}`) && response.request().method() === 'GET');
  await page.goBack();
  expect((await persistedRead).status()).toBe(200);
  await expect(page.getByRole('heading', { name: "You're booked." })).toBeVisible();
  await expect(page.getByText(confirmationId)).toBeVisible();
  await expect(page.getByText('Paradise')).toBeVisible();
  await expect(page.getByText('Sandhya 70mm')).toBeVisible();
  await expect(page.getByText('A1, A2, A3')).toBeVisible();
  await expect(page.getByText('₹450.00')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('payment-confirmation.png'), fullPage: true });
  expect(failures).toEqual([]);
});
