# Socrates-Cube 7 分钟演示脚本

## 0:00-0:30 开场

介绍系统定位：Socrates-Cube 面向《计算机网络》课程，通过多智能体协作完成“诊断、资源、路径、画像”一体化辅导。打开首页后进入对话页面，说明右侧面板包含画像、资源、路径和日志。

## 0:30-2:30 诊断与追问

输入：“TCP 握手只需要两次就够了吧？”观察 AgentStatusBar 依次出现 Orchestrator、Retriever、Diagnosis。展示诊断卡片：错误类型为流程遗漏或事实错误，指出第三次 ACK 的意义。旁白强调系统不是直接给答案，而是用失效连接请求的反例进行苏格拉底式追问。

## 2:30-3:40 资源生成

继续输入：“给我生成一道 TCP 三次握手练习题。”右侧资源页展示 ExerciseCard。说明 ResourceGenerator 会结合知识库证据、诊断结果和难度生成资源，并把资源写入数据库。

## 3:40-4:50 路径规划

切换到“路径”标签页。展示 PathTimeline 中的节点顺序、掌握度、预计时间。点击一个节点，打开 PathReasonModal，说明推荐理由来自知识图谱前置依赖、画像掌握度和薄弱点优先级。

## 4:50-5:50 学习画像

切换到“画像”标签页，展示八维雷达图。说明 Profiler 根据每轮对话和诊断结果更新 mastery_map、weak_points、strong_points，用于下一轮路径和资源推荐。

## 5:50-6:40 Agent 日志

切换到“日志”标签页，展示 Retriever、Diagnosis、Profiler、ResourceGenerator、PathPlanner 的运行日志。强调每个 Agent 都有 trace，便于验收、调试和答辩说明。

## 6:40-7:00 总结

总结三点创新：三层认知诊断、多源知识库检索、可解释学习路径。若线上 LLM 或 ChromaDB 不可用，系统仍可用 Mock LLM 和本地 KB 索引完成离线演示。
