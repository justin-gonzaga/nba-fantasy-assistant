// WEB-008 AC2: a normal build must not contain the e2e auth seam (src/auth/e2eAuth.ts).
// Usage: node scripts/check-no-e2e.mjs [distDir]   (default: dist next to this script's app)
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const dist = process.argv[2] ?? join(fileURLToPath(new URL('..', import.meta.url)), 'dist')
const assets = join(dist, 'assets')
const hits = readdirSync(assets)
  .filter((f) => f.endsWith('.js'))
  .filter((f) => /e2e/i.test(readFileSync(join(assets, f), 'utf8')))

if (hits.length > 0) {
  console.error(`e2e code in the production build: ${hits.join(', ')}`)
  process.exit(1)
}
console.log(`no e2e code in ${assets}`)
