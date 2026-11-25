import { getTasteProfile } from "@/lib/api";
import TasteHistory from "@/components/TasteHistory";
import type { TasteProfile } from "@/types/taste-profile";

export const dynamic = "force-dynamic";
export const metadata = { title: "Taste Profile | Movie Agent" };

const formatDate = new Intl.DateTimeFormat("en-US", {
  month: "short", day: "numeric", year: "numeric", timeZone: "UTC",
});

function ProfileFindings({ profile }: { profile: TasteProfile }) {
  const reviews = new Map(profile.reviews.map((review) => [review.review_id, review]));
  const observations = new Map(profile.evidence.map((item) => [item.evidence_id, item]));

  function renderEvidence(ids: number[]) {
    return ids.map((id) => {
      const item = observations.get(id);
      const review = item && reviews.get(item.review_id);
      if (!review || !item) return null;
      return (
        <li key={id} className="border-l-2 border-[#BDB76B] pl-4">
          <h4 className="font-semibold">{review.title}</h4>
          <time dateTime={review.reviewed_on} className="text-sm text-[#706453]">
            {formatDate.format(new Date(review.reviewed_on))}
          </time>
          <blockquote className="my-2 whitespace-pre-line break-words font-display text-lg">
            {review.original_body ?? item.quote}
          </blockquote>
          <p className="text-sm text-[#625845]"><strong>Model interpretation</strong> · {item.interpretation}</p>
        </li>
      );
    });
  }

  if (!profile.preferences.length) return (
    <p className="empty-state mt-8 rounded-3xl p-6">These reviews yielded no recurring preferences with enough supporting evidence.</p>
  );
  return (
    <div className="mt-8 space-y-5">
      {profile.preferences.map((preference) => (
        <article key={preference.claim} className="surface-card rounded-3xl p-6 md:p-8">
          <p className="eyebrow">{preference.theme}</p>
          <h2 className="mt-2 max-w-3xl font-display text-2xl leading-snug">{preference.claim}</h2>
          <details className="mt-4">
            <summary className="cursor-pointer font-semibold text-[#775321]">Why we think this</summary>
            <h3 className="mt-5 font-semibold">Supporting reviews</h3>
            <ul className="mt-3 space-y-4">{renderEvidence(preference.supporting)}</ul>
            {preference.exceptions.length > 0 && (
              <>
                <h3 className="mt-5 font-semibold">Exceptions</h3>
                <ul className="mt-3 space-y-4">{renderEvidence(preference.exceptions)}</ul>
              </>
            )}
          </details>
        </article>
      ))}
    </div>
  );
}

export default async function TasteProfilePage() {
  let profile: TasteProfile | null = null;
  let unavailable = false;
  try {
    profile = await getTasteProfile();
  } catch {
    unavailable = true;
  }
  const reviews = profile?.reviews;
  return (
    <main className="app-page">
      <section className="mx-auto max-w-5xl px-5 py-10 md:py-14">
        <header className="page-hero rounded-[2.25rem] px-6 py-10 md:px-10">
          <h1 className="font-display text-4xl font-semibold md:text-6xl">Taste Profile</h1>
          {reviews && reviews.length > 0 && (
            <p className="mt-3 text-[#625845]">
              From {reviews.length} reviews, {formatDate.format(new Date(reviews[0].reviewed_on))}
              {" through "}{formatDate.format(new Date(reviews[reviews.length - 1].reviewed_on))}.
            </p>
          )}
        </header>
        {unavailable ? (
          <p role="alert" className="mt-8">Could not reach the taste profile. Check the backend connection and reload this page.</p>
        ) : profile ? (
          <>
            {profile.is_current === false && <p role="status" className="mt-5 text-[#706453]">
              Your reviews have changed since this profile was built. Reload to check for the updated profile.
            </p>}
            {profile.history?.length ? <TasteHistory profile={profile} /> : <ProfileFindings profile={profile} />}
          </>
        ) : (
          <div className="empty-state mt-8 rounded-3xl p-6">
            <h2 className="font-display text-2xl">Your profile hasn’t been built yet</h2>
            <p className="mt-2">From the backend directory, run <code>python -m app.scripts.build_taste_profile</code> to analyze your review history.</p>
          </div>
        )}
      </section>
    </main>
  );
}
