import { ref, computed, nextTick } from 'vue'

// 滚动场景枚举
export const SCROLL_SCENARIOS = {
  FORCE: 'force',           // 强制滚动（发送消息、切换会话）
  SMART: 'smart',           // 智能滚动（新消息到达）
  FOLLOW: 'follow',         // 跟随滚动（流式输出）
  PRESERVE: 'preserve'      // 保持位置（展开工具框）
}

// 滚动管理器
export function useScrollManager(containerRef) {
  // 状态管理
  const isUserScrolling = ref(false)
  const lastScrollTop = ref(0)
  const userScrollTimer = ref(null)
  const isAutoScrolling = ref(false)
  const currentScrollTop = ref(0)
  
  // 防抖定时器
  let scrollDebounceTimer = null
  let followScrollTimer = null
  
  // 响应式的底部检测
  const isNearBottom = computed(() => {
    if (!containerRef.value) return true
    const container = containerRef.value
    const threshold = 50

    // 如果内容高度小于等于容器高度，认为在底部
    if (container.scrollHeight <= container.clientHeight) {
      return true
    }

    return currentScrollTop.value + container.clientHeight >= container.scrollHeight - threshold
  })

  // 检查是否在底部附近（函数版本，用于内部调用）
  const checkIsNearBottom = (threshold = 50) => {
    if (!containerRef.value) return true
    const container = containerRef.value

    // 如果内容高度小于等于容器高度，认为在底部
    if (container.scrollHeight <= container.clientHeight) {
      return true
    }

    return container.scrollTop + container.clientHeight >= container.scrollHeight - threshold
  }
  
  // 检测用户主动滚动
  const detectUserScroll = () => {
    if (!containerRef.value) return

    const scrollTop = containerRef.value.scrollTop
    currentScrollTop.value = scrollTop

    // 如果不是自动滚动且滚动位置发生变化，说明是用户主动滚动
    if (!isAutoScrolling.value && scrollTop !== lastScrollTop.value) {
      isUserScrolling.value = true

      // 清除之前的定时器
      if (userScrollTimer.value) {
        clearTimeout(userScrollTimer.value)
      }

      // 如果用户滚动到底部，立即隐藏按钮
      if (checkIsNearBottom()) {
        isUserScrolling.value = false
      } else {
        // 2秒后重置用户滚动状态
        userScrollTimer.value = setTimeout(() => {
          isUserScrolling.value = false
        }, 2000)
      }
    }

    lastScrollTop.value = scrollTop
  }
  
  // 平滑滚动到底部
  const smoothScrollToBottom = (duration = 300) => {
    if (!containerRef.value) return
    
    const container = containerRef.value
    const start = container.scrollTop
    const target = container.scrollHeight - container.clientHeight
    const distance = target - start
    
    if (distance === 0) return
    
    isAutoScrolling.value = true
    
    const startTime = performance.now()
    
    const animateScroll = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      
      // 使用easeOutCubic缓动函数
      const easeProgress = 1 - Math.pow(1 - progress, 3)
      
      container.scrollTop = start + distance * easeProgress
      
      if (progress < 1) {
        requestAnimationFrame(animateScroll)
      } else {
        isAutoScrolling.value = false
      }
    }
    
    requestAnimationFrame(animateScroll)
  }
  
  // 立即滚动到底部
  const instantScrollToBottom = () => {
    if (!containerRef.value) return
    
    isAutoScrolling.value = true
    containerRef.value.scrollTop = containerRef.value.scrollHeight
    
    // 短暂延迟后重置状态
    setTimeout(() => {
      isAutoScrolling.value = false
    }, 100)
  }
  
  // 主要的滚动方法
  const scrollTo = (scenario = SCROLL_SCENARIOS.SMART, options = {}) => {
    const {
      smooth = true,
      force = false,
      delay = 0
    } = options
    
    const executeScroll = () => {
      if (!containerRef.value) return
      
      switch (scenario) {
        case SCROLL_SCENARIOS.FORCE:
          // 强制滚动，无论用户在哪里
          if (smooth) {
            smoothScrollToBottom(200)
          } else {
            instantScrollToBottom()
          }
          break
          
        case SCROLL_SCENARIOS.SMART:
          // 智能滚动，只有在底部附近才滚动
          if (force || checkIsNearBottom()) {
            if (smooth) {
              smoothScrollToBottom(300)
            } else {
              instantScrollToBottom()
            }
          }
          break

        case SCROLL_SCENARIOS.FOLLOW:
          // 跟随滚动，用于流式输出
          if (!isUserScrolling.value && checkIsNearBottom(100)) {
            // 防抖处理，避免频繁滚动
            if (followScrollTimer) {
              clearTimeout(followScrollTimer)
            }

            followScrollTimer = setTimeout(() => {
              if (smooth) {
                smoothScrollToBottom(150)
              } else {
                instantScrollToBottom()
              }
            }, 50)
          }
          break
          
        case SCROLL_SCENARIOS.PRESERVE:
          // 保持位置，不滚动
          break
          
        default:
          console.warn('Unknown scroll scenario:', scenario)
      }
    }
    
    if (delay > 0) {
      setTimeout(executeScroll, delay)
    } else {
      nextTick(executeScroll)
    }
  }
  
  // 防抖滚动
  const debouncedScroll = (scenario, options = {}, debounceMs = 100) => {
    if (scrollDebounceTimer) {
      clearTimeout(scrollDebounceTimer)
    }
    
    scrollDebounceTimer = setTimeout(() => {
      scrollTo(scenario, options)
    }, debounceMs)
  }
  
  // 初始化滚动监听
  const initScrollListener = () => {
    if (!containerRef.value) return

    // 初始化当前滚动位置
    currentScrollTop.value = containerRef.value.scrollTop
    lastScrollTop.value = containerRef.value.scrollTop

    containerRef.value.addEventListener('scroll', detectUserScroll, { passive: true })
  }
  
  // 清理资源
  const cleanup = () => {
    if (userScrollTimer.value) {
      clearTimeout(userScrollTimer.value)
    }
    if (scrollDebounceTimer) {
      clearTimeout(scrollDebounceTimer)
    }
    if (followScrollTimer) {
      clearTimeout(followScrollTimer)
    }
    
    if (containerRef.value) {
      containerRef.value.removeEventListener('scroll', detectUserScroll)
    }
  }
  
  return {
    // 状态
    isUserScrolling,
    isNearBottom,
    
    // 方法
    scrollTo,
    debouncedScroll,
    initScrollListener,
    cleanup,
    
    // 便捷方法
    forceScrollToBottom: (smooth = true) => scrollTo(SCROLL_SCENARIOS.FORCE, { smooth }),
    smartScrollToBottom: (smooth = true) => scrollTo(SCROLL_SCENARIOS.SMART, { smooth }),
    followScrollToBottom: (smooth = false) => scrollTo(SCROLL_SCENARIOS.FOLLOW, { smooth }),
  }
}
