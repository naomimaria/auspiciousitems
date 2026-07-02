#!/usr/bin/env python3
"""
AuspiciousItems bot — posts generated horoscopes/spells to Tumblr and Bluesky.
Reads grammar from grammar.json, generates a post, and sends it to both platforms.

Required environment variables:
    TUMBLR_CONSUMER_KEY
    TUMBLR_CONSUMER_SECRET
    TUMBLR_OAUTH_TOKEN
    TUMBLR_OAUTH_SECRET
    TUMBLR_BLOG_NAME        e.g. "auspiciousitems.tumblr.com"
    BLUESKY_HANDLE          e.g. "auspiciousitems.bsky.social"
    BLUESKY_APP_PASSWORD
"""

import json
import os
import sys
import tracery
from tracery.modifiers import base_english
import pytumblr
from atproto import Client as BskyClient


# --- Grammar data (loaded once, used for tag detection) ---
WESTERN_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

CHINESE_SIGNS = [
    "rat", "ox", "tiger", "rabbit", "dragon", "snake",
    "horse", "goat", "monkey", "rooster", "dog", "pig"
]

WESTERN_ELEMENTS = ["fire signs", "water signs", "earth signs", "air signs"]
MODALITIES = ["cardinal signs", "fixed signs", "mutable signs"]
MOON_PHASES = [
    "new moon", "waxing crescent moon", "first quarter moon", "waxing gibbous moon",
    "full moon", "waning gibbous moon", "half moon", "waning crescent moon"
]

# Templates that are spell/ritual in nature — detected by keywords in the generated text
SPELL_KEYWORDS = [
    "poultice", "salve", "tincture", "elixir", "smudge stick",
    "scatter", "burn", "steep", "soak", "concoction", "sprinkle",
    "apply", "smear", "mix an", "drink a", "sleep with", "place a",
    "jar full", "bundle"
]

TECH_KEYWORDS = [
    "internet karma", "profile", "selfie", "follow a new person",
    "posting on", "purchased online", "filter on it"
]


def load_grammar(path="grammar.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_post(grammar_data):
    grammar = tracery.Grammar(grammar_data)
    grammar.add_modifiers(base_english)
    return grammar.flatten("#origin#")


def detect_tags(text):
    """
    Analyse the generated text and return two tag lists:
    tumblr_tags — full tag set for Tumblr
    bluesky_tags — reduced tag set for Bluesky (appended inline as hashtags)
    """
    lower = text.lower()

    tumblr = []
    bluesky = []

    # --- Western zodiac sign ---
    matched_sign = None
    for sign in WESTERN_SIGNS:
        if lower.startswith(sign) or f", {sign}" in lower or f" {sign}," in lower:
            matched_sign = sign
            break
    if matched_sign:
        tumblr += ["horoscope", "astrology", matched_sign]
        bluesky += ["horoscope", "astrology", matched_sign]

    # --- Western elements ---
    matched_element = None
    for element in WESTERN_ELEMENTS:
        if element in lower:
            matched_element = element
            break
    if matched_element:
        tumblr += ["horoscope", "astrology", matched_element]
        if not bluesky:
            bluesky += ["horoscope", "astrology"]

    # --- Modalities ---
    matched_modality = None
    for modality in MODALITIES:
        if modality in lower:
            matched_modality = modality
            break
    if matched_modality:
        tumblr += ["horoscope", "astrology", matched_modality]
        if not bluesky:
            bluesky += ["horoscope", "astrology"]

    # --- Planets / retrograde / prograde ---
    has_planet = any(p in lower for p in [
        "mercury", "venus", "mars", "jupiter", "saturn",
        "uranus", "neptune", "pluto", "exoplanet", "meteorite",
        "asteroid", "comet"
    ])
    if has_planet:
        motion = "retrograde" if "retrograde" in lower else "prograde" if "prograde" in lower else None
        tumblr += ["horoscope", "astrology"]
        if motion:
            tumblr.append(motion)
        if not bluesky:
            bluesky += ["horoscope", "astrology"]

    # --- Chinese zodiac ---
    matched_chinese = None
    for animal in CHINESE_SIGNS:
        if animal in lower:
            matched_chinese = animal
            break
    if matched_chinese:
        tumblr += ["chinese zodiac", "lunar horoscope", f"year of the {matched_chinese}"]
        bluesky += ["chinese zodiac", matched_chinese]

    # --- Moon phases ---
    matched_moon = None
    for phase in MOON_PHASES:
        if phase in lower:
            matched_moon = phase
            break
    if matched_moon:
        tumblr += ["horoscope", "astrology", "moon phase", matched_moon]
        if not bluesky:
            bluesky += ["horoscope", "astrology"]

    # --- Tech/internet rituals (check before spells — more specific) ---
    is_tech = any(kw in lower for kw in TECH_KEYWORDS)
    if is_tech:
        tumblr += ["spells", "witchy", "bruja", "social media"]
        bluesky += ["spells"]

    # --- Spells / potions / rituals ---
    is_spell = any(kw in lower for kw in SPELL_KEYWORDS)
    if is_spell and not is_tech:
        tumblr += ["spells", "witchy", "bruja"]
        bluesky += ["spells"]

    # --- Fallback: general if nothing matched yet ---
    if not tumblr:
        tumblr += ["horoscope", "astrology"]
    if not bluesky:
        bluesky += ["horoscope", "astrology"]

    # Deduplicate while preserving order, then append bot last
    def dedup(lst):
        seen = set()
        out = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    tumblr = dedup(tumblr) + ["bot"]
    bluesky = dedup(bluesky) + ["bot"]

    return tumblr, bluesky


def post_to_tumblr(text, tags):
    client = pytumblr.TumblrRestClient(
        os.environ["TUMBLR_CONSUMER_KEY"],
        os.environ["TUMBLR_CONSUMER_SECRET"],
        os.environ["TUMBLR_OAUTH_TOKEN"],
        os.environ["TUMBLR_OAUTH_SECRET"],
    )
    blog = os.environ["TUMBLR_BLOG_NAME"]
    response = client.create_text(blog, body=text, tags=tags)
    if "id" in response:
        print(f"✓ Tumblr: posted (id {response['id']}) tags: {tags}")
    else:
        print(f"✗ Tumblr error: {response}", file=sys.stderr)
        sys.exit(1)


def post_to_bluesky(text, tags):
    # Append hashtags inline after sparkle emoji
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags)
    full_text = f"{text} ✨ {hashtags}"

    client = BskyClient()
    client.login(os.environ["BLUESKY_HANDLE"], os.environ["BLUESKY_APP_PASSWORD"])
    client.send_post(text=full_text)
    print(f"✓ Bluesky: posted with tags: {tags}")


def main():
    grammar_data = load_grammar()
    post_text = generate_post(grammar_data)
    tumblr_tags, bluesky_tags = detect_tags(post_text)

    print(f"Generated: {post_text}")
    print(f"Tumblr tags: {tumblr_tags}")
    print(f"Bluesky tags: {bluesky_tags}\n")

    errors = []

    try:
        post_to_tumblr(post_text, tumblr_tags)
    except Exception as e:
        print(f"✗ Tumblr failed: {e}", file=sys.stderr)
        errors.append("tumblr")

    try:
        post_to_bluesky(post_text, bluesky_tags)
    except Exception as e:
        print(f"✗ Bluesky failed: {e}", file=sys.stderr)
        errors.append("bluesky")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
