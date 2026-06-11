"""Reusable cognitive workflow primitives for higher-level agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ReasoningStep:
    name: str
    observation: str
    decision: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


@dataclass
class AgentTrace:
    goal: str
    steps: list[ReasoningStep] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    def add_step(
        self,
        name: str,
        observation: str,
        decision: str,
        confidence: float = 0.7,
        evidence: list[str] | None = None,
    ) -> None:
        self.steps.append(
            ReasoningStep(
                name=name,
                observation=observation,
                decision=decision,
                confidence=max(0.0, min(1.0, confidence)),
                evidence=evidence or [],
            )
        )

    def add_tool_call(self, tool: str, args: dict[str, Any], result_summary: str) -> None:
        self.tool_calls.append({"tool": tool, "args": args, "result_summary": result_summary})

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [step.__dict__ for step in self.steps],
            "tool_calls": self.tool_calls,
        }


class CognitiveAgentMixin:
    """Adds plan-act-reflect behavior without depending on a specific LLM provider."""

    def make_trace(self, goal: str) -> AgentTrace:
        return AgentTrace(goal=goal)

    def reflect(self, trace: AgentTrace, quality_checks: dict[str, bool]) -> dict[str, Any]:
        passed = [name for name, ok in quality_checks.items() if ok]
        failed = [name for name, ok in quality_checks.items() if not ok]
        confidence = len(passed) / max(1, len(quality_checks))
        trace.add_step(
            "self_reflection",
            f"passed={passed}; failed={failed}",
            "accept" if not failed else "revise_or_warn",
            confidence,
        )
        return {"passed": passed, "failed": failed, "confidence": confidence}

    def use_tool(
        self,
        trace: AgentTrace,
        tool_name: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        result = fn(*args, **kwargs)
        summary = str(result)
        if len(summary) > 180:
            summary = summary[:177] + "..."
        trace.add_tool_call(tool_name, {"args": args, "kwargs": kwargs}, summary)
        return result


class AwaitableDict(dict):
    """A dict that can also be awaited by legacy async tests."""

    def __await__(self):
        async def _wrap():
            return self

        return _wrap().__await__()
