import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [react()],
  server: {
    proxy: {
      '/health': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/total-pages': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/page-text': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/page-image': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/page-image-binary': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/update-book-info': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/check-toc-exists': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/update-toc': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/update-alignment-offset': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/check-alignment-offset': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/books': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/chapters': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/upload-book': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/delete-book': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/sections': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/pages': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/view-pdf': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    },
  },
})
