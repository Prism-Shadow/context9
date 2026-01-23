// @ts-nocheck
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'url'
import { dirname, resolve } from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Get the project root directory (parent of web directory)
  const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
  
  // Load env file from project root directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, projectRoot, '')
  
  return {
    plugins: [react()],
    base: '/', // Use root path for production
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0', // 允许外部访问
      port: parseInt(env.CONTEXT9_PANEL_PORT || '8012', 10),
      proxy: {
        '/api': {
          target: `http://localhost:${parseInt(env.CONTEXT9_PORT || '8011', 10)}`,
          changeOrigin: true,
        },
      },
    },
  }
})
