"""
Simple lexicon-based sentiment scorer.

This is intentionally dependency-free so the project runs out of the box.
For your report / a stronger version, swap this out for:
  - NLTK's VADER (great for short social-media-style text), or
  - a pretrained transformer via Hugging Face
    (e.g. `distilbert-base-uncased-finetuned-sst-2-english`)
Both are drop-in replacements for `analyze(text)` below — just make sure
they return a float in roughly [-1, 1].
"""

import re

POSITIVE_WORDS = {
    "love", "great", "amazing", "awesome", "fantastic", "excellent", "good",
    "best", "brilliant", "incredible", "perfect", "beautiful", "wonderful",
    "enjoy", "enjoyed", "fun", "happy", "exciting", "excited", "masterpiece",
    "favorite", "recommend", "impressive", "outstanding", "solid", "banger",
}

NEGATIVE_WORDS = {
    "hate", "terrible", "awful", "bad", "worst", "boring", "disappointing",
    "disappointed", "poor", "waste", "mediocre", "dull", "annoying", "flop",
    "overrated", "trash", "horrible", "sad", "cringe", "bland", "weak",
}

NEGATIONS = {"not", "never", "no", "n't", "dont", "don't", "isn't", "wasn't"}


def analyze(text):
    """Return a sentiment score in [-1, 1]. Positive = favorable, negative = unfavorable."""
    if not text:
        return 0.0

    words = re.findall(r"[a-z']+", text.lower())
    score = 0
    negate_next = False

    for word in words:
        if word in NEGATIONS:
            negate_next = True
            continue

        value = 0
        if word in POSITIVE_WORDS:
            value = 1
        elif word in NEGATIVE_WORDS:
            value = -1

        if value != 0:
            if negate_next:
                value = -value
            score += value
            negate_next = False

    if len(words) == 0:
        return 0.0

    # Normalize roughly into [-1, 1] based on sentiment-word density.
    normalized = max(-1.0, min(1.0, score / max(3, len(words) ** 0.5)))
    return round(normalized, 3)


def label(score):
    """Turn a numeric score into a human-readable label for the UI."""
    if score > 0.15:
        return "positive"
    if score < -0.15:
        return "negative"
    return "neutral"
