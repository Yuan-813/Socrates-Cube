# SenseNova-U1 信息图生成技能

## 描述
调用 SenseNova-U1-8B-MoT-Infographic-V3 模型生成高质量计算机网络教学信息图。
U1 系列是商汤科技开源的原生多模态统一模型，Infographic-V3 (2026-07-16 最新发布) 在密集信息图排版、文本渲染方面达到开源 SoTA。

**V3 新增编辑能力**：
- 局部文字编辑：修改信息图中的单个文本元素
- 内容编辑：替换/补充指定区域的内容
- 版式编辑：调整布局、字体、配色方案
- 全局风格转换：维持内容不变，一键切换风格模板
官方仓库：https://github.com/OpenSenseNova/SenseNova-U1

## 触发场景
- 用户要求"生成信息图"、"画一张拓扑图"、"可视化XX协议"
- DiagnosisAgent 触发 infographic 资源类型时
- ResourceGeneratorAgent 需要视觉化教学材料

## 核心能力
| 模型 | 特点 | 适用场景 |
|------|------|---------|
| U1-8B-MoT-Infographic-V3 | 信息图生成+编辑，支持局部文字/内容/版式编辑 | 协议栈图、知识点总结卡片 |
| U1-8B-MoT-Interleaved | 图文交织生成 | 带图解的知识文档 |
| U1-8B-MoT | 通用T2I+理解 | 网络拓扑示意图 |

## API 调用方式

### 通过 Socrates-Cube 后端接口（推荐）
```bash
POST /api/v1/media/generate-image
{
  "prompt": "TCP三次握手握手流程信息图，包含SYN/SYN-ACK/ACK步骤、状态机转换、RFC 9293标注",
  "style": "infographic",
  "knowledge_point": "TCP三次握手"
}
```

### 直接调用 SenseNova API
```python
import requests

resp = requests.post(
    "https://api.sensecore.cn/v1/images/generations",
    headers={"Authorization": f"Bearer {SENOVAU1_API_KEY}"},
    json={
        "model": "SenseNova-U1-8B-MoT-Infographic-V3",
        "prompt": "计算机网络OSI七层模型教学信息图，专业简洁风格",
        "size": "1024x768",
        "n": 1,
    }
)
image_url = resp.json()["data"][0]["url"]
```

## 推荐 Prompt 模板（计算机网络方向）

### 协议栈信息图
```
{协议名}协议{知识点}教学信息图，包含：
1. 报文格式字段（位宽标注）
2. 状态机流程（箭头+状态）
3. 常见误解提示（红色警示框）
4. RFC标准引用
简洁专业风格，蓝白色调
```

### 对比图
```
{协议 A} vs {协议 B} 对比信息图，
左右分栏，相同维度对比，
突出核心差异，适合教学展示
```

### 网络拓扑图（topology 样式 - V3 新增）
```
企业网络拓扑信息图：
节点：客户机(PC)、交换机(Switch)、路由器(Router)、防火墙(Firewall)、服务器(Server)
层次：入文层→汇聚层→核心层
链路标注：IP地址段、带宽、VLAN编号
风格：网络设备通用图标，青灰色调，对齐专业
```

### 报文格式图（packet 样式 - V3 新增）
```
{PDU 名称} 报文格式图，包含：
- 字段名称与位宽标注（按标准 RFC 定义）
- 必填字段用蓝色列出，可选字段用浅灰色
- 典型取値示例标注在字段下方
- 验错字段用红色标出，标注计算公式
- RFC 标准编号标注在图下方
```

### V3 局部编辑 Prompt 空模板
```
[编辑指令]将图中 "{原文字}" 修改为 "{新文字}"，
保持周围布局、字体和配色不变
```

## 在 generate_media.py 中的集成位置
- 文件：`src/loopse/api/generate_media.py`
- 函数：`generate_image()`
- 模型变量：`SENOVAU1_MODEL_INFOGRAPHIC = "SenseNova-U1-8B-MoT-Infographic-V3"`

## 环境配置
```env
# .env 中配置
SENOVAU1_API_KEY=your_key_here
SENOVAU1_BASE_URL=https://api.sensecore.cn/v1
SENOVAU1_MODEL=SenseNova-U1-8B-MoT-Infographic-V3
```
