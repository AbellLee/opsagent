import { marked } from 'marked';
import Prism from 'prismjs';
import 'prismjs/themes/prism.css';

// 配置marked选项
marked.setOptions({
  highlight: function(code, lang) {
    if (lang && Prism.languages[lang]) {
      return Prism.highlight(code, Prism.languages[lang], lang);
    } else {
      return code;
    }
  },
  breaks: true,
  gfm: true
});

// 添加对 Mermaid 的支持
const renderer = new marked.Renderer();
const originalCodeRenderer = renderer.code;

renderer.code = function(code, language, isEscaped) {
  if (language === 'mermaid') {
    // 为Mermaid图表添加唯一的ID和标识
    const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
    return `<div class="mermaid" id="${id}">${code}</div>`;
  }
  return originalCodeRenderer.call(this, code, language, isEscaped);
}

marked.use({ renderer });

// Markdown解析函数
export function parseMarkdown(text) {
  if (!text) return text;
  return marked.parse(text);
}

// Mermaid 图表初始化函数
export async function initializeMermaid() {
  if (window.mermaid) {
    // 如果 mermaid 还未初始化，则初始化
    if (!window.mermaid.initialize) {
      await window.mermaid.default;
      window.mermaid = window.mermaid.default;
    }
    
    window.mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      flowchart: {
        useMaxWidth: true
      },
      securityLevel: 'loose',
      fontFamily: '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    });
  }
}