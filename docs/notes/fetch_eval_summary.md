# Latest Evaluation Snapshot

We ran the full planner → fetcher flow on the standard DIY query list right after tightening the comment filters (karma ≥ 2, top‑5 per post). The two artifacts worth bookmarking:

- Quantitative summary: `data/eval_runs/fetch_eval_20251110_211345.json`
- Content preview: `data/fetch_previews/fetch_preview_20251110_215359.json`

## What We Saw

- **Post acceptance stays on target.** Each query kept between 12 and 30 posts, which lines up with the 25‑40% acceptance range in `docs/reddit_fetcher_baselines.md`.
- **Comment counts normalized.** After the karma filter, accepted comments dropped to 16–67 per query (roughly 2–3 comments per post). That’s exactly what we wanted—no single thread is flooding the dataset anymore.
- **Preview shows higher-signal replies.** The fetch preview JSON is easy to skim and every retained comment shares actual techniques or tips. Empty `comments` arrays now only appear on posts that truly lacked community upvotes. This gives us confidence we’re handing quality context to the synthesizer.

## Implications

- The karma threshold + top‑5 cap improved relevance without starving the fetcher. We can safely feed these FetchResults into the next stage knowing they contain community-approved answers.
- Because per-query totals still differ (e.g., drywall repair returns more usable content than bathtub caulking), we may want to normalize contributions during synthesis so high-volume topics don’t dominate.

## Next Steps

1. **Run the preview script for any new query batch** to confirm comments remain useful before touching the synthesizer.
2. **Add a synth prototype** that ingests one of these FetchResults and highlights a few top themes per query. Focus first on the queries with richer previews (drywall repair, floating shelves) to validate the end-to-end story.
3. **Monitor comment mix** as we expand the query list; if topics consistently return fewer than ~10 comments, revisit the planner search terms rather than loosening filters.
