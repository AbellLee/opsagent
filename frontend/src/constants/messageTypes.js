/**
 * 消息类型常量定义 - 简化版本，参考Augment风格
 */
export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant'
}

/**
 * 消息显示配置
 */
export const MESSAGE_CONFIG = {
  [MESSAGE_TYPES.USER]: {
    align: 'right',
    bgColor: '#409eff',
    textColor: '#fff',
    showHeader: false,
    icon: '👤',
    defaultSender: '用户'
  },
  [MESSAGE_TYPES.ASSISTANT]: {
    align: 'left',
    bgColor: '#f0f5ff',
    textColor: '#333',
    showHeader: true,
    icon: '🤖',
    defaultSender: 'AI助手'
  }
}

/**
 * 工具图标映射
 */
export const TOOL_ICONS = {
  calculator: '🧮',
  web_search: '🔍',
  file_search: '📁',
  code_search: '💻',
  default: '🔧'
}

/**
 * 工具调用状态
 */
export const TOOL_STATUS = {
  CALLING: 'calling',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

/**
 * 消息状态常量
 */
export const MESSAGE_STATUS = {
  SENDING: 'sending',
  SENT: 'sent',
  DELIVERED: 'delivered',
  FAILED: 'failed',
  RETRYING: 'retrying'
}

/**
 * 获取工具图标
 * @param {string} toolName - 工具名称
 * @returns {string} 工具图标
 */
export function getToolIcon(toolName) {
  return TOOL_ICONS[toolName] || TOOL_ICONS.default
}

/**
 * 获取消息配置
 * @param {string} messageType - 消息类型
 * @returns {object} 消息配置
 */
export function getMessageConfig(messageType) {
  return MESSAGE_CONFIG[messageType] || MESSAGE_CONFIG[MESSAGE_TYPES.ASSISTANT]
}

/**
 * 检查消息是否包含工具调用
 * @param {object} message - 消息对象
 * @returns {boolean} 是否包含工具调用
 */
export function hasToolCalls(message) {
  return message && message.tool_calls && Array.isArray(message.tool_calls) && message.tool_calls.length > 0
}

/**
 * 获取工具调用状态显示文本
 * @param {string} status - 工具状态
 * @returns {string} 状态显示文本
 */
export function getToolStatusText(status) {
  switch (status) {
    case TOOL_STATUS.CALLING:
    case 'calling':
      return '执行中...'
    case TOOL_STATUS.COMPLETED:
    case 'completed':
      return '已完成'
    case TOOL_STATUS.FAILED:
    case 'failed':
      return '执行失败'
    case 'unknown':
    default:
      return '未知状态'
  }
}

/**
 * 检查消息内容是否为JSON格式
 * @param {string} content - 消息内容
 * @returns {boolean} 是否为JSON格式
 */
export function isJsonContent(content) {
  if (!content || typeof content !== 'string') return false
  try {
    JSON.parse(content)
    return true
  } catch {
    return false
  }
}

/**
 * 格式化JSON内容
 * @param {string} content - JSON字符串
 * @returns {string} 格式化后的JSON字符串
 */
export function formatJsonContent(content) {
  try {
    return JSON.stringify(JSON.parse(content), null, 2)
  } catch {
    return content
  }
}

/**
 * 创建标准消息对象
 * @param {string} type - 消息类型
 * @param {string} content - 消息内容
 * @param {object} extraProps - 额外属性
 * @returns {object} 标准消息对象
 */
export function createMessage(type, content, extraProps = {}) {
  return {
    id: Date.now() + Math.random(),
    type,
    role: type, // 保持向后兼容
    content,
    timestamp: new Date().toISOString(),
    sender: type === MESSAGE_TYPES.USER ? '用户' : 'AI助手',
    ...extraProps
  }
}
