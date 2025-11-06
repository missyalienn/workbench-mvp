
## How does manual_score_test.py work? 


`manual_score_test.py` is a manual smoke test for the keyword scoring. It works like this: 


- Runs from the command line; you can pass --subreddit, --term, --limit, and --pause flags to control where it looks.
- Sets up logging (both to the terminal and to a timestamped file in logs/).
- Uses REST client to hit Reddit’s search endpoint for each subreddit/term combo.
- Cleans the title/body with clean_text, runs evaluate_post_relevance, and logs whether the post was accepted or rejected with the score and matched keywords.
- Sleeps briefly between requests so we don’t hit rate limits.
- Prints a final summary of how many posts cleared the threshold.
- Saves the output to logs/manual_score_test+{timestamp}.log (currently gitignored, will check in as needed)
  

It’s basically a quick way to fetch real Reddit posts, run them through the scoring helper, and see if the weights/threshold behave the we want before building the full fetcher.