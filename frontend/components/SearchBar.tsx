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
    <section className="surface-card rounded-[2rem] p-6 md:p-8">
      <div className="mb-6">
        <p className="eyebrow mb-2">Natural-language discovery</p>
        <h2 className="font-display text-3xl font-semibold text-[#352D22] md:text-5xl">
          Describe your perfect watch
        </h2>
        <p className="mt-3 max-w-2xl text-base leading-7 text-[#706453]">
          Share a mood, genre, pace, or a movie you already love. Your request
          stays grounded in the local movie catalog.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <textarea
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="For example: A gentle, futuristic love story that feels hopeful..."
          className="warm-field min-h-32 w-full resize-none rounded-2xl p-4 text-base leading-7 outline-none transition"
        />

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-[#706453]">
            Recommendations are ranked for relevance and personal fit.
          </p>
          <button
            type="submit"
            disabled={isLoading || query.trim().length < 2}
            className="primary-action rounded-full px-7 py-3 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? "Finding your movies..." : "Find my movies"}
          </button>
        </div>

        <details className="group rounded-2xl border border-[#BDB76B]/55 bg-[#FDFBD4]/55 p-4">
          <summary className="cursor-pointer font-semibold text-[#544835] transition hover:text-[#8A5B2B]">
            Advanced recommendation settings
          </summary>
          <div className="mt-5 grid gap-4 border-t border-[#BDB76B]/45 pt-5 sm:grid-cols-2 lg:grid-cols-3">
            <label className="flex items-center justify-between gap-3 text-sm text-[#544835]">
              Results to show
              <select
                value={topK}
                onChange={(event) => onTopKChange(Number(event.target.value))}
                className="warm-field warm-select rounded-xl px-3 py-2 outline-none"
              >
                {[3, 5, 8, 10].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-3 text-sm text-[#544835]">
              <input
                type="checkbox"
                checked={includeWatched}
                onChange={(event) => onIncludeWatchedChange(event.target.checked)}
                className="h-4 w-4 accent-[#CE8946]"
              />
              Include watched movies
            </label>
            <label className="flex items-center gap-3 text-sm text-[#544835]">
              <input
                type="checkbox"
                checked={useLlmIntent}
                onChange={(event) => onUseLlmIntentChange(event.target.checked)}
                className="h-4 w-4 accent-[#CE8946]"
              />
              Use LLM intent parser
            </label>
            <label className="flex items-center gap-3 text-sm text-[#544835]">
              <input
                type="checkbox"
                checked={enforceHardConstraints}
                onChange={(event) =>
                  onEnforceHardConstraintsChange(event.target.checked)
                }
                className="h-4 w-4 accent-[#CE8946]"
              />
              Enforce metadata constraints
            </label>
            <label className="flex items-center gap-3 text-sm text-[#544835]">
              <input
                type="checkbox"
                checked={useLlmReranker}
                onChange={(event) => onUseLlmRerankerChange(event.target.checked)}
                className="h-4 w-4 accent-[#CE8946]"
              />
              Use LLM reranker
            </label>
            <label className="flex items-center gap-3 text-sm text-[#544835]">
              <input
                type="checkbox"
                checked={useLlmExplanations}
                onChange={(event) => onUseLlmExplanationsChange(event.target.checked)}
                className="h-4 w-4 accent-[#CE8946]"
              />
              Use LLM explanations
            </label>
            <label className="flex items-center gap-3 text-sm text-[#544835]">
              <input
                type="checkbox"
                checked={includeAgentTrace}
                onChange={(event) => onIncludeAgentTraceChange(event.target.checked)}
                className="h-4 w-4 accent-[#CE8946]"
              />
              Show agent trace
            </label>
          </div>
        </details>
      </form>

      <div className="mt-6 border-t border-[#BDB76B]/40 pt-5">
        <p className="mb-3 text-sm font-semibold text-[#625845]">
          Need inspiration? Try one of these:
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => onQueryChange(example)}
              className="rounded-full border border-[#BDB76B]/80 bg-[#FFFDF0]/65 px-3 py-2 text-xs text-[#625845] transition hover:border-[#CE8946] hover:bg-[#CE8946]/10 hover:text-[#68411F]"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
