# Movie Agent End-to-End Evaluation

Generated automatically by Day 17 evaluation.

## Configuration Summary

| Configuration | Hit@K | Precision@K | Recall@K | MRR | nDCG@K | Constraint Accuracy | Diversity | Novelty | P50 Latency | P95 Latency | Fallback Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| local_raw | 0.5000 | 0.1500 | 0.1500 | 0.3125 | 0.3528 | 0.4778 | 0.6677 | 0.3231 | 12.7000 | 13.6995 | 0.0000 |
| openai_raw | 0.6250 | 0.2500 | 0.2500 | 0.4583 | 0.5827 | 0.8500 | 0.5817 | 0.2203 | 222.5300 | 441.1070 | 0.0000 |
| openai_intent_retrieval | 0.6250 | 0.2250 | 0.2250 | 0.3625 | 0.5247 | 0.8055 | 0.5865 | 0.3025 | 1642.0100 | 2125.9190 | 0.0000 |
| openai_agent_heuristic | 0.5000 | 0.2000 | 0.2000 | 0.4062 | 0.5309 | 0.8055 | 0.7518 | 0.2791 | 1539.3400 | 1636.1045 | 0.0000 |
| openai_agent_llm | 0.7500 | 0.2750 | 0.2750 | 0.7500 | 0.7653 | 0.9556 | 0.5844 | 0.2234 | 4280.9100 | 5883.9345 | 0.0000 |

## Per-Query Results

| Configuration | Query | Hit@K | MRR | nDCG@K | Constraint Accuracy | Diversity | Latency | Error |
|---|---|---:|---:|---:|---:|---:|---:|---|
| local_raw | nolan_under_150 | 1.0000 | 0.5000 | 0.5838 | 0.8000 | 0.6600 | 12.2600 |  |
| local_raw | dicaprio_uncertain_reality | 1.0000 | 0.5000 | 0.2543 | 0.2000 | 0.8967 | 12.4000 |  |
| local_raw | quiet_emotional_scifi | 0.0000 | 0.0000 | 0.5928 | — | 0.4850 | 11.6600 |  |
| local_raw | korean_thriller_after_2000 | 1.0000 | 0.5000 | 0.6587 | 0.8667 | 0.8433 | 13.3600 |  |
| local_raw | family_animation_under_120 | 0.0000 | 0.0000 | 0.0000 | 0.4000 | 0.5500 | 13.6800 |  |
| local_raw | french_romance_before_2010 | 0.0000 | 0.0000 | 0.0925 | 0.6000 | 0.4000 | 12.6700 |  |
| local_raw | antiwar_survival | 1.0000 | 1.0000 | 0.6400 | — | 0.6733 | 13.7100 |  |
| local_raw | character_driven_action | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.8333 | 12.7300 |  |
| openai_raw | nolan_under_150 | 1.0000 | 1.0000 | 0.9332 | 0.9000 | 0.7900 | 460.0700 |  |
| openai_raw | dicaprio_uncertain_reality | 1.0000 | 1.0000 | 0.8415 | 0.8000 | 0.8050 | 405.8900 |  |
| openai_raw | quiet_emotional_scifi | 1.0000 | 1.0000 | 0.6639 | — | 0.6533 | 221.0600 |  |
| openai_raw | korean_thriller_after_2000 | 1.0000 | 0.3333 | 0.4261 | 0.9333 | 0.7667 | 224.7200 |  |
| openai_raw | family_animation_under_120 | 1.0000 | 0.3333 | 0.8062 | 0.9333 | 0.4100 | 147.9700 |  |
| openai_raw | french_romance_before_2010 | 0.0000 | 0.0000 | 0.0000 | 0.5333 | 0.5417 | 180.5000 |  |
| openai_raw | antiwar_survival | 0.0000 | 0.0000 | 0.6228 | — | 0.2500 | 206.9700 |  |
| openai_raw | character_driven_action | 0.0000 | 0.0000 | 0.3676 | 1.0000 | 0.4367 | 224.0000 |  |
| openai_intent_retrieval | nolan_under_150 | 1.0000 | 1.0000 | 0.9332 | 0.9000 | 0.7900 | 2286.1000 |  |
| openai_intent_retrieval | dicaprio_uncertain_reality | 1.0000 | 1.0000 | 0.9256 | 0.8000 | 0.8050 | 1683.2500 |  |
| openai_intent_retrieval | quiet_emotional_scifi | 1.0000 | 0.2000 | 0.4517 | — | 0.6733 | 1512.7500 |  |
| openai_intent_retrieval | korean_thriller_after_2000 | 1.0000 | 0.2000 | 0.5386 | 1.0000 | 0.6167 | 1621.8400 |  |
| openai_intent_retrieval | family_animation_under_120 | 0.0000 | 0.0000 | 0.3593 | 0.5333 | 0.6683 | 1548.7300 |  |
| openai_intent_retrieval | french_romance_before_2010 | 0.0000 | 0.0000 | 0.0000 | 0.6000 | 0.3333 | 1592.8600 |  |
| openai_intent_retrieval | antiwar_survival | 1.0000 | 0.5000 | 0.7227 | — | 0.2500 | 1828.4400 |  |
| openai_intent_retrieval | character_driven_action | 0.0000 | 0.0000 | 0.2665 | 1.0000 | 0.5550 | 1662.1800 |  |
| openai_agent_heuristic | nolan_under_150 | 1.0000 | 1.0000 | 0.9332 | 0.9000 | 0.8800 | 1483.3700 |  |
| openai_agent_heuristic | dicaprio_uncertain_reality | 1.0000 | 1.0000 | 0.9172 | 0.8000 | 0.8050 | 1579.7300 |  |
| openai_agent_heuristic | quiet_emotional_scifi | 0.0000 | 0.0000 | 0.6237 | — | 0.8417 | 1630.6900 |  |
| openai_agent_heuristic | korean_thriller_after_2000 | 1.0000 | 0.2500 | 0.4890 | 0.9333 | 0.7267 | 1615.9400 |  |
| openai_agent_heuristic | family_animation_under_120 | 0.0000 | 0.0000 | 0.4461 | 0.6667 | 0.8283 | 1433.0600 |  |
| openai_agent_heuristic | french_romance_before_2010 | 0.0000 | 0.0000 | 0.0000 | 0.5333 | 0.6417 | 1362.9100 |  |
| openai_agent_heuristic | antiwar_survival | 1.0000 | 1.0000 | 0.5415 | — | 0.6350 | 1639.0200 |  |
| openai_agent_heuristic | character_driven_action | 0.0000 | 0.0000 | 0.2966 | 1.0000 | 0.6557 | 1498.9500 |  |
| openai_agent_llm | nolan_under_150 | 1.0000 | 1.0000 | 0.9256 | 1.0000 | 0.7550 | 3657.6000 |  |
| openai_agent_llm | dicaprio_uncertain_reality | 1.0000 | 1.0000 | 0.9332 | 1.0000 | 0.8717 | 3572.2900 |  |
| openai_agent_llm | quiet_emotional_scifi | 1.0000 | 1.0000 | 0.8421 | — | 0.5100 | 4429.1000 |  |
| openai_agent_llm | korean_thriller_after_2000 | 1.0000 | 1.0000 | 0.7860 | 1.0000 | 0.4250 | 3647.7400 |  |
| openai_agent_llm | family_animation_under_120 | 0.0000 | 0.0000 | 0.6094 | 0.9333 | 0.5283 | 4780.6700 |  |
| openai_agent_llm | french_romance_before_2010 | 1.0000 | 1.0000 | 0.9203 | 0.8000 | 0.6750 | 4723.0500 |  |
| openai_agent_llm | antiwar_survival | 1.0000 | 1.0000 | 0.9250 | — | 0.2500 | 6478.0000 |  |
| openai_agent_llm | character_driven_action | 0.0000 | 0.0000 | 0.1809 | 1.0000 | 0.6600 | 4132.7200 |  |

## Interpretation Notes

- Curated relevant-title lists are incomplete and should be treated as smoke-test labels.
- nDCG is most meaningful after the pooled candidates have been manually graded.
- Catalog novelty is a popularity-based proxy, not a direct measure of user value.
- LLM configurations should be compared over multiple runs before making strong claims about stability.


## Conclusion
- local_raw: fast, diverse, but relatively weak retrieval. Only half the queries returned any movie from your curated relevant-title lists. Its constraint accuracy was only: 47.78%. Its MRR of 0.3125 also means relevant movies often appeared relatively low in the list or were absent.

- openai_raw: the clearest standalone improvement. Hit@K: 0.5000 → 0.6250; Precision: 0.1500 → 0.2500; Recall: 0.1500 → 0.2500; MRR: 0.3125 → 0.4583; Constraint accuracy: 0.4778 → 0.8500. Diversity and novelty fell. Among the configurations without extra reasoning calls, openai_raw currently offers the strongest quality-to-latency tradeoff. It is a strong candidate for your default retrieval layer. latency: 14 ms → 210 ms. 

- openai_intent_retrieval: the intent rewrite did not help.

- openai_agent_heuristic: diversity worked, relevance regressed

- openai_agent_llm: best quality, highest latency 


# Conclusion 1: The embedding upgrade helped

This is your strongest conclusion because local_raw and openai_raw differ mainly in the embedding provider.

You can currently say:

On the initial eight-query evaluation set, OpenAI embeddings improved Hit@5 from 0.50 to 0.625, Precision@5 from 0.15 to 0.25, MRR from 0.313 to 0.458, and metadata-constraint accuracy from 0.478 to 0.85, while increasing median retrieval latency from approximately 14 ms to 210 ms.

That is a valid ablation result, subject to the small-sample caveat.

# Conclusion 2: Single-query intent rewriting is not helping yet

You can say:

Replacing the original query with a single LLM-generated retrieval rewrite did not improve Hit@5 or constraint accuracy and reduced Precision@5 and MRR, while adding approximately 1.5 seconds of median latency.

This indicates you should inspect or redesign the retrieval-query strategy.

# Conclusion 3: The heuristic reranker currently overemphasizes diversity

You can say:

Heuristic reranking increased intra-list genre diversity from 0.571 to 0.732 and modestly improved novelty, but reduced Hit@5, MRR, and constraint adherence, suggesting that the current diversity or novelty weights may be too strong relative to semantic relevance.

# Conclusion 4: Bounded LLM reranking is promising but expensive

You can say:

The bounded LLM reranker achieved the best first-pass quality, including 0.75 Hit@5, 0.75 MRR, and 0.933 constraint accuracy, but increased median latency to approximately 4.37 seconds and P95 latency to approximately 6.10 seconds.

# Conclusion 5: The full LLM pipeline should remain optional for now

A reasonable product decision based on this first pass is:

Default fast mode:
openai_raw or tuned heuristic pipeline

High-quality mode:
openai_agent_llm

Do not finalize this decision until after pooled relevance grading.
