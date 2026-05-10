import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const renderer = new marked.Renderer()

renderer.code = (code: string, language?: string) => {
  const validLang = language && hljs.getLanguage(language) ? language : 'plaintext'
  const highlighted = hljs.highlight(code, { language: validLang }).value
  return `<pre class="hljs"><div class="code-header"><span class="code-lang">${validLang}</span><button class="copy-btn" onclick="copyCode(this)">复制</button></div><code class="hljs language-${validLang}">${highlighted}</code></pre>`
}

marked.setOptions({
  renderer,
  breaks: true,
  gfm: true,
})

export function renderMarkdown(content: string): string {
  return marked.parse(content) as string
}

// 给全局 window 暴露 copyCode 供按钮调用
;(window as any).copyCode = function(btn: HTMLButtonElement) {
  const pre = btn.closest('pre')
  if (!pre) return
  const code = pre.querySelector('code')
  if (!code) return
  navigator.clipboard.writeText(code.textContent || '').then(() => {
    const old = btn.textContent
    btn.textContent = '已复制'
    setTimeout(() => (btn.textContent = old), 1500)
  })
}
