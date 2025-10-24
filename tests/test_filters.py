"""Unit tests for post filtering helpers."""

from types import SimpleNamespace
from scripts.ingest_pipeline import include_post

#Helper Function 
def make_submission(flair: str = "", title: str = "", selftext: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        link_flair_text=flair,
        title=title,
        selftext=selftext,
    )

# include_post rejects submission if body is too short even if flair & title pass. 
def test_short_body_excluded():
    submission = make_submission(
        flair="help",
        title="How do I fix my table?",
        selftext= "Short body", # ,20 characters after cleaning
    )
    assert include_post(submission) is False 

# include_posts allows submission if allowed flairs AND title pass.
def test_allowed_flair_title_match_included():
    submission = make_submission(
        flair="woodworking", 
        title="How do I fix this table?",
        selftext="Need help with how to fix a broken table leg that snapped while sanding.",
    )
    assert include_post(submission) is True

#inlcude_post allows submission with flair None or empty and title passes.
def test_no_flair_with_title_match_included():
    submission = make_submission(
        flair="",
        title="How do I fix this table?",
        selftext="Need help with how to fix a broken table leg that snapped while sanding.",
    )
    assert include_post(submission) is True 

#include_post rejects submission if flair passes but title does not. 
def test_allowed_flair_without_title_match_excluded():
    submission = make_submission(
        flair="help",
        title="I made this for my wife.",
        selftext="I made this shelf for my wife. Took three weeks. How did I do?",
    ) 
    assert include_post(submission) is False
