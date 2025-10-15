import { marked } from 'marked';
import Prism from 'prismjs';
import 'prismjs/themes/prism.css';

// 手动添加常用语言支持
Prism.languages.python = Prism.languages.python || {
  'comment': {
    pattern: /(^|[^\\])#.*/,
    lookbehind: true
  },
  'string': {
    pattern: /("""|''')[\s\S]*?\1|("|')(?:\\.|(?!\2)[^\\\r\n])*\2/,
    greedy: true
  },
  'function': {
    pattern: /((?:^|\s)def[ \t]+)[a-zA-Z_]\w*(?=\s*\()/g,
    lookbehind: true
  },
  'class-name': {
    pattern: /(\bclass\s+)\w+/i,
    lookbehind: true
  },
  'keyword': /\b(?:and|as|assert|break|class|continue|def|del|elif|else|except|exec|finally|for|from|global|if|import|in|is|lambda|not|or|pass|print|raise|return|try|while|with|yield)\b/,
  'builtin': /\b(?:__import__|abs|all|any|apply|basestring|bin|bool|buffer|bytearray|bytes|callable|chr|classmethod|cmp|coerce|compile|complex|delattr|dict|dir|divmod|enumerate|eval|execfile|file|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|intern|isinstance|issubclass|iter|len|list|locals|long|map|max|memoryview|min|next|object|oct|open|ord|pow|property|range|raw_input|reduce|reload|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|unichr|unicode|vars|xrange|zip)\b/,
  'boolean': /\b(?:True|False|None)\b/,
  'number': /(?:\b(?=\d)|\B(?=\.))(?:0[bo])?(?:(?:\d|0x[\da-f])[\da-f]*\.?\d*|\.\d+)(?:e[+-]?\d+)?j?\b/i,
  'operator': /[-+%=]=?|!=|\*\*?=?|\/\/?=?|<[<=>]?|>[=>]?|[&|^~]/,
  'punctuation': /[{}[\];(),.:]/
};

// 确保JavaScript语言支持存在
if (!Prism.languages.javascript) {
  Prism.languages.javascript = Prism.languages.js = {
    'comment': [
      {
        pattern: /(^|[^\\])\/\*[\s\S]*?(?:\*\/|$)/,
        lookbehind: true
      },
      {
        pattern: /(^|[^\\:])\/\/.*/,
        lookbehind: true
      }
    ],
    'string': {
      pattern: /(["'])(?:(?!\1)[^\\\r\n]|\\(?:\r\n|[\s\S]))*\1/,
      greedy: true
    },
    'class-name': {
      pattern: /(^|[^$\w\xA0-\uFFFF])[A-Z]\w*(?=\.(?:prototype|constructor))/,
      lookbehind: true
    },
    'keyword': /\b(?:as|async|await|break|case|catch|class|const|continue|debugger|default|delete|do|else|enum|export|extends|finally|for|from|function|get|if|implements|import|in|instanceof|interface|let|new|null|of|package|private|protected|public|return|set|static|super|switch|this|throw|try|typeof|undefined|var|void|while|with|yield)\b/,
    'function': /[_$a-zA-Z\xA0-\uFFFF][_$a-zA-Z0-9\xA0-\uFFFF]*(?=\s*\()/i,
    'number': /\b(?:(?:0x(?:[\da-f]+\.?[\da-f]*|\.[\da-f]+)(?:p[+-]?\d+)?)|(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\b/i,
    'operator': /--?|\+\+?|!=?=?|<=?|>=?|==?=?|&&?|\|\|?|\?|\*|\/|~|\^|%/,
    'punctuation': /[{}[\];(),.:]/
  };
}

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
  let actualLanguage = extractText(language);

  console.log('代码块渲染:', { actualCode: actualCode.substring(0, 50), actualLanguage, availableLanguages: Object.keys(Prism.languages) });

  // 如果没有语言标识符，尝试自动检测
  if (!actualLanguage || actualLanguage.trim() === '') {
    // 简单的语言检测
    if (actualCode.includes('def ') && actualCode.includes(':')) {
      actualLanguage = 'python';
    } else if (actualCode.includes('function ') || actualCode.includes('const ') || actualCode.includes('let ')) {
      actualLanguage = 'javascript';
    } else if (actualCode.includes('SELECT ') || actualCode.includes('FROM ')) {
      actualLanguage = 'sql';
    } else if (actualCode.includes('#!/bin/bash') || actualCode.includes('#!/bin/sh')) {
      actualLanguage = 'bash';
    }
    console.log('自动检测语言:', actualLanguage);
  }

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
      console.log('代码高亮成功:', actualLanguage);
    } catch (error) {
      console.warn('代码高亮失败:', error);
      highlightedCode = actualCode;
    }
  } else {
    console.warn('语言不支持或未找到:', actualLanguage, 'Available:', Object.keys(Prism.languages));
    // 如果没有语言支持，至少应用基本的HTML转义
    highlightedCode = actualCode
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  const langClass = actualLanguage ? ` class="language-${actualLanguage}"` : ' class="language-none"';
  return `<pre class="code-block"><code${langClass}>${highlightedCode}</code></pre>`;
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

    console.log('解析Markdown文本:', text.substring(0, 200));

    // 解析 Markdown
    const result = marked.parse(text);

    console.log('Markdown解析结果:', result.substring(0, 200));

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