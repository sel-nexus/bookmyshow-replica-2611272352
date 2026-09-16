import { expect, test } from '@playwright/test';

test('authenticated customer pays and sees backend confirmation details', async ({ page }) => {
  const failures: string[] = [];
  page.on('console', (message) => { if (message.type() === 'error') failures.push(message.text()); });
  page.on('pageerror', (error) => failures.push(error.message));
  await page.goto('/login');
  await page.getByLabel('Mobile number').fill('9876543210');
  await page.getByRole('button', { name: /continue/i }).click();
  await page.getByLabel(/OTP|One-time password/).fill('1234');
  await page.getByRole('button', { name: /verify|reveal films/i }).click();
  await page.getByRole('button', { name: 'Select Paradise' }).click();
  await page.getByRole('button', { name: 'Select Sandhya 70mm' }).click();
  await page.getByRole('button', { name: 'Continue to payment' }).click();
  await page.getByLabel('Demo card number').fill('4242 4242 4242 4242');
  await page.getByRole('button', { name: 'Pay ₹450' }).click();
  await expect(page.getByRole('heading', { name: "You're booked." })).toBeVisible({ timeout: 5000 });
  await expect(page.getByText(/BMS-\d{8}-[A-Z0-9]{6}/)).toBeVisible();
  await expect(page.getByText('Paradise')).toBeVisible();
  await expect(page.getByText('Sandhya 70mm')).toBeVisible();
  await expect(page.getByText('A1, A2, A3')).toBeVisible();
  await expect(page.getByText('₹450.00')).toBeVisible();
  expect(failures).toEqual([]);
});
