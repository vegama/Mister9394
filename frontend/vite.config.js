import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
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
