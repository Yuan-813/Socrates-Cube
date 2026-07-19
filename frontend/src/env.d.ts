/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'page-flip' {
  export class PageFlip {
    constructor(element: HTMLElement, settings: Record<string, any>)
    loadFromHTML(elements: NodeListOf<HTMLElement> | HTMLElement[]): void
    on(event: string, callback: (e: any) => void): void
    flipNext(): void
    flipPrev(): void
    destroy(): void
  }
}

declare module 'mermaid' {
  const mermaid: {
    initialize: (config: Record<string, unknown>) => void
    render: (id: string, definition: string) => Promise<{ svg: string }>
  }
  export default mermaid
}
