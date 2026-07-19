# 讯飞超拟人语音合成 - WebSocket API 接入

## 接入方式

本项目已改为使用**讯飞超拟人语音合成 WebSocket API** 直接通信，不依赖任何本地 SDK 文件。

### 技术方案

- **语音合成**：通过 WebSocket 直连讯飞 TTS 服务 (`wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6`)
- **鉴权方式**：HMAC-SHA256 签名生成鉴权 URL 参数
- **音频格式**：MP3 (lame 编码，24kHz 采样率)
- **口型同步**：Web Audio API 频谱分析 + CSS 动画

### 相关文件

- `src/composables/useVirtualTeacher.ts` — WebSocket TTS 连接、音频播放、振幅分析
- `src/components/VirtualTeacherPanel.vue` — 虚拟教师 UI 组件（SVG 动画头像 + 口型同步）

### 环境变量

```env
VITE_XUNFEI_DH_APPID=你的AppID
VITE_XUNFEI_DH_API_KEY=你的APIKey
VITE_XUNFEI_DH_API_SECRET=你的APISecret
```

### 发音人

默认使用 `x6_lingxiaoxuan_flow`（聆小璇，女声），可通过后端 `/api/v1/virtual-teacher/voices` 查看全部可用发音人。

## 旧方案说明

此目录原用于存放 VMS Web SDK 文件（vms.js），但讯飞超拟人数字人交互服务的 Web SDK 实际不可用（控制台无 JavaScript SDK 下载选项）。已改为纯 WebSocket API 方案。
