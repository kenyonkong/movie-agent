"use client";

import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "@/lib/api";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function checkBackend() {
    try {
      setError(null);
      const data = await getHealth();
      setHealth(data);
    } catch (err) {
      setHealth(null);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }

  useEffect(() => {
    checkBackend();
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center px-6 py-12">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.3em] text-cyan-400">
            Summer 2026 Personal Project
          </p>

          <h1 className="mb-4 text-4xl font-bold tracking-tight md:text-6xl">
            Movie Agent
          </h1>

          <p className="mb-8 max-w-2xl text-lg leading-8 text-slate-300">
            A full-stack AI movie recommendation system with semantic search,
            personalized reranking, user preference memory, and grounded
            explanations.
          </p>

          <div className="mb-6 rounded-2xl border border-slate-800 bg-slate-950 p-5">
            <h2 className="mb-3 text-xl font-semibold">
              Backend Connection Status
            </h2>

            {health && (
              <div className="space-y-2 text-sm text-slate-300">
                <p>
                  <span className="font-semibold text-slate-100">Status:</span>{" "}
                  {health.status}
                </p>
                <p>
                  <span className="font-semibold text-slate-100">App:</span>{" "}
                  {health.app_name}
                </p>
                <p>
                  <span className="font-semibold text-slate-100">Version:</span>{" "}
                  {health.version}
                </p>
                <p>
                  <span className="font-semibold text-slate-100">
                    Environment:
                  </span>{" "}
                  {health.environment}
                </p>
              </div>
            )}

            {error && (
              <p className="text-sm text-red-400">
                Could not connect to backend: {error}
              </p>
            )}

            {!health && !error && (
              <p className="text-sm text-slate-400">Checking backend...</p>
            )}
          </div>

          <button
            onClick={checkBackend}
            className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            Recheck Backend
          </button>
        </div>
      </section>
    </main>
  );
}