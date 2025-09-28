import { marked } from 'marked';
import Prism from 'prismjs';
import 'prismjs/themes/prism.css';

// 辅助函数：安全地提取文本内容
function extractText(input) {
  if (typeof input === 'string') {
    return input;
  }
  if (typeof input === 'object' && input !== null) {
    if (input.text) return input.text;
    if (input.raw) return input.raw;
  }
  return String(input || '');
}

// 配置 marked 选项
marked.setOptions({
  breaks: true,
  gfm: true
});

// 创建自定义渲染器
const renderer = new marked.Renderer();

// 重写代码块渲染器
renderer.code = function(code, language, isEscaped) {
  // 确保 code 是字符串
  const actualCode = extractText(code);
  const actualLanguage = extractText(language);

  // 处理 Mermaid 图表
  if (actualLanguage === 'mermaid') {
    const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
    return `<div class="mermaid" id="${id}">${actualCode}</div>`;
  }

  // 处理其他代码块
  let highlightedCode = actualCode;
  if (actualLanguage && Prism.languages[actualLanguage]) {
    try {
      highlightedCode = Prism.highlight(actualCode, Prism.languages[actualLanguage], actualLanguage);
    } catch (error) {
      console.warn('代码高亮失败:', error);
      highlightedCode = actualCode;
    }
  }

  const langClass = actualLanguage ? ` class="language-${actualLanguage}"` : '';
  return `<pre><code${langClass}>${highlightedCode}</code></pre>`;
};

// 使用自定义渲染器
marked.use({ renderer });

// Markdown解析函数
export function parseMarkdown(text) {
  try {
    if (!text) return '';

    // 确保输入是字符串
    if (typeof text !== 'string') {
      console.warn('parseMarkdown received non-string input:', typeof text, text);
      text = String(text);
    }

    // 解析 Markdown
    const result = marked.parse(text);

    // 确保返回字符串
    return typeof result === 'string' ? result : String(result);
  } catch (error) {
    console.error('Markdown解析失败:', error, { input: text });

    // 降级处理：返回HTML转义的纯文本
    const fallbackText = String(text || '');
    return fallbackText
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\n/g, '<br>');
  }
}

// Mermaid 图表初始化函数
export async function initializeMermaid() {
  if (window.mermaid) {
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