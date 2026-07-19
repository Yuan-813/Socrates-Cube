# Skill: 向证书模拟考试题库添加新题目

## 适用场景
- 扩充 HCIA / CCNA / 期末考试 / HCIP 题库
- 新增考试类型（如 CCNP、H3CNE、软考网络工程师）
- 题目纠错或更新答案

## 题库文件位置

```
data/certificate_exams.json
```

结构：
```json
{
  "exams": {
    "hcia_mock":           { "question_count": 30, "questions": [...] },
    "ccna_mock":           { "question_count": 30, "questions": [...] },
    "computer_network_exam": { "question_count": 30, "questions": [...] },
    "hcip_mock":           { "question_count": 10, "questions": [...] }
  }
}
```

## 题目格式规范

```json
{
  "id": "hcia_031",
  "type": "single",
  "question": "关于OSPF协议，以下描述正确的是？",
  "options": {
    "A": "OSPF是距离矢量路由协议",
    "B": "OSPF使用Dijkstra算法计算最短路径",
    "C": "OSPF不支持VLSM",
    "D": "OSPF的管理距离默认为110"
  },
  "answer": "B",
  "explanation": "OSPF是链路状态路由协议，使用SPF（Dijkstra）算法。管理距离默认为110（选项D也正确，若题目允许多选答案，请使用multi类型）。",
  "knowledge_point": "路由选择协议",
  "kp_node_id": "kp_010"
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 格式：`{exam_prefix}_{三位数序号}`，如 `hcia_031` |
| `type` | 是 | `single`（单选）/ `multi`（多选）/ `judge`（判断题） |
| `question` | 是 | 题干，建议 20-80 字 |
| `options` | 是 | 单选/多选必须有 A-D，判断题用 `{"A": "正确", "B": "错误"}` |
| `answer` | 是 | 单选为单个字母，多选为字母字符串如 `"ABC"` |
| `explanation` | 是 | 解析，至少 30 字，引用 RFC 或教材章节更好 |
| `knowledge_point` | 是 | 对应知识点名称，参考 `data/knowledge_graph.json` 中 `nodes` 的 `name` 字段 |
| `kp_node_id` | 是 | 对应 `data/knowledge_graph.json` 中节点 ID，如 `kp_010` |

## KP 节点 ID 速查

| kp_node_id | 知识点 |
|------------|--------|
| kp_001 | 计算机网络体系结构 |
| kp_003 | TCP/IP四层模型 |
| kp_005 | 传输层协议 |
| kp_007 | TCP可靠传输机制 |
| kp_008 | IP地址与子网划分 |
| kp_009 | IP路由原理 |
| kp_010 | 路由选择协议（OSPF/BGP/RIP） |
| kp_012 | 网络安全基础 |
| kp_013 | 应用层协议（HTTP/DNS/FTP） |
| kp_014 | 数据链路层 |
| kp_019 | 华为HCIA认证体系 |

## 批量添加题目的 Python 脚本

```python
import json
from pathlib import Path

path = Path("data/certificate_exams.json")
data = json.loads(path.read_text(encoding="utf-8"))

new_questions = [
    {
        "id": "hcia_031",
        "type": "single",
        "question": "你的题目",
        "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
        "answer": "A",
        "explanation": "解析说明...",
        "knowledge_point": "路由选择协议",
        "kp_node_id": "kp_010"
    }
]

data["exams"]["hcia_mock"]["questions"].extend(new_questions)
data["exams"]["hcia_mock"]["question_count"] = len(data["exams"]["hcia_mock"]["questions"])
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"题库已更新，HCIA现有 {data['exams']['hcia_mock']['question_count']} 道题")
```

## 添加全新考试类型

在 `data/certificate_exams.json` 的 `exams` 对象中添加：

```json
"h3cne_mock": {
  "name": "H3C 网络工程师认证模拟",
  "description": "H3CNE 认证核心考点模拟题，涵盖华三设备配置与协议原理",
  "question_count": 20,
  "time_limit_minutes": 90,
  "pass_score": 60,
  "cert_node_id": "kp_019",
  "questions": [...]
}
```

然后在 `frontend/src/views/ExamView.vue` 中确认图标映射：
```typescript
const examIcons: Record<string, string> = {
  // ...
  h3cne_mock: '🔴',
}
```

## 质量检查

添加完成后运行：
```powershell
python -c "
import json
data=json.load(open('data/certificate_exams.json',encoding='utf-8'))
for eid,exam in data['exams'].items():
    q=len(exam['questions']); m=exam.get('question_count',0)
    status='OK' if q==m else f'MISMATCH({q}!={m})'
    print(f'{eid}: {q}题 [{status}]')
"
```
