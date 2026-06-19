import time
from typing import Any

from app.db.schemas import AgentTrace, AgentTraceStep

class AgentTracer:
    """
    Collects a sanitized execution trace for one MovieAgent run.

    When disabled, methods still work but no steps are stored.
    This avoids scattering `if include_trace` checks throughout the agent.
    """

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.started_at = time.perf_counter()
        self.steps: list[AgentTraceStep] = []

    
    def start_step(self) -> float:
        """
        Return a high-resolution timestamp used to measure one step.
        """
        return time.perf_counter()
    

    def complete(
        self,
        name: str,
        started_at: float, 
        details: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled:
            return

        self.steps.append(
            AgentTraceStep(
                name=name,
                status="completed",
                duration_ms=self._elapsed_ms(started_at),
                details=details or {},
            )
        )
    

    def skip(
        self,
        name: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled:
            return

        step_details = {
            "reason": reason,
            **(details or {}), # unpack the details
        }
        self.steps.append(
            AgentTraceStep(
                name=name,
                status="skipped",
                duration_ms=0.0,
                details=step_details,
            )
        )

    
    def fail(
        self, 
        name: str,
        started_at: float,
        error: Exception,
    ) -> None:
        if not self.enabled:
            return

        self.steps.append(
            AgentTraceStep(
                name=name,
                status="failed",
                duration_ms=self._elapsed_ms(started_at),
                details={
                    "error_type": type(error).__name__,
                    "message": str(error)[0:200],  # Limit the message to 200 characters
                },
            )
        )


    def build(self) -> AgentTrace | None:
        if not self.enabled:
            return None
        
        total_duration_ms = (
            time.perf_counter() - self.started_at
        ) * 1000

        return AgentTrace(
            steps=self.steps,
            total_duration_ms=round(total_duration_ms, 2),
        )

    
    def _elapsed_ms(self, started_at: float) -> float:
        return round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )