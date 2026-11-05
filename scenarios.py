"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""

_OWN_WRITING = [
    "A false accusation can harm a writer more than a missed AI-generated passage harms the site, so the high-confidence AI label should be rare on work I know is mine. Requiring the limit in every trial prevents a good average from hiding an inconsistent run.",
    "A measurable gap shows the combined score distinguishes the two calibration groups, while a 0.20 margin is large enough to be useful rather than a tiny difference lost in model variation.",
    "All three labels need to be reachable for the unsure band to serve as a real alternative to an accusation, not just an unused code path. Repeating the same samples checks that model variation does not make a label disappear.",
    "A writer needs a reliable way to challenge a wrong result, and an append-only record preserves both the original decision and the review request for later follow-up.",
    "Invalid input should be rejected clearly before it reaches the model, while a documented size limit prevents oversized submissions from consuming unbounded resources. Keeping the service healthy after these requests guards against malformed input crashing the route or process.",
    "A writer sends POST /submit with JSON containing text and creator_id. The route checks the JSON fields and rejects blank or over-100,000-character text; the detector rejects text that is too short to score. The model signal measures how predictable the text is, while the style signal measures sentence-length variation and vocabulary repetition.",
    "The route combines the two scores with a weighted average, then maps the result to a human, unsure, or AI label. It generates a content_id and writes the scores and decision to the audit log. A writer can later send that ID and their reasoning to POST /appeal, where the appeal is appended with under_review status.",
    "Predictability does not establish authorship. Plain conventional human writing can be predictable, while unusual human writing can surprise the model. The signal only scores the first 400 tokens, so the rest of a long submission does not affect that measurement.",
    "The style signal uses sentence-length variation and vocabulary repetition, and it reports punctuation density for inspection without including it in the score. It cannot understand meaning or verify authorship. Genre, text length, quotations, typos, and sentence splitting can all change these measurements without changing who wrote the text.",
    "I ran the CLI and both signals on the same passages, retained punctuation as a diagnostic rather than a scored measure, and chose 0.60 model / 0.40 style weights to keep the shallow style signal from dominating. I recorded the observed split and formula in Signals and Scoring.",
]

_CLEARLY_AI = [
    "The implementation of this framework requires careful consideration of several interconnected factors. First, the system must establish a consistent process for evaluating each submission. Additionally, the resulting information should be organized in a manner that supports reliable review and ongoing improvement.",
    "Effective communication is an essential component of successful collaboration. By establishing clear expectations and maintaining a structured workflow, teams can reduce uncertainty and improve the quality of their outcomes. This approach also enables participants to identify potential challenges at an earlier stage.",
    "The analysis demonstrates that a comprehensive approach can provide meaningful benefits. In particular, combining multiple sources of information allows decision makers to develop a more balanced understanding of the situation. As a result, organizations can make choices that are both informed and sustainable.",
    "A well-designed process should account for both immediate requirements and long-term objectives. The first step is to identify the relevant constraints, after which appropriate methods can be selected and applied. Regular evaluation then ensures that the process continues to meet its intended goals.",
    "Technology can support a wide range of activities when it is implemented thoughtfully. However, successful implementation depends on careful planning, consistent execution, and meaningful evaluation. These considerations help ensure that the final solution remains useful, accessible, and responsive to changing needs.",
]

_CALIBRATION = [
    _CLEARLY_AI[0],
    _OWN_WRITING[0],
    "The implementation of this system requires careful consideration of several important factors. First, the service should validate incoming data to ensure reliable processing. Additionally, each stage should provide consistent results and maintain clear records. By following these principles, the system can deliver an effective and user-friendly experience.",
    _OWN_WRITING[7],
    _CLEARLY_AI[2],
]

SCENARIOS = [
    {
        "name": "my own writing",
        "criterion": 1,
        "texts": _OWN_WRITING,
    },
    {
        "name": "AI versus human score spread",
        "criterion": 2,
        "texts": _CLEARLY_AI + _OWN_WRITING[:5],
        "groups": ["clearly AI"] * 5 + ["clearly human"] * 5,
    },
    {
        "name": "label coverage",
        "criterion": 3,
        "texts": _CALIBRATION,
        "groups": ["AI-like", "human-written", "borderline", "human-written", "AI-like"],
    },
    {
        "name": "appeal round-trip",
        "criterion": 4,
        "texts": _OWN_WRITING[5:],
        "appeal_reasoning": "I wrote this submission myself and would like a person to review the result.",
    },
    {
        "name": "malformed input and service health",
        "criterion": 5,
        "bodies": [
            {"creator_id": "eval_bad_missing"},
            {"text": None, "creator_id": "eval_bad_null"},
            {"text": 12345, "creator_id": "eval_bad_number"},
            {"text": "   \t", "creator_id": "eval_bad_blank"},
            {"text": "x" * 100_001, "creator_id": "eval_bad_oversized"},
        ],
        "health_after": True,
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    criteria = [scenario.get("criterion") for scenario in SCENARIOS]
    if sorted(criteria) != [1, 2, 3, 4, 5]:
        problems.append("scenarios must cover criteria 1 through 5 exactly once")

    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        groups = scenario.get("groups")
        if groups and len(groups) != len(texts):
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has a different number "
                "of group labels and texts"
            )

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
