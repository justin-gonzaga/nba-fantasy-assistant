// DRAFT-020 AC7: the draft room is its own route chunk, and its sound/motion code (src/features/draft/fx)
// stays under a gzip budget.
// Usage: node scripts/check-chunk-size.mjs [distDir]   (run `pnpm build` first)
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { gzipSync } from 'node:zlib'

export const FX_BUDGET_GZIP = 5 * 1024
// Only the synth uses this Web Audio call; the small prefs module (also read by the report view) stays in the entry.
const MARKER = 'exponentialRampToValueAtTime'

/** `files` are the built chunks as `{ name, text }`; `fxGzip` is the gzip size of the fx code alone. */
export function evaluate(files, fxGzip, budget = FX_BUDGET_GZIP) {
  if (!files.some((f) => f.name.startsWith('DraftPracticePage')))
    return {
      ok: false,
      message: 'no separate DraftPracticePage chunk: the draft room is not lazy-loaded',
    }
  const leaked = files.find((f) => f.name.startsWith('index-') && f.text.includes(MARKER))
  if (leaked) return { ok: false, message: `fx code is in the entry chunk ${leaked.name}` }
  if (!files.some((f) => f.text.includes(MARKER)))
    return { ok: false, message: 'fx code not found in any chunk' }
  return fxGzip > budget
    ? { ok: false, message: `fx code is ${fxGzip} B gzip, over the ${budget} B budget` }
    : {
        ok: true,
        message: `draft room is a lazy chunk; fx code is ${fxGzip} B gzip (budget ${budget} B)`,
      }
}

/** Bundles the fx modules alone (React and the rest of the app external) and gzips the result. */
async function fxGzipSize(root) {
  const { build } = await import('vite')
  const { default: react } = await import('@vitejs/plugin-react')
  const dir = join(root, 'src/features/draft/fx')
  const entry = readdirSync(dir)
    .filter((f) => /\.tsx?$/.test(f) && !f.includes('.test.'))
    .map((f) => join(dir, f))
  const out = await build({
    root,
    configFile: false,
    logLevel: 'silent',
    plugins: [react()],
    build: {
      write: false,
      minify: true,
      lib: { entry, formats: ['es'] },
      rolldownOptions: { external: [/^react($|\/)/, /^\.\.\//] },
    },
  })
  const chunks = (Array.isArray(out) ? out : [out]).flatMap((o) => o.output)
  return gzipSync(chunks.map((c) => c.code ?? '').join('\n')).length
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]
if (isMain) {
  const root = fileURLToPath(new URL('..', import.meta.url))
  const assets = join(process.argv[2] ?? join(root, 'dist'), 'assets')
  const files = readdirSync(assets)
    .filter((f) => f.endsWith('.js'))
    .map((name) => ({ name, text: readFileSync(join(assets, name), 'utf8') }))
  const r = evaluate(files, await fxGzipSize(root))
  console[r.ok ? 'log' : 'error'](r.message)
  if (!r.ok) process.exit(1)
}
