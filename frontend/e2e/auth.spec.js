import { expect, test } from '@playwright/test';

test('protected routes redirect unauthenticated users to login', async ({ page }) => {
  await page.goto('/assessments');
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole('heading', { name: 'SARP' })).toBeVisible();
});
