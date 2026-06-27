type SearchBarProps = {
    query: string;
    topK: number;
    includeWatched: boolean;
    useLlmExplanations: boolean;
    useLlmIntent: boolean;
    enforceHardConstraints: boolean;
    useLlmReranker: boolean;
    includeAgentTrace: boolean;
    isLoading: boolean;
    onQueryChange: (query: string) => void;
    onTopKChange: (topK: number) => void;
    onIncludeWatchedChange: (includeWatched: boolean) => void;
    onEnforceHardConstraintsChange: (enforceHardConstraints: boolean) => void;
    onUseLlmExplanationsChange: (useLlmExplanations: boolean) => void;
    onUseLlmIntentChange: (useLlmIntent: boolean) => void;
    onUseLlmRerankerChange: (useLlmReranker: boolean) => void;
    onIncludeAgentTraceChange: (includeAgentTrace: boolean) => void;
    onSubmit: () => void;
};

const EXAMPLE_QUERIES = [
  "I want something like Her, lonely and futuristic, but not too slow",
  "A dark psychological thriller with obsession and mystery",
  "A funny comfort movie about friendship and family",
  "An epic fantasy adventure with battles and magical worlds",
  "A quiet emotional sci-fi movie about memory and identity",
];

export function SearchBar({
    query,
    topK,
    includeWatched,
    useLlmExplanations,
    useLlmIntent,
    enforceHardConstraints,
    useLlmReranker,
    includeAgentTrace,
    isLoading,
    onQueryChange,
    onTopKChange,
    onIncludeWatchedChange,
    onEnforceHardConstraintsChange,
    onUseLlmExplanationsChange,
    onUseLlmIntentChange,
    onUseLlmRerankerChange,
    onIncludeAgentTraceChange,
    onSubmit,
}: SearchBarProps) {
    function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        onSubmit();
    }

    return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl">
      <div className="mb-5">
        <p className="mb-2 text-sm font-medium uppercase tracking-[0.25em] text-cyan-400">
          Natural-language movie search
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-100 md:text-5xl">
          What do you want to watch?
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">
          Describe the mood, style, pacing, genre, or a reference movie. The
          backend will retrieve semantically similar movies from your vector
          database.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Example: I want a lonely, gentle sci-fi movie like Her but not too slow..."
          className="min-h-32 w-full resize-none rounded-2xl border border-slate-700 bg-slate-950 p-4 text-base text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400"
        />

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <label className="flex items-center gap-3 text-sm text-slate-300">
              Top K
              <select
                value={topK}
                onChange={(event) => onTopKChange(Number(event.target.value))}
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-cyan-400"
              >
                {[3, 5, 8, 10].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={includeWatched}
                onChange={(event) => onIncludeWatchedChange(event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-cyan-400 focus:ring-cyan-400"
              />
              Include watched movies
            </label>
            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={useLlmIntent}
                onChange={(event) => onUseLlmIntentChange(event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-cyan-400 focus:ring-cyan-400"
              />
              Use LLM intent parser
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={enforceHardConstraints}
                onChange={(event) =>
                  onEnforceHardConstraintsChange(
                    event.target.checked
                  )
                }
                className="h-4 w-4 rounded border-slate-700 bg-slate-950"
              />

              Enforce exact metadata constraints
            </label>
            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={useLlmReranker}
                onChange={(event) => onUseLlmRerankerChange(event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-cyan-400 focus:ring-cyan-400"
              />
              Use LLM reranker
            </label>
            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={useLlmExplanations}
                onChange={(event) => onUseLlmExplanationsChange(event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-cyan-400 focus:ring-cyan-400"
              />
              Use LLM explanations
            </label>
            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={includeAgentTrace}
                onChange={(event) => onIncludeAgentTraceChange(event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-950 text-cyan-400 focus:ring-cyan-400"
              />
              Show agent execution trace
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading || query.trim().length < 2}
            className="rounded-xl bg-cyan-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "Searching..." : "Recommend Movies"}
          </button>
        </div>
      </form>

      <div className="mt-5">
        <p className="mb-3 text-sm font-medium text-slate-300">
          Try an example:
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => onQueryChange(example)}
              className="rounded-full border border-slate-700 px-3 py-2 text-xs text-slate-300 transition hover:border-cyan-400 hover:text-cyan-300"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}