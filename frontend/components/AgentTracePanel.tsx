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
    return "border-[#9AA05B]/60 bg-[#BDB76B]/18 text-[#565A2D]";
  }

  if (status === "skipped") {
    return "border-[#D4AF37]/60 bg-[#D4AF37]/15 text-[#6A550F]";
  }

  return "border-[#B86B4B]/55 bg-[#CE8946]/12 text-[#814526]";
}


export function AgentTracePanel({
    trace,
}: AgentTracePanelProps) {
    return (
        <section className="surface-card mb-6 rounded-3xl p-5">
            <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                    <h3 className="font-display text-2xl font-semibold text-[#352D22]">
                        MovieAgent Execution Trace
                    </h3>

                    <p className="mt-1 text-sm text-[#706453]">
                        {trace.agent_name} · {trace.agent_version}
                    </p>
                </div>

                <span className="w-fit rounded-full border border-[#D4AF37]/65 bg-[#D4AF37]/12 px-3 py-1 text-xs font-semibold text-[#6A550F]">
                    Total: {trace.total_duration_ms.toFixed(2)} ms
                </span>
            </div>

            <div className="space-y-3">
                {trace.steps.map((step, index) => (
                    <details
                        key={`${step.name}-${index}`}
                        className="rounded-2xl border border-[#BDB76B]/55 bg-[#FDFBD4]/45 p-4"
                    >
                        <summary className="cursor-pointer list-none">
                            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                                <div className="flex items-center gap-3">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[#BDB76B]/25 text-xs font-semibold text-[#5E5A31]">
                                    {index + 1}
                                </span>

                                <span className="font-medium text-[#42382B]">
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

                                <span className="text-sm text-[#706453]">
                                    {step.duration_ms.toFixed(2)} ms
                                </span>
                            </div>
                        </summary>

                        <pre className="mt-4 overflow-x-auto rounded-xl border border-[#BDB76B]/55 bg-[#F5EDC5] p-4 text-xs leading-6 text-[#544835]">
                            {JSON.stringify(step.details, null, 2)}
                        </pre>
                    </details>
                ))}
            </div>
        </section>
    );
}
