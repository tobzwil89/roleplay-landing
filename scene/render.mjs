// Nimmt scene.html Bild für Bild auf und baut daraus die Videos und Standbilder in assets/.
// Aufruf:  node scene/render.mjs            alles (Quer- und Hochformat)
//          node scene/render.mjs still      nur je ein Standbild zur Kontrolle
// Braucht Playwright (aus ../tunnel-front geliehen) und ffmpeg.
import { createRequire } from 'node:module'
import { execFileSync } from 'node:child_process'
import { mkdirSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

const require = createRequire(import.meta.url)
const { chromium } = require(path.resolve(import.meta.dirname, '../../tunnel-front/node_modules/playwright'))

const SECONDS = 12
const FPS = 30
const ROOT = path.resolve(import.meta.dirname, '..')
const FORMATS = [
  { name: '16x9', width: 1920, height: 1080, crf: 27 },
  { name: '9x16', width: 1080, height: 1920, crf: 27 },
]
const stillOnly = process.argv[2] === 'still'

const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] })
// ONLY=9x16 rendert nur ein Format
for (const f of FORMATS.filter((x) => !process.env.ONLY || x.name === process.env.ONLY)) {
  const page = await browser.newPage({ viewport: { width: f.width, height: f.height }, deviceScaleFactor: 1 })
  page.on('pageerror', (e) => console.error(e.message))
  await page.goto('file://' + path.join(ROOT, 'scene/scene.html?capture'))
  await page.waitForFunction(() => typeof window.renderAt === 'function')

  // Standbild (auch Ersatzbild für die Seite)
  await page.evaluate(() => window.renderAt(0.15))
  await page.screenshot({ path: path.join(ROOT, `assets/poster-${f.name}.jpg`), type: 'jpeg', quality: 82 })
  console.log(`Standbild ${f.name} fertig`)
  if (stillOnly) { await page.close(); continue }

  const dir = path.join(process.env.FRAMES_DIR || tmpdir(), `frames-${f.name}`)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const total = SECONDS * FPS
  for (let i = 0; i < total; i++) {
    await page.evaluate((t) => window.renderAt(t), i / total)
    await page.screenshot({ path: path.join(dir, `${String(i).padStart(4, '0')}.png`) })
    if (i % 60 === 0) console.log(`${f.name}: Bild ${i}/${total}`)
  }
  await page.close()

  execFileSync('ffmpeg', [
    '-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(dir, '%04d.png'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', String(f.crf), '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart', '-an', path.join(ROOT, `assets/hero-${f.name}.mp4`),
  ], { stdio: 'inherit' })
  rmSync(dir, { recursive: true, force: true })
  console.log(`Video ${f.name} fertig`)
}
await browser.close()
