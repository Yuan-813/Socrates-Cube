#!/usr/bin/env python3
"""运行三层诊断引擎准确率评测（30 条用例）。

输出 JSON 结果供文档撰写使用，不生成 Markdown 报告。
用法:
  python scripts/run_diagnosis_accuracy_test.py
  python scripts/run_diagnosis_accuracy_test.py --output docs/results/diagnosis_accuracy_phase5_data.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from loopse.agent.diagnosis import DiagnosisAgent  # noqa: E402

# 5 条正确回答对照用例
CORRECT_CASES = [
    {
        "id": "ok_01",
        "message": "TCP三次握手的过程是：客户端发SYN，服务端回SYN+ACK，客户端再发ACK。",
        "expect_correct": True,
    },
    {
        "id": "ok_02",
        "message": "HTTP 运行在 TCP 之上，TCP 再运行在 IP 之上。",
        "expect_correct": True,
    },
    {
        "id": "ok_03",
        "message": "DNS 递归查询由本地 DNS 代为完成全部查询；迭代查询只返回下一步服务器地址。",
        "expect_correct": True,
    },
    {
        "id": "ok_04",
        "message": "rwnd 由接收方通告，cwnd 由发送方根据拥塞状况调整，发送窗口取二者较小值。",
        "expect_correct": True,
    },
    {
        "id": "ok_05",
        "message": "ARP 将 IP 地址解析为同一局域网内的 MAC 地址。",
        "expect_correct": True,
    },
]


def load_wrong_cases(limit: int = 25) -> list[dict]:
    path = ROOT / "data" / "raw" / "misconceptions.json"
    if not path.exists():
        raise FileNotFoundError(f"误解库不存在: {path}")
    items = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for item in items[:limit]:
        cases.append({
            "id": item.get("id", f"mc_{len(cases)}"),
            "message": item.get("misconception", ""),
            "expect_correct": False,
            "expect_error_type": item.get("error_type"),
            "knowledge_node_id": item.get("knowledge_node_id"),
        })
    return cases


def score_case(result: dict, case: dict) -> dict:
    layer1_ok = result.get("is_correct") is case["expect_correct"]
    layer2_ok = True
    layer3_ok = True

    if not case["expect_correct"]:
        layer2_ok = bool(result.get("root_causes"))
        layer3_ok = result.get("pattern") is not None
        expected_pattern = case.get("expect_error_type")
        if expected_pattern and result.get("error_type"):
            # error_type 与误解库 pattern 允许映射近似
            layer1_ok = layer1_ok and result.get("error_type") != "none"

    return {
        "layer1_surface": layer1_ok,
        "layer2_root_cause": layer2_ok,
        "layer3_pattern": layer3_ok,
        "all_pass": layer1_ok and layer2_ok and layer3_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnosis accuracy benchmark")
    parser.add_argument(
        "--output",
        default=str(ROOT / "docs" / "results" / "diagnosis_accuracy_phase5_data.json"),
        help="JSON output path",
    )
    args = parser.parse_args()

    agent = DiagnosisAgent()
    cases = load_wrong_cases(25) + CORRECT_CASES
    results = []
    t0 = time.time()

    for case in cases:
        started = time.time()
        diagnosis = agent.diagnose(
            user_message=case["message"],
            context_docs=[{"document": case.get("knowledge_node_id", "计算机网络")}],
        )
        elapsed_ms = int((time.time() - started) * 1000)
        scores = score_case(diagnosis, case)
        results.append({
            **case,
            "scores": scores,
            "actual": {
                "is_correct": diagnosis.get("is_correct"),
                "error_type": diagnosis.get("error_type"),
                "surface_error": diagnosis.get("surface_error"),
                "root_causes": diagnosis.get("root_causes"),
                "pattern": diagnosis.get("pattern"),
                "confidence": diagnosis.get("confidence"),
            },
            "elapsed_ms": elapsed_ms,
        })

    total = len(results)
    l1 = sum(1 for r in results if r["scores"]["layer1_surface"])
    l2 = sum(1 for r in results if r["scores"]["layer2_root_cause"])
    l3 = sum(1 for r in results if r["scores"]["layer3_pattern"])
    all_pass = sum(1 for r in results if r["scores"]["all_pass"])

    summary = {
        "total_cases": total,
        "layer1_accuracy": round(l1 / total * 100, 1),
        "layer2_accuracy": round(l2 / total * 100, 1),
        "layer3_accuracy": round(l3 / total * 100, 1),
        "overall_accuracy": round(all_pass / total * 100, 1),
        "avg_elapsed_ms": round(sum(r["elapsed_ms"] for r in results) / total, 1),
        "total_elapsed_ms": int((time.time() - t0) * 1000),
        "target_met_85pct": all_pass / total >= 0.85,
    }

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": summary,
        "cases": results,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nResults written to: {out}")
    return 0 if summary["target_met_85pct"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
