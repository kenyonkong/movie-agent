import type {
    AgentTrace, 
    AgentTraceStatus, 
} from "@/types/movie"

type AgentTracePanelProps = {
    trace: AgentTrace;
};

function statusLabel(status: AgentTraceStatus): string {
  if (status === "completed") {
    return "Completed";
  }

  if (status === "skipped") {
    return "Skipped";
  }

  return "Failed";
}

function statusClasses(status: AgentTraceStatus): string {
  if (status === "completed") {
    return "border-green-500/40 bg-green-500/10 text-green-300";
  }

  if (status === "skipped") {
    return "border-yellow-500/40 bg-yellow-500/10 text-yellow-300";
  }

  return "border-red-500/40 bg-red-500/10 text-red-300";
}


export function AgentTracePanel({
    trace,
}: AgentTracePanelProps) {
    return (
        <section className="mb-6 rounded-3xl border border-slate-800 bg-slate-900/70 p-5">
            <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                    <h3 className="text-lg font-bold text-slate-100">
                        MovieAgent Execution Trace
                    </h3>

                    <p className="mt-1 text-sm text-slate-400">
                        {trace.agent_name} · {trace.agent_version}
                    </p>
                </div>

                <span className="w-fit rounded-full border border-cyan-700 bg-cyan-950/40 px-3 py-1 text-xs text-cyan-200">
                    Total: {trace.total_duration_ms.toFixed(2)} ms
                </span>
            </div>

            <div className="space-y-3">
                {trace.steps.map((step, index) => (
                    <details
                        key={`${step.name}-${index}`}
                        className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4"
                    >
                        <summary className="cursor-pointer list-none">
                            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                                <div className="flex items-center gap-3">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-slate-300">
                                    {index + 1}
                                </span>

                                <span className="font-medium text-slate-200">
                                    {step.name}
                                </span>

                                <span
                                    className={`rounded-full border px-2 py-1 text-xs ${statusClasses(
                                        step.status
                                    )}`}
                                >
                                    {statusLabel(step.status)}
                                </span>
                                </div>

                                <span className="text-sm text-slate-400">
                                    {step.duration_ms.toFixed(2)} ms
                                </span>
                            </div>
                        </summary>

                        <pre className="mt-4 overflow-x-auto rounded-xl border border-slate-800 bg-slate-900 p-4 text-xs leading-6 text-slate-400">
                            {JSON.stringify(step.details, null, 2)}
                        </pre>
                    </details>
                ))}
            </div>
        </section>
    );
}