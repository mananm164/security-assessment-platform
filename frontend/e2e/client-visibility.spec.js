import { expect, test } from '@playwright/test';
import { clientEmail, e2ePassword, login } from './helpers.js';

test('client user cannot see import controls or raw observation navigation', async ({ page }) => {
  await login(page, clientEmail, e2ePassword);

  await expect(page.getByRole('link', { name: 'Scanner Observations' })).toHaveCount(0);
  await page.getByRole('link', { name: 'Assessments' }).click();
  await page.getByRole('row', { name: /E2E Northwind Browser Import/i }).getByRole('link', { name: 'Open' }).click();

  await expect(page.getByRole('tab', { name: 'Imports' })).toHaveCount(0);
  await expect(page.getByRole('tab', { name: 'Scanner Observations' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Import scan report' })).toHaveCount(0);
});
