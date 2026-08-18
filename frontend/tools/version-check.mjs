import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(process.cwd(), '..')
const version = readFileSync(resolve(root, 'VERSION'), 'utf8').trim()
const pkg = JSON.parse(readFileSync(resolve(process.cwd(), 'package.json'), 'utf8'))
const lock = JSON.parse(readFileSync(resolve(process.cwd(), 'package-lock.json'), 'utf8'))
const project = JSON.parse(readFileSync(resolve(root, 'project_football9394.json'), 'utf8'))

const mismatches = []
if (pkg.version !== version) mismatches.push(`package.json=${pkg.version}`)
if (lock.version !== version) mismatches.push(`package-lock.json=${lock.version}`)
if (lock.packages?.['']?.version !== version) mismatches.push(`package-lock root=${lock.packages?.['']?.version}`)
if (project.version !== version) mismatches.push(`project.version=${project.version}`)
if (mismatches.length) {
  console.error(`VERSION=${version}; incoherencias: ${mismatches.join(', ')}`)
  process.exit(1)
}
console.log(`version metadata: ${version} PASS`)
