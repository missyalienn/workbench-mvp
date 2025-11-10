# Reddit Fetcher Baselines

Acceptance and quality targets we expect during fetcher runs. Use these to judge whether a smoke test or live run is healthy.

- **Candidates per (subreddit, term):** Aim for 8–10 raw posts when `post_limit ≈ 10`. Consistently lower counts may mean the planner query is too narrow.
- **Post acceptance rate:** 25–40% of candidates should survive validation + scoring + length + dedupe. <10% suggests overly strict filters; >60% means we’re letting in too much noise.
- **Comment yield:** Around 60% of accepted posts should carry at least one approved comment, averaging 2–3 comments per post.
- **Rejection mix:** Expect most rejections from metadata vetoes (deleted, AutoModerator, ads, non-self) and length filters. Surging scoring rejections signal a query or threshold issue.
- **Total output:** For 3 subreddits × 3 search terms × `post_limit=10`, final posts should land in the ~20–35 range with vetted comments attached.
