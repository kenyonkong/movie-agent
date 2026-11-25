export type ProfileReview = {
  review_id: number;
  movie_id: string;
  title: string;
  reviewed_on: string;
  display_body: string;
  original_body: string | null;
};

export type Evidence = {
  evidence_id: number;
  review_id: number;
  quote: string;
  interpretation: string;
};

export type TasteProfile = {
  generated_at: string;
  model: string;
  reviews: ProfileReview[];
  evidence: Evidence[];
  preferences: {
    theme: string;
    claim: string;
    supporting: number[];
    exceptions: number[];
  }[];
};
