
## Log Notes - Keyword Filtering to Capture Signal

- Our original log had acceptance rate of 28/60. This was too strict and we were missing out on high quality content. 
- We ran several iterations tweaking heuristics and finally reached a new baseline of 54/60 or 90% 
- We succsfully tweaked our filters from being overly agressive to capturing a strong signal that a post is relevant for DIY instructional content.


## Ending point: Baseline-90 Log
- **Log:**  `logs/manual_score_test_11-07_01-05-29.log`
- Accepted 54/60, 90% 
- This suggests filters are keeping most instructional posts (and only weeding out obvious junk). 
- The current configuration captures most relevant posts while still enforcing the threshold and negative checks.
- 2 false positives (showoff/brag posts remain) bc they contain positive keywords and exceed the min threshold. 
- Will brainstorm how to handle these better at a later point. 

## Starting point: Baseline-28 Log

- **Log:** `manual_score_test_11-06_22-50-50.log`

**Observations after Baseline-28**
  - False negatives:
    - “How can I safely replace the ceiling light fixture?” scored 0 → add question variants (“How can I…”, “Can I…”, “replace”) so instructional titles match.
    - “Help with these stupid light switches.” scored 0 → add generic “help” requests to the question-driven group.
    - “Trying to replace light switches…” only matched “broken” → include “replace/swap/change” verbs in how-to or troubleshooting groups.
  - False positives:
    - Showcase posts (“How I turned a broken NES…”, “New laundry nook…”, “DIY Time Portal”) passed because generic keywords (drill, screws, broken) outweighed the lack of instruction → add anti-keywords (“How I…”, “I made…”, “After/Before”) and lower weights for `tools_materials` and `safety_tips`.
    - “I made custom closet built-ins…” highlight the need for brag filters (“I made…”, “custom build”) or lower weights for catch-all materials.
  
  **Decisions after Baseline-28:** 
 - Expand question-driven keywords to cover “How can I…”, “Can I…”, “help”, “replace/change/swap”.
 - Add anti-showcase phrases (“How I…”, “I made…”, “After/Before”, “turned my…”) to `NEGATIVE_KEYWORDS`.
- Reduce weight of `tools_materials` and `safety_tips` so they can’t push showcase posts over the threshold alone.

## Run:
  
  ```bash 
  python -m scripts.manual_score_test \
  --subreddit diy \
  --subreddit homeimprovement \
  --search-term "replace broken light switch safely" \
  --search-term "light switch installation tips" \
  --search-term "how to change light switch" \
  --limit 10
  ```