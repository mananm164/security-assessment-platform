import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from '@playwright/test';
import { consultantEmail, e2ePassword, login } from './helpers.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nmapFixture = path.resolve(__dirname, '../../backend/fixtures/nmap/sample.xml');

test('consultant uploads previews and confirms a fictional Nmap report', async ({ page }) => {
  await login(page, consultantEmail, e2ePassword);

  await page.getByRole('link', { name: 'Assessments' }).click();
  await page.getByRole('row', { name: /E2E Northwind Browser Import/i }).getByRole('link', { name: 'Open' }).click();
  await page.getByRole('tab', { name: 'Imports' }).click();
  await page.getByRole('button', { name: 'Import scan report' }).click();

  await page.getByLabel('Source tool').click();
  await page.getByRole('option', { name: 'Nmap' }).click();
  await page.locator('input[type="file"]').setInputFiles(nmapFixture);
  await page.getByRole('button', { name: 'Generate preview' }).click();

  await expect(page.getByText('Open TCP/80')).toBeVisible();
  await expect(page.getByText('E2E_FAKE_SECRET_DO_NOT_RENDER')).toHaveCount(0);

  await page.getByRole('button', { name: 'Confirm import' }).click();
  await expect(page.getByText(/Import completed/)).toBeVisible();
  await expect(page.getByRole('tab', { name: 'Scanner Observations' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('cell', { name: 'Open TCP/80 (http)' })).toBeVisible();
  await expect(page.getByText('E2E_FAKE_SECRET_DO_NOT_RENDER')).toHaveCount(0);
});
