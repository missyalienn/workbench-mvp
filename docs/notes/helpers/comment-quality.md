## Comment Quality Plan

**Tie comments to their post:** after a post clears relevance + safety filters, we call a dedicated fetch_and_filter_comments(post_id) helper that hits Reddit’s /comments/{id} endpoint. That API returns the post plus its top-level replies, so we only see comments written under the given post (no cross-post leakage).

**Clean and normalize first: every comment body runs through clean_text,** same as post titles/bodies. This strips markdown noise, links, and emojis so scoring/length checks see real content and the LLM later works with clean text.

**Apply basic quality gates:** for each cleaned comment we enforce:

- non-empty and above a minimum word/character count (skip “thanks!” replies),
- minimum Reddit score (e.g., score ≥ 1) to favor community-approved answers,
- optional NSFW or deleted checks if Reddit flags them. Each rejection gets logged with a reason (too_short, low_score, etc.) for tuning.

**Keep best comments per post:** store accepted comments in a list attached to that Post model (Post.comments). Since we only populate this list after passing post-level filters, every comment automatically inherits the same SearchPlan context and can be surfaced alongside its post.

**Log and test:** logging records how many comments we fetched vs. accepted per post, helping us adjust thresholds. In tests we mock the Reddit response and assert that only comments aligned to the post ID make it into Post.comments.

This pipeline ensures each Post carries a curated set of relevant answers, giving the LLM the back-and-forth context it needs when generating responses.