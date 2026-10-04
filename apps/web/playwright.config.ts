import { defineConfig, devices } from '@playwright/test'
import { API_URL, DEMO_PORT, DEMO_URL, LIVE_PORT } from './e2e/support/urls'

// WEB-008: persona e2e against `vite preview` of two production builds.
// - demo: no VITE_API_URL, so the sample data and no sign-in (the public demo, D-38)
// - live: VITE_API_URL points at a host the tests mock with page.route, and VITE_E2E_AUTH=1 swaps
//   Google sign-in for a fake adapter (src/auth/e2eAuth.ts; normal builds tree-shake it out)
const CI = !!process.env.CI

const server = (out: string, port: number, env: Record<string, string>) => ({
  command: `node node_modules/vite/bin/vite.js build --outDir ${out} --emptyOutDir && node node_modules/vite/bin/vite.js preview --outDir ${out} --port ${port} --strictPort`,
  url: `http://localhost:${port}`,
  reuseExistingServer: false, // always the current source
  timeout: 120_000,
  // Empty values override any local env file, so each build is exactly the mode it names.
  env: {
    VITE_API_URL: '',
    VITE_E2E_AUTH: '',
    VITE_FIREBASE_API_KEY: '',
    VITE_FIREBASE_AUTH_DOMAIN: '',
    VITE_FIREBASE_PROJECT_ID: '',
    VITE_FIREBASE_APP_ID: '',
    ...env,
  },
})

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: CI,
  retries: CI ? 1 : 0,
  workers: CI ? 4 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: DEMO_URL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    // Steady frames for axe and layout checks; the keyboard persona opts back into motion.
    contextOptions: { reducedMotion: 'reduce' },
  },
  projects: [
    { name: 'iphone-13', use: { ...devices['iPhone 13'] } },
    { name: 'pixel-7', use: { ...devices['Pixel 7'] } },
    {
      name: 'desktop-chrome',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
  ],
  webServer: [
    server('dist-e2e/demo', DEMO_PORT, {}),
    server('dist-e2e/live', LIVE_PORT, { VITE_API_URL: API_URL, VITE_E2E_AUTH: '1' }),
  ],
})
