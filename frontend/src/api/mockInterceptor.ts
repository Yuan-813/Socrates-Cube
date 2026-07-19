/**
 * 前端 Mock 拦截器
 * 当 VITE_MOCK_MODE=true 时，拦截所有 API 请求并返回本地 Mock 数据
 */
import type { AxiosInstance } from 'axios'
import { mockProfile, mockDiagnosis, mockResources, mockPath, mockLogs } from './mock'

const IS_MOCK = import.meta.env.VITE_MOCK_MODE === 'true'

const mockChallengerStart = {
  status: 'active' as const,
  session_id: 'mock-session-001',
  round: 1,
  max_rounds: 5,
  question: 'TCP 三次握手中，如果第三次 ACK 丢失，会发生什么？',
  question_type: 'scenario',
  topic: 'TCP 三次握手',
  correct_answer_hint: '服务端会重传 SYN+ACK，连接未完全建立',
  distractor_explanation: '误认为服务端发出 SYN+ACK 即算连接建立',
}

/** 模拟延迟 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 安装 Mock 拦截器到 axios 实例
 */
export function installMockInterceptor(client: AxiosInstance) {
  if (!IS_MOCK) return

  console.info('[Mock Mode] 前端 Mock 拦截器已启用')

  client.interceptors.request.use(async (config) => {
    const url = config.url || ''

    // 健康检查
    if (url.includes('/health')) {
      return { ...config, adapter: () => Promise.resolve({ data: { status: 'ok' }, status: 200, statusText: 'OK', headers: {}, config }) }
    }

    // 画像接口
    if (url.includes('/api/v1/profile')) {
      await delay(300)
      return { ...config, adapter: () => Promise.resolve({ data: mockProfile, status: 200, statusText: 'OK', headers: {}, config }) }
    }

    // 学习路径接口
    if (url.includes('/api/v1/path/plan') || url.includes('/api/v1/path')) {
      await delay(400)
      return { ...config, adapter: () => Promise.resolve({ data: { nodes: mockPath, total_nodes: mockPath.length }, status: 200, statusText: 'OK', headers: {}, config }) }
    }

    // 资源生成接口
    if (url.includes('/api/v1/resources/generate-all')) {
      await delay(600)
      return {
        ...config,
        adapter: () => Promise.resolve({
          data: {
            knowledge_point: 'TCP 三次握手',
            docs: mockResources.filter(r => r.type === 'document'),
            exercise: mockResources.filter(r => r.type === 'quiz'),
            code: mockResources.filter(r => r.type === 'code'),
            mindmap: mockResources.filter(r => r.type === 'mindmap'),
            script: mockResources.filter(r => r.type === 'video'),
            total_resources: mockResources.length,
          },
          status: 200, statusText: 'OK', headers: {}, config,
        }),
      }
    }

    if (url.includes('/api/v1/resources/generate')) {
      await delay(400)
      return { ...config, adapter: () => Promise.resolve({ data: mockResources[0], status: 200, statusText: 'OK', headers: {}, config }) }
    }

    if (url.includes('/api/v1/resources')) {
      await delay(300)
      return { ...config, adapter: () => Promise.resolve({ data: mockResources, status: 200, statusText: 'OK', headers: {}, config }) }
    }

    // 日志接口
    if (url.includes('/api/v1/logs')) {
      await delay(200)
      return { ...config, adapter: () => Promise.resolve({ data: mockLogs, status: 200, statusText: 'OK', headers: {}, config }) }
    }

    // Challenger 接口
    if (url.includes('/api/v1/challenger/start')) {
      await delay(350)
      return {
        ...config,
        adapter: () => Promise.resolve({
          data: { status: 'ok', challenge: mockChallengerStart },
          status: 200, statusText: 'OK', headers: {}, config,
        }),
      }
    }

    if (url.includes('/api/v1/challenger/evaluate')) {
      await delay(400)
      return {
        ...config,
        adapter: () => Promise.resolve({
          data: {
            status: 'ok',
            result: {
              status: 'completed',
              round: 1,
              is_correct: true,
              feedback: '回答抓住了第三次 ACK 防止半开连接的关键作用。',
              understanding_level: '良好',
              understanding_score: 85,
              suggestions: ['可以尝试用 Wireshark 观察重传行为', '进入协议仿真巩固流程直觉'],
              total_rounds: 1,
              correct_count: 1,
            },
          },
          status: 200, statusText: 'OK', headers: {}, config,
        }),
      }
    }

    if (url.includes('/api/v1/simulator')) {
      await delay(250)
      return {
        ...config,
        adapter: () => Promise.resolve({
          data: { scenarios: ['three_way_handshake', 'four_way_wavehand', 'sliding_window'] },
          status: 200, statusText: 'OK', headers: {}, config,
        }),
      }
    }

    // 联通测试
    if (url.includes('/api/v1/chat/test')) {
      return { ...config, adapter: () => Promise.resolve({ data: { status: 'ok', mock: true }, status: 200, statusText: 'OK', headers: {}, config }) }
    }

    // 默认放行
    return config
  })
}

/**
 * 判断当前是否处于 Mock 模式
 */
export function isMockMode(): boolean {
  return IS_MOCK
}

/**
 * Mock SSE 流式输出：使用 setInterval 模拟逐 token 推送
 * 返回 AbortController 供调用方取消
 */
export function mockStreamChat(
  message: string,
  onEvent: (payload: any) => void,
  onDone: () => void,
  _onError?: (err: Error) => void,
): AbortController {
  const controller = new AbortController()

  // 预设回复文本
  const replyText = generateMockReply(message)

  // 1. Orchestrator 启动
  setTimeout(() => {
    if (controller.signal.aborted) return
    onEvent({ event: 'agent_start', agent_name: 'Orchestrator', data: { message: '开始理解问题与规划协作流程' } })
    onEvent({ event: 'state_change', agent_name: 'Orchestrator', data: { from: 'idle', to: 'learning', message: '进入学习模式' } })
  }, 80)

  // 2. Retriever 检索
  setTimeout(() => {
    if (controller.signal.aborted) return
    onEvent({ event: 'agent_start', agent_name: 'Retriever', data: { message: '检索知识库、协议片段和知识图谱' } })
    onEvent({ event: 'tool_call', agent_name: 'Retriever', data: { tool_name: 'hybrid_retrieval', input: message.slice(0, 120), status: 'calling' } })
  }, 200)

  setTimeout(() => {
    if (controller.signal.aborted) return
    onEvent({ event: 'tool_call', agent_name: 'Retriever', data: { tool_name: 'hybrid_retrieval', status: 'completed', result_count: 5 } })
    onEvent({ event: 'agent_end', agent_name: 'Retriever', data: { message: '检索完成，命中文档 3 条、图谱节点 2 个' } })
  }, 600)

  // 3. Diagnosis 三层诊断
  setTimeout(() => {
    if (controller.signal.aborted) return
    onEvent({ event: 'agent_start', agent_name: 'Diagnosis', data: { message: '执行三层错误诊断' } })
    onEvent({ event: 'tool_call', agent_name: 'Diagnosis', data: { tool_name: 'three_layer_diagnosis', input: message.slice(0, 120), status: 'calling' } })
  }, 700)

  setTimeout(() => {
    if (controller.signal.aborted) return
    onEvent({ event: 'tool_call', agent_name: 'Diagnosis', data: { tool_name: 'three_layer_diagnosis', status: 'completed', is_correct: mockDiagnosis.is_correct } })
    onEvent({ event: 'diagnosis', agent_name: 'Diagnosis', data: mockDiagnosis })
    onEvent({ event: 'agent_end', agent_name: 'Diagnosis', data: { message: '诊断完成', is_correct: mockDiagnosis.is_correct } })
  }, 1200)

  // 4. 流式输出主回复 (token 事件)
  setTimeout(() => {
    if (controller.signal.aborted) return
    onEvent({ event: 'agent_start', agent_name: 'Orchestrator', data: { message: '生成可追问的主回复' } })
  }, 1300)

  let charIndex = 0
  const tokenInterval = setInterval(() => {
    if (controller.signal.aborted) {
      clearInterval(tokenInterval)
      return
    }
    if (charIndex < replyText.length) {
      const chunkSize = Math.min(3, replyText.length - charIndex)
      const token = replyText.slice(charIndex, charIndex + chunkSize)
      onEvent({ event: 'token', agent_name: 'Orchestrator', data: { token } })
      charIndex += chunkSize
    } else {
      clearInterval(tokenInterval)

      onEvent({ event: 'agent_end', agent_name: 'Orchestrator', data: { message: '主回复完成' } })

      // 5. Profiler 画像更新
      setTimeout(() => {
        if (controller.signal.aborted) return
        onEvent({ event: 'agent_start', agent_name: 'Profiler', data: { message: '更新学习画像' } })
        onEvent({ event: 'agent_end', agent_name: 'Profiler', data: { message: '画像已更新', weak_points: ['kn_005'], turn_count: 9 } })
      }, 100)

      // 6. 资源生成
      setTimeout(() => {
        if (controller.signal.aborted) return
        onEvent({ event: 'agent_start', agent_name: 'ResourceGenerator', data: { message: '生成并持久化五类学习资源' } })
        onEvent({ event: 'resource', agent_name: 'ResourceGenerator', data: mockResources[0] })
        onEvent({ event: 'agent_end', agent_name: 'ResourceGenerator', data: { message: '五类资源生成完成，共 5 份' } })
      }, 300)

      // 7. 路径更新
      setTimeout(() => {
        if (controller.signal.aborted) return
        onEvent({ event: 'agent_start', agent_name: 'PathPlanner', data: { message: '基于画像和图谱生成路径' } })
        onEvent({ event: 'path_update', agent_name: 'PathPlanner', data: { nodes: mockPath } })
        onEvent({ event: 'agent_end', agent_name: 'PathPlanner', data: { message: '路径规划完成，共 6 个节点' } })
      }, 500)

      // 7.5 Challenger 检验（诊断错误时触发）
      if (!mockDiagnosis.is_correct) {
        setTimeout(() => {
          if (controller.signal.aborted) return
          onEvent({ event: 'agent_start', agent_name: 'Challenger', data: { message: '生成针对性误解检验题' } })
          onEvent({ event: 'challenger', agent_name: 'Challenger', data: mockChallengerStart })
          onEvent({ event: 'agent_end', agent_name: 'Challenger', data: { message: '第 1 轮检验题已生成', topic: mockChallengerStart.topic } })
        }, 600)
      }

      // 8. 状态回退 + done
      setTimeout(() => {
        if (controller.signal.aborted) return
        onEvent({ event: 'state_change', agent_name: 'Orchestrator', data: { from: 'learning', to: 'idle', message: '本轮对话完成' } })
        onEvent({ event: 'done', agent_name: 'Orchestrator', data: { session_id: 'mock-session-001', total_time_ms: 3200 } })
        onDone()
      }, 700)
    }
  }, 40)

  controller.signal.addEventListener('abort', () => {
    clearInterval(tokenInterval)
  })

  return controller
}

/** 根据输入生成 Mock 回复 */
function generateMockReply(message: string): string {
  if (message.includes('握手') || message.includes('三次')) {
    return `## TCP 三次握手过程

TCP 三次握手（Three-Way Handshake）是建立 TCP 连接的标准流程：

**第一次握手（SYN）**
客户端发送 SYN 报文，序列号 seq=x，进入 SYN_SENT 状态。

**第二次握手（SYN+ACK）**
服务端收到 SYN 后，回复 SYN+ACK 报文，seq=y，ack=x+1，进入 SYN_RCVD 状态。

**第三次握手（ACK）**
客户端收到 SYN+ACK 后，发送 ACK 报文，seq=x+1，ack=y+1，双方进入 ESTABLISHED 状态。

> 💡 **为什么需要三次而不是两次？**
> 第三次握手防止了历史重复连接的建立。如果只有两次握手，服务端无法确认客户端是否收到了 SYN+ACK，可能导致旧连接的 SYN 被当作新连接处理。

参考来源：[1] 谢希仁《计算机网络》第8版 第3章 [2] RFC 793 TCP 规范`
  }

  if (message.includes('HTTP') || message.includes('http')) {
    return `## HTTP 协议概述

HTTP（超文本传输协议）是应用层协议，基于 TCP 传输。

**请求-响应模型**
1. 客户端发送请求（Method + URL + Headers + Body）
2. 服务端返回响应（Status Code + Headers + Body）

**常见方法**
- GET：获取资源
- POST：提交数据
- PUT：更新资源
- DELETE：删除资源

**状态码分类**
- 2xx：成功（200 OK）
- 3xx：重定向（301 永久重定向）
- 4xx：客户端错误（404 Not Found）
- 5xx：服务端错误（500 Internal Server Error）

参考来源：[1] RFC 9110 HTTP Semantics [2] 谢希仁《计算机网络》第6章`
  }

  return `## 关于"${message}"的解答

这是一个很好的计算机网络问题。让我从以下几个方面来分析：

**核心概念**
在计算机网络中，理解协议分层模型是关键。TCP/IP 四层模型包括：应用层、传输层、网络层和数据链路层。

**详细解释**
每一层都有明确的职责分工：
- 应用层：定义应用之间的通信规则（HTTP、DNS、FTP）
- 传输层：提供端到端的可靠/不可靠传输（TCP、UDP）
- 网络层：负责路由选择和数据包转发（IP、ICMP）
- 数据链路层：在相邻节点间传输帧（Ethernet、PPP）

**总结**
理解每层协议的职责边界，是掌握计算机网络的核心基础。

参考来源：[1] 谢希仁《计算机网络》第8版 第1章`
}
