"""LLM-backed agents/planners for domain-specific flows.

These components generate structured plans (tool calls) and must remain safe:
- strict JSON outputs
- allowlisted tools only
- validated inputs (Pydantic)
- deterministic execution (tools are executed by code, not by the LLM)
"""


