import { test, expect } from '@playwright/test';

const sampleFile = {
  name: 'sample.pdf',
  mimeType: 'application/pdf',
  buffer: Buffer.from('%PDF-1.4 sample'),
};

test('sync mode upload flow shows outputs', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Miner-U Web Interface' })).toBeVisible();

  const dropzone = page.getByTestId('upload-dropzone');
  await expect(dropzone).toBeVisible();

  // Ensure async mode is unchecked (sync mode)
  const asyncCheckbox = page.locator('input[type="checkbox"]');
  await expect(asyncCheckbox).not.toBeChecked();

  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(sampleFile);

  const uploadButton = page.getByRole('button', { name: /Upload and Parse/i });
  await uploadButton.click();

  await expect(page.getByText(/Uploading sample.pdf/i)).toBeVisible();
  await expect(page.getByText(/Download Markdown/i)).toBeVisible({ timeout: 30000 });
  await expect(page.getByText(/Download JSON/i)).toBeVisible();
});

test('async mode shows job status and polling', async ({ page }) => {
  await page.goto('/');

  // Enable async mode
  const asyncCheckbox = page.locator('input[type="checkbox"]');
  await asyncCheckbox.check();
  await expect(asyncCheckbox).toBeChecked();

  // Upload file
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(sampleFile);

  const uploadButton = page.getByRole('button', { name: /Upload and Parse/i });
  await uploadButton.click();

  // Should show job submission
  await expect(page.getByText(/Submitting job/i)).toBeVisible();

  // Should show job ID
  await expect(page.getByText(/Job ID:/i)).toBeVisible({ timeout: 10000 });

  // Should show status (PENDING or PROCESSING)
  await expect(page.getByText(/Status: (PENDING|PROCESSING)/i)).toBeVisible();

  // Should eventually show completion
  await expect(page.getByText(/Status: SUCCESS/i)).toBeVisible({ timeout: 60000 });

  // Should show completed timestamp
  await expect(page.getByText(/Completed:/i)).toBeVisible();

  // Should show results
  await expect(page.getByText(/Download Markdown/i)).toBeVisible({ timeout: 5000 });
  await expect(page.getByText(/Download JSON/i)).toBeVisible();
});
