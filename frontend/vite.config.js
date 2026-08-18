import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const productVersion = readFileSync(resolve(process.cwd(), '..', 'VERSION'), 'utf8').trim()

export default defineConfig({
  plugins: [vue()],
  define: {
    __MISTER9394_VERSION__: JSON.stringify(productVersion),
  },
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.MISTER9394_API_URL || 'http://127.0.0.1:8000'
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
