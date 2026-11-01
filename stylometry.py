"""
Signal two: the style signal.

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are implemented below. The style signal combines sentence
length variation and vocabulary repetition; punctuation density is reported
for inspection but is not included because its direction is not reliable by
itself.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies.

    Returns:
        A coefficient of variation (standard deviation divided by mean sentence
        length). Higher values mean more variation.

    A hint on what you're reaching for: the standard deviation of sentence
    lengths, probably divided by the mean so a long text and a short one are
    comparable. `statistics.stdev` is imported for you.

    Watch the edge case: a one-sentence submission has no spread at all, and
    `stdev` raises on fewer than two values. Decide what that should return
    before the attack set decides for you.
    """
    lengths = [len(words(sentence)) for sentence in sentences(text)]
    if len(lengths) < 2:
        return 0.0

    mean_length = statistics.mean(lengths)
    if mean_length == 0:
        return 0.0
    return statistics.stdev(lengths) / mean_length


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat. Two texts of different lengths aren't
    directly comparable on it, and if your test inputs vary a lot in length,
    that alone can look like a signal.
    """
    tokens = words(text)
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    How much common punctuation appears relative to word count.

    Returns:
        A float. Whether you count all punctuation or only some kinds — commas,
        semicolons, dashes — is a real choice. Semicolons and em dashes are
        more interesting than full stops, because they vary more between
        writers.
    """
    token_count = len(words(text))
    if token_count == 0:
        return 0.0
    punctuation_count = len(re.findall(r"[,;:!?—–-]", text))
    return punctuation_count / token_count


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

     Average two bounded AI-likelihood measures: low sentence-length variation
     and repeated vocabulary point upward. Punctuation density is available as
     a diagnostic, but is not scored because density alone has no stable
     human-versus-AI direction.
    """
    tokens = words(text)
    if not tokens:
        return 0.5

    sentence_parts = sentences(text)
    if len(sentence_parts) < 2:
        variation_ai = 0.5
    else:
        variation = sentence_length_spread(text)
        variation_ai = 1.0 / (1.0 + variation)

    repetition_ai = 1.0 - type_token_ratio(text)
    return round((variation_ai + repetition_ai) / 2.0, 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\nHigher style_signal means more likely AI.")
