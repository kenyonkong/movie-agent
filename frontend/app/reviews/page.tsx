import Link from "next/link";

export default function ReviewsPage() {
  return (
    <main className="app-page">
      <section className="mx-auto max-w-6xl px-6 py-10 md:py-14">
        <div className="page-hero rounded-[2.25rem] px-6 py-10 md:px-10 md:py-14">
          <p className="eyebrow mb-3">My Reviews</p>
          <h1 className="font-display max-w-4xl text-4xl font-semibold leading-[1.05] text-[#352D22] md:text-6xl">
            A home for the films you remember.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[#706453] md:text-lg">
            Soon you will be able to rate movies, capture your thoughts, and
            return to a personal journal of everything you have watched.
          </p>
        </div>

        <div className="surface-card mt-8 grid overflow-hidden rounded-[2rem] md:grid-cols-[0.8fr_1.2fr]">
          <div className="flex min-h-64 items-center justify-center border-b border-[#BDB76B]/55 bg-[linear-gradient(145deg,#D4AF37,#CE8946)] p-8 md:border-r md:border-b-0">
            <div className="flex h-40 w-40 rotate-[-3deg] flex-col items-center justify-center rounded-2xl border border-[#FFFDF0]/70 bg-[#FDFBD4]/90 text-center shadow-[0_20px_40px_rgba(91,72,30,0.22)]">
              <span className="text-xs font-bold uppercase tracking-[0.22em] text-[#826714]">
                Coming next
              </span>
              <span className="mt-3 font-display text-3xl font-semibold text-[#352D22]">
                Film Journal
              </span>
            </div>
          </div>

          <div className="p-8 md:p-10">
            <p className="eyebrow mb-3">Review feature · To do</p>
            <h2 className="font-display text-3xl font-semibold text-[#352D22]">
              Your first review starts with a movie.
            </h2>
            <p className="mt-3 max-w-xl text-base leading-7 text-[#706453]">
              Review actions are visible as placeholders, but nothing is saved
              yet. Browse the catalog or discover recommendations while the
              writing experience is being prepared.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                href="/movies"
                className="primary-action rounded-full px-6 py-3 text-sm font-bold transition"
              >
                Browse movies
              </Link>
              <Link
                href="/"
                className="secondary-action rounded-full px-6 py-3 text-sm font-semibold transition"
              >
                View recommendations
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
