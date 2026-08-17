import { mkdtempSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { extname, join, relative, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

const root = resolve(process.argv[2] || 'src')
const files = []
function walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) walk(path)
    else if (extname(path) === '.vue') files.push(path)
  }
}
walk(root)

const temp = mkdtempSync(join(tmpdir(), 'm9394-vue-syntax-'))
const errors = []
try {
  files.forEach((file, index) => {
    const source = readFileSync(file, 'utf8')
    const match = source.match(/<script(?:\s+setup)?[^>]*>([\s\S]*?)<\/script>/i)
    if (!match) return
    const target = join(temp, `${index}.mjs`)
    writeFileSync(target, match[1], 'utf8')
    const result = spawnSync(process.execPath, ['--check', target], { encoding: 'utf8' })
    if (result.status !== 0) errors.push(`${relative(root, file)}\n${result.stderr || result.stdout}`)
  })
} finally {
  rmSync(temp, { recursive: true, force: true })
}

if (errors.length) {
  console.error('Vue script syntax gate FAILED')
  for (const error of errors) console.error(error)
  process.exit(1)
}
console.log(`Vue script syntax gate OK: ${files.length}/${files.length} SFCs`)
