import { expect, test } from '@playwright/test';

test('authenticated user selects a mapped theatre and fixed seats', async ({ page }) => {
  const browserErrors: string[] = [];
  page.on('pageerror', (error) => browserErrors.push(error.message));
  await page.goto('/login');
  await page.getByLabel('Mobile number').fill('9876543210');
  await page.getByRole('button', { name: /continue/i }).click();
  await page.getByLabel('OTP').fill('1234');
  await page.getByRole('button', { name: /verify/i }).click();
  await expect(page.getByRole('heading', { name: 'Choose a movie' })).toBeVisible();
  await page.getByRole('button', { name: 'Select Paradise' }).click();
  await expect(page.getByRole('heading', { name: 'Choose a theatre' })).toBeVisible();
  await page.getByRole('button', { name: 'Select Sandhya 70mm' }).click();
  await expect(page.getByRole('grid', { name: 'Selected seats' })).toContainText('A1');
  await page.getByRole('button', { name: 'Continue to payment' }).click();
  await expect(page.getByText('Payment setup is the next step.')).toBeVisible();
  expect(browserErrors).toEqual([]);
});
