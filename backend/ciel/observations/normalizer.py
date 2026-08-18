from __future__ import annotations

from typing import Any


class ObservationNormalizer:
    def normalize(
        self,
        action: dict[str, Any],
        routed_action: dict[str, Any],
        tool_execution: dict[str, Any],
    ) -> dict[str, Any]:
        results = tool_execution.get("results") or []
        success = all(result.get("success") is True for result in results) if results else True
        summaries = [self._summarize_result(result) for result in results]
        return {
            "action": action,
            "routed_tools": routed_action.get("tools", []),
            "success": success,
            "summary": "\n".join(summary for summary in summaries if summary).strip(),
            "result_count": len(results),
            "raw_result_refs": [
                {
                    "tool": result.get("tool"),
                    "action": result.get("action"),
                    "success": result.get("success"),
                    "returnCode": result.get("returnCode"),
                    "statusCode": result.get("statusCode"),
                    "errorType": result.get("errorType"),
                }
                for result in results
            ],
        }

    def _summarize_result(self, result: dict[str, Any]) -> str:
        tool = result.get("tool", "tool")
        action = result.get("action", "")
        success = result.get("success") is True
        status = "succeeded" if success else "failed"
        output = result.get("output")
        if output is None and result.get("data") is not None:
            output = str(result["data"])
        if output is None:
            output = result.get("error", "")
        output = str(output or "").strip()
        if len(output) > 1200:
            output = output[:1200] + "\n[output truncated]"
        if output:
            return f"{tool}/{action} {status}:\n{output}"
        return f"{tool}/{action} {status}."
