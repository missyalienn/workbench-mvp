"""Keyword groups that prioritize instructional Reddit content."""

from collections import OrderedDict

KEYWORD_GROUPS = OrderedDict(
    {
        "how_to_instructional": {
            "rationale": "Capture explicit how-to phrasing and verbs that start DIY walkthroughs.",
            "keywords": [
                "how to",  # direct how-to wording
                "step by step",  # instructions broken into steps
                "build",  # common DIY action verb
                "refinish",  # surface preparation projects
                "install",  # hardware and fixture setup
                "assemble",  # kit builds or furniture assembly
                "repair",  # detailed fix oriented language
                "instructions",  # explicit request for detailed guidance
                "fix",  # general repair or troubleshooting phrasing
            ],
        },
        "troubleshooting_repair": {
            "rationale": "Flag posts asking for help fixing failures or diagnosing problems.",
            "keywords": [
                "won't start",  # common failure phrasing
                "doesn't work",  # general malfunction
                "stuck",  # mechanical jams
                "leaking",  # plumbing or fluid issues
                "squeaking",  # noise-based diagnosis
                "shorted",  # electrical fault
                "cracked",  # structural damage needing advice
                "broken",  # general failure state
                "scratched",  # surface damage requiring advice
                "dented",  # structural damage requiring advice
                "damage",  # general damage state requiring advice
            ],
        },
        "question_driven": {
            "rationale": "Highlight questions seeking advice, best practices, or collective tips.",
            "keywords": [
                "any tips",  # open request for suggestions
                "what's the best way",  # direct process inquiry
                "should i",  # decision guidance ask
                "how would you",  # community experience solicitation
                "is it possible to",  # feasibility check
                "recommendations for",  # product or approach referrals
                "looking for advice",  # explicit help request
            ],
        },
        "tools_materials": {
            "rationale": "Surface posts about material choices and tool usage that underpin DIY planning.",
            "keywords": [
                "plywood",  # common woodworking material
                "2x4",  # framing lumber shorthand
                "sandpaper",  # finishing supply
                "drill",  # handheld power tool terminology
                "impact driver",  # power tool terminology
                "stain",  # finish selection
                "poly",  # polyurethane finish shorthand
                "miter saw",  # precision cutting tool
                "orbital sander",  # surface prep equipment
                "screws",  # fastener selection
                "drill bits",  # consumable tooling
            ],
        },
        "safety_tips": {
            "rationale": "Identify posts focused on safe execution and first-time maker confidence.",
            "keywords": [
                "safety gear",  # protective equipment focus
                "safe to do",  # risk assessment wording
                "first time",  # novice indicator
                "beginner mistake",  # learning mindset
                "newbie",  # self-identified inexperience
                "learning curve",  # expectation setting
                "respirator",  # PPE for finishes and dust
                "mask",  # general face protection
            ],
        },
    }
)

NEGATIVE_KEYWORDS = OrderedDict(
    {
        "showcase_brag": {
            "rationale": "Filter out posts that celebrate finished work without instructional detail.",
            "keywords": [
                "just finished",  # announcement of completion
                "before and after",  # showcase collage language
                "my latest build",  # portfolio oriented phrasing
                "finally done",  # completion celebration
                "check out my",  # promotional tone
                "progress pics",  # visual update without guidance
                "showing off",  # explicit brag indicator
                "i built",  # explicit build announcement
                "i made",  # explicit make announcement
                "i finished",  # explicit finish announcement
            ],
        }
    }
)

KEYWORD_WEIGHTS = OrderedDict(
    {
        "how_to_instructional": 5.0,
        "troubleshooting_repair": 4.0,
        "question_driven": 3.0,
        "tools_materials": 2.0,
        "safety_tips": 2.0,
        "showcase_brag": -6.0,
    }
)

MIN_POST_SCORE = 6.0

# TODO: Move these to fetch logic or planner logic.
#MIN_COMMENT_SCORE = 0.0
#MIN_POST_UPVOTES = 10
#MIN_POST_NSFW = False
#MIN_COMMENT_NSFW = False