/**
 * 消息类型常量定义
 */
export const MESSAGE_TYPES = {
  USER: 'user',
  ASSISTANT: 'assistant', 
  TOOL_CALL: 'tool_call',
  TOOL_RESULT: 'tool_result'
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
  },
  [MESSAGE_TYPES.TOOL_CALL]: {
    align: 'left',
    bgColor: '#fff7e6', 
    textColor: '#333',
    showHeader: true,
    icon: '🔧',
    defaultSender: 'AI助手'
  },
  [MESSAGE_TYPES.TOOL_RESULT]: {
    align: 'left',
    bgColor: '#f6ffed',
    textColor: '#333', 
    showHeader: true,
    icon: '📊',
    defaultSender: '工具执行结果'
  }
}

/**
 * 工具图标映射
 */
export const TOOL_ICONS = {
  calculator: '🧮',
  web_search: '🔍',
  default: '🔧'
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
 * 检查是否为工具相关消息
 * @param {string} messageType - 消息类型
 * @returns {boolean} 是否为工具消息
 */
export function isToolMessage(messageType) {
  return messageType === MESSAGE_TYPES.TOOL_CALL || messageType === MESSAGE_TYPES.TOOL_RESULT
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
