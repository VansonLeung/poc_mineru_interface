import { test, expect } from '@playwright/test';

const sampleFile = {
  name: 'sample.pdf',
  mimeType: 'application/pdf',
  buffer: Buffer.from('%PDF-1.4 sample'),
};

test('upload flow shows outputs', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Miner-U Web Interface' })).toBeVisible();

  const dropzone = page.getByTestId('upload-dropzone');
  await expect(dropzone).toBeVisible();

  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(sampleFile);

  await expect(page.getByText(/Uploading sample.pdf/i)).toBeVisible();
  await expect(page.getByText(/Download Markdown/i)).toBeVisible();
  await expect(page.getByText(/Download JSON/i)).toBeVisible();
});
