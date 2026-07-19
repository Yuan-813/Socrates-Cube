/**
 * 浏览器特性检测工具
 * 用于动画降级决策
 */

/** 检测是否支持CSS 3D变换 */
export function supports3DTransforms(): boolean {
  if (typeof CSS === 'undefined') return false
  return CSS.supports('transform-style', 'preserve-3d')
}

/** 检测用户是否偏好减少动画 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** 检测是否为触摸设备 */
export function isTouchDevice(): boolean {
  if (typeof window === 'undefined') return false
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

/** 检测是否为移动端 */
export function isMobileViewport(): boolean {
  if (typeof window === 'undefined') return false
  return window.innerWidth < 768
}

/** 综合降级模式判断 */
export type AnimationMode = 'full' | 'reduced' | 'minimal'
export function getAnimationMode(): AnimationMode {
  if (prefersReducedMotion()) return 'minimal'
  if (!supports3DTransforms()) return 'reduced'
  return 'full'
}
