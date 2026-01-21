/// <reference types="vite/client" />

declare const process: {
  cwd(): string
  env: {
    CONTEXT9_PANEL_PORT?: string
    [key: string]: string | undefined
  }
}

declare module 'url' {
  export class URL {
    constructor(input: string, base?: string | URL)
    href: string
    origin: string
    protocol: string
    username: string
    password: string
    host: string
    hostname: string
    port: string
    pathname: string
    search: string
    searchParams: URLSearchParams
    hash: string
  }
  export function fileURLToPath(url: string | URL): string
}

interface ImportMeta {
  readonly url: string
}
