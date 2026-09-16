/** Exercise the browser authentication journey against the live API. */
import { expect, test } from '@playwright/test';

test('a customer enters with a mobile number and the configured demo OTP', async ({ page }) => {
  const failures: string[] = [];
  page.on('console', (message) => { if (message.type() === 'error') { failures.push(message.text()); } });
  page.on('pageerror', (error) => failures.push(error.message));
  await page.goto('/');
  await page.getByRole('link', { name: 'Enter the theatre' }).click();
  await page.getByLabel('Mobile number').fill('9876543210');
  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.getByRole('heading', { name: 'Verify code.' })).toBeVisible();
  await page.getByLabel('One-time password').fill('1234');
  await page.getByRole('button', { name: 'Reveal films' }).click();
  await expect(page.getByRole('heading', { name: 'Films arriving next.' })).toBeVisible();
  expect(failures).toEqual([]);
});
