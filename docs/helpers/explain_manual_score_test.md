
## How does manual_score_test.py work? 


`manual_score_test.py` is a manual smoke test for the keyword scoring. It works like this: 


- Runs from the command line; you can pass `--query`, `--limit`, and `--pause` flags.
- Sets up logging (both to the terminal and to a timestamped file in logs/).
- Uses the planner (`create_search_plan`) to expand each query into subreddits + search terms, then uses `RedditClient.paginate_search` to fetch posts with the same transport defaults as the fetcher.
- Applies `passes_post_validation` before scoring so only eligible posts are “considered.”
- Cleans the title/body with `clean_text`, runs `evaluate_post_relevance`, and logs whether the post passed along with score and matched keywords.
- Sleeps briefly between requests so we don’t hit rate limits.
- Logs summaries at the end:
  - per pair: `Summary (pair): passed X/Y posts for r/<subreddit> | search_term='<term>' | query='<query>'`
  - overall: passed/considered and considered/fetched totals.
- Saves output to `logs/manual_score_test_<timestamp>.log` (gitignored).

Example run:
```bash
python3 scripts/manual_score_test.py --query "how to caulk bathtub."
```
  

It’s basically a quick way to fetch real Reddit posts, run them through the scoring helper, and see if the weights/threshold behave the we want before building the full fetcher.
