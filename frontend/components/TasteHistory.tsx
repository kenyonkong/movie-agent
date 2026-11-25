"use client";

import { useState } from "react";
import type { Evidence, ProfileReview, TasteProfile } from "@/types/taste-profile";

const date = (value: string) => new Intl.DateTimeFormat("en-US", {
  month: "short", year: "numeric", day: "numeric", timeZone: "UTC",
}).format(new Date(value));

function Sources({ items, reviews }: { items: Evidence[]; reviews: Map<number, ProfileReview> }) {
  const grouped = new Map<number, Evidence[]>();
  for (const item of items) {
    const group = grouped.get(item.review_id) ?? [];
    group.push(item);
    grouped.set(item.review_id, group);
  }
  return <ul className="mt-4 space-y-4">
    {[...grouped].map(([key, evidence]) => {
      const review = reviews.get(key);
      if (!review) return null;
      return <li key={key} className="border-l-2 border-[#BDB76B] pl-4">
        <strong>{review.title}</strong> <time className="text-sm text-[#706453]" dateTime={review.reviewed_on}>{date(review.reviewed_on)}</time>
        <blockquote className="mt-1 whitespace-pre-line">{review.original_body ?? evidence.map(e => e.quote).join(" … ")}</blockquote>
        {evidence.map(e => <p key={e.evidence_id} className="mt-1 text-sm text-[#625845]">
          <strong>{e.exception ? "Exception" : "Model interpretation"}</strong> · {e.interpretation}
        </p>)}
      </li>;
    })}
  </ul>;
}

export default function TasteHistory({ profile }: { profile: TasteProfile }) {
  const { reviews, history, aspects, evidence } = profile;
  const reviewMap = new Map(reviews.map(r => [r.review_id, r]));
  const byId = new Map(evidence.map(e => [e.evidence_id, e]));
  const distinctFilms = (items: Evidence[]) => new Set(items.map(item => item.review_id)).size;
  const periodForReview = new Map<number, number>();
  history.forEach((period, index) => {
    const start = history[index - 1]?.through ?? 0;
    reviews.slice(start, period.through).forEach(r => periodForReview.set(r.review_id, index));
  });
  const ranked = aspects.map(aspect => {
    const items = evidence.filter(e => e.aspect === aspect.key && !e.exception);
    const periods = new Set(items.map(e => periodForReview.get(e.review_id))).size;
    return { ...aspect, count: distinctFilms(items), periods };
  }).sort((a, b) => b.count - a.count);
  const [aspectKey, setAspect] = useState(ranked[0]?.key);
  const [periodIndex, setPeriod] = useState(history.length - 1);
  const [showAll, setShowAll] = useState(false);
  const current = history[history.length - 1];
  const aspect = ranked.find(a => a.key === aspectKey);
  const entries = evidence.filter(e => e.aspect === aspectKey);
  const periods = history.map((period, index) => {
    const start = history[index - 1]?.through ?? 0;
    const ids = new Set(reviews.slice(start, period.through).map(r => r.review_id));
    const items = entries.filter(e => ids.has(e.review_id));
    return { ...period, start, total: ids.size, items, count: distinctFilms(items.filter(e => !e.exception)),
      endDate: reviews[period.through - 1].reviewed_on };
  });
  const selected = periods[periodIndex];
  const maxRate = Math.max(0.01, ...periods.map(p => p.count / p.total));
  const recentIds = new Set(reviews.slice(-30).map(r => r.review_id));
  const recent = distinctFilms(entries.filter(e => !e.exception && recentIds.has(e.review_id)));
  const panel = "surface-card mt-6 rounded-3xl p-5 md:p-8";

  function summary(period: typeof current) {
    if (!period.findings.length) return <p className="mt-3">There is too little recurring evidence to summarize this period.</p>;
    return <>
      <p className="mt-4 max-w-prose font-display text-xl leading-relaxed">
        {period.findings.map(f => f.sentence).join(" ")}
      </p>
      <details className="mt-4">
        <summary className="cursor-pointer font-semibold text-[#775321]">Why we think this</summary>
        {period.findings.map(f => <details key={f.sentence} className="mt-4">
          <summary className="cursor-pointer font-semibold">{f.sentence}</summary>
          <Sources items={f.supporting.flatMap(id => byId.get(id) ?? [])} reviews={reviewMap} />
        </details>)}
      </details>
    </>;
  }

  return <>
    <section className={panel}>
      <h2 className="font-display text-3xl">Your taste today</h2>
      {summary(current)}
    </section>
    {aspect && <>
      <section className={panel}>
        <h2 className="font-display text-3xl">Recurring likes and dislikes</h2>
        <p className="mt-2 text-sm text-[#706453]">Bubble area shows how many films support a preference. Select one to explore it over time.</p>
        <div className="mt-5 grid gap-6 sm:grid-cols-2">
          {(["like", "dislike"] as const).map(direction => {
            const group = ranked.filter(a => a.direction === direction);
            const visible = showAll ? group : group.slice(0, 4);
            return <div key={direction}>
              <h3 className="font-display text-2xl">{direction === "like" ? "Likes" : "Dislikes"}</h3>
              <div className="mt-2 grid gap-1">
                {visible.map(a => {
                  const diameter = 48 * Math.sqrt(a.count / ranked[0].count);
                  return <button key={a.key} type="button" aria-pressed={a.key === aspectKey}
                    onClick={() => setAspect(a.key)}
                    className="flex items-center gap-3 rounded-xl border border-transparent px-2 py-1 text-left hover:bg-[#BDB76B]/15 aria-pressed:border-[#AB925B] aria-pressed:bg-[#F5EDC5]">
                    <span className="grid h-12 w-12 shrink-0 place-items-center" aria-hidden="true">
                      <span className="rounded-full" style={{width: diameter, height: diameter,
                        backgroundColor: direction === "like" ? "#9DAD71" : "#CA8D5D"}} />
                    </span>
                    <span>{a.label}<small className="block text-[#706453]">{a.count} films · {a.periods} periods</small></span>
                  </button>;
                })}
                {!group.length && <p className="text-sm">No recurring evidence yet.</p>}
              </div>
            </div>;
          })}
        </div>
        {ranked.some(a => ranked.filter(b => b.direction === a.direction).length > 4) &&
          <button type="button" className="secondary-action mt-4 rounded-full px-4 py-1.5" aria-expanded={showAll}
            onClick={() => { if (showAll) setAspect(ranked[0].key); setShowAll(!showAll); }}>
            {showAll ? "Show fewer preferences" : "Show all preferences"}
          </button>}
      </section>
      <section className={panel}>
        <h2 className="font-display text-3xl">Your taste through time</h2>
        <h3 className="mt-4 text-xl font-semibold">{aspect.label}</h3>
        <p className="mt-1 text-sm text-[#625845]">{recent} of your latest {recentIds.size} films · {aspect.count} of {reviews.length} overall · recurring in {periods.filter(p => p.count > 0).length} of {periods.length} periods</p>
        <p className="mt-3 text-sm text-[#625845]">Bars show the share of films with supporting evidence in each period. Select a bar for its dates and reviews.</p>
        <div className="mt-4 flex gap-1 overflow-x-auto pb-2" role="group" aria-label="Review periods">
          {periods.map((p, i) => <button type="button" key={p.through} onClick={() => setPeriod(i)}
            aria-pressed={i === periodIndex} aria-label={`Through ${date(p.endDate)}, ${p.count} of ${p.total} films${p.partial ? ", partial period" : ""}`}
            title={`${date(p.endDate)} · ${p.count}/${p.total}`}
            className="min-w-12 flex-1 rounded-lg border border-transparent px-1 py-2 text-xs aria-pressed:border-[#A58443] aria-pressed:bg-[#F5EDC5]">
            <span className="flex h-24 items-end justify-center border-b border-[#AF9C6B]">
              <span className={`block w-3/5 rounded-t ${p.partial ? "border-2 border-dashed border-[#886A36] bg-[#EAD6AA]" : "bg-[#B9944D]"}`}
                style={{height: `${100 * p.count / p.total / maxRate}%`}} />
            </span>
            <span className="mt-1 block">{Math.round(100 * p.count / p.total)}%</span>
            <span className="text-[#706453]">{p.endDate.slice(0,4)}{p.partial ? "*" : ""}</span>
          </button>)}
        </div>
        <h3 className="mt-4 font-semibold">{date(reviews[selected.start].reviewed_on)} – {date(selected.endDate)}</h3>
        <p className="text-sm text-[#625845]">{selected.count} of {selected.total} films · Reviews {selected.start + 1}–{selected.through}{selected.partial ? " · Partial period" : ""}</p>
        {selected.items.length > 0 && <details className="mt-3" key={aspectKey + ":" + selected.through}>
          <summary className="cursor-pointer font-semibold text-[#775321]">Reviews from this period</summary>
          <Sources items={selected.items} reviews={reviewMap} />
        </details>}
        {selected.through !== current.through && <details className="mt-3" key={selected.through}>
          <summary className="cursor-pointer font-semibold text-[#775321]">Profile through review {selected.through}</summary>
          {summary(selected)}
        </details>}
      </section>
    </>}
  </>;
}
