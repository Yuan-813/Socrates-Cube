/**
 * 全局动画配置常量
 * 集中管理所有动画参数，确保风格一致
 */

export const ANIMATION = {
  /** 分屏过渡动画 */
  splitTransition: {
    slideInDuration: 800,
    holdDuration: 400,
    slideOutDuration: 800,
    bufferDelay: 400,
    totalDuration: 2400,
    easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
  /** 翻页动画 */
  flipPage: {
    duration: 800,
    maxShadowOpacity: 0.5,
  },
  /** 通知动画 */
  notification: {
    showDuration: 3000,
    fadeInDuration: 500,
    fadeOutDuration: 400,
  },
} as const

/** 项目主题色 */
export const THEME = {
  primaryGradient: 'linear-gradient(135deg, #3b82f6, #6366f1)',
  darkBg: 'linear-gradient(135deg, #0a0e27 0%, #1a1040 50%, #0d1b3e 100%)',
  accentGold: '#f59e0b',
} as const
