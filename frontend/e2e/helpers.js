import { expect } from '@playwright/test';

export const consultantEmail = 'consultant.e2e@sarp.example';
export const clientEmail = 'client.e2e@sarp.example';
export const e2ePassword = process.env.E2E_TEST_PASSWORD || 'change-me-e2e-only';

export async function login(page, email = consultantEmail, password = e2ePassword) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByRole('textbox', { name: 'Password' }).fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: /Assessments|Risk Dashboard/ })).toBeVisible();
}
