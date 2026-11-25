import Image from "next/image";

import { MovieReviewPanel } from "@/components/MovieReviewPanel";
import type { MovieSearchItem } from "@/types/movie";

type BrowseMovieCardProps = {
  movie: MovieSearchItem;
  priority?: boolean;
};

export function BrowseMovieCard({
  movie,
  priority = false,
}: BrowseMovieCardProps) {
  return (
    <article className="surface-card overflow-hidden rounded-[2rem] transition duration-300 hover:-translate-y-1 hover:border-[#CE8946]/70 hover:shadow-[0_24px_60px_rgba(91,72,30,0.18)]">
      <div className="flex flex-col sm:flex-row">
        <div className="relative aspect-[2/3] w-full shrink-0 bg-[#E8DCA1] sm:w-52">
          {movie.poster_url ? (
            <Image
              src={movie.poster_url}
              alt={`${movie.title} poster`}
              fill
              sizes="(max-width: 640px) 100vw, 208px"
              className="object-cover"
              priority={priority}
            />
          ) : (
            <div className="flex h-full min-h-72 items-center justify-center bg-[linear-gradient(145deg,#FDFBD4,#BDB76B)] p-6 text-center text-sm font-semibold text-[#625845]">
              No poster available
            </div>
          )}
        </div>

        <div className="relative min-w-0 flex-1 overflow-hidden bg-[#FFFDF0]">
          {movie.backdrop_url && (
            <div
              className="pointer-events-none absolute inset-0"
              aria-hidden="true"
            >
              <Image
                src={movie.backdrop_url}
                alt=""
                fill
                sizes="(max-width: 640px) 100vw, 820px"
                className="object-cover object-center opacity-20 saturate-75"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#FFFDF0] via-[#FFFDF0]/90 to-[#FDFBD4]/70" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#FFFDF0]/80 via-transparent to-[#D4AF37]/10" />
            </div>
          )}

          <div className="relative z-10 flex h-full flex-col justify-between gap-8 p-6">
            <div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="font-display text-3xl font-semibold text-[#352D22]">
                    {movie.title}
                  </h2>
                  <p className="mt-1 text-sm font-medium text-[#706453]">
                    {movie.release_year ?? "Unknown year"}
                  </p>
                </div>

                <div className="w-fit rounded-2xl border border-[#D4AF37]/75 bg-[#FDFBD4]/90 px-4 py-3 text-left shadow-[0_8px_20px_rgba(91,72,30,0.10)] backdrop-blur-sm sm:text-right">
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#826714]">
                    Movie rating
                  </p>
                  <p className="mt-1 font-display text-2xl font-semibold text-[#594713]">
                    {movie.movie_rating !== null
                      ? `${movie.movie_rating.toFixed(1)}/10`
                      : "Not rated"}
                  </p>
                </div>
              </div>

              <dl className="mt-6 grid gap-4">
                <div>
                  <dt className="text-xs font-bold uppercase tracking-[0.18em] text-[#8A5B2B]">
                    Director
                  </dt>
                  <dd className="mt-1 text-base text-[#42382B]">
                    {movie.director ?? "Director unavailable"}
                  </dd>
                </div>

                <div>
                  <dt className="text-xs font-bold uppercase tracking-[0.18em] text-[#8A5B2B]">
                    Cast
                  </dt>
                  <dd className="mt-1 text-base leading-7 text-[#42382B]">
                    {movie.cast.length > 0
                      ? movie.cast.join(", ")
                      : "Cast unavailable"}
                  </dd>
                </div>
              </dl>
            </div>

            <div>
              <MovieReviewPanel movieId={movie.movie_id} title={movie.title} />
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
