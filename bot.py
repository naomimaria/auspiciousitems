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


def load_grammar(path="grammar.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_post(grammar_data):
    grammar = tracery.Grammar(grammar_data)
    grammar.add_modifiers(base_english)
    return grammar.flatten("#origin#")


def post_to_tumblr(text):
    client = pytumblr.TumblrRestClient(
        os.environ["TUMBLR_CONSUMER_KEY"],
        os.environ["TUMBLR_CONSUMER_SECRET"],
        os.environ["TUMBLR_OAUTH_TOKEN"],
        os.environ["TUMBLR_OAUTH_SECRET"],
    )
    blog = os.environ["TUMBLR_BLOG_NAME"]
    response = client.create_text(blog, body=text, tags=["horoscope", "astrology", "spells", "bot"])
    if "id" in response:
        print(f"✓ Tumblr: posted (id {response['id']})")
    else:
        print(f"✗ Tumblr error: {response}", file=sys.stderr)
        sys.exit(1)


def post_to_bluesky(text):
    client = BskyClient()
    client.login(os.environ["BLUESKY_HANDLE"], os.environ["BLUESKY_APP_PASSWORD"])
    client.send_post(text=text)
    print("✓ Bluesky: posted")


def main():
    grammar_data = load_grammar()
    post_text = generate_post(grammar_data)

    print(f"Generated: {post_text}\n")

    errors = []

    try:
        post_to_tumblr(post_text)
    except Exception as e:
        print(f"✗ Tumblr failed: {e}", file=sys.stderr)
        errors.append("tumblr")

    try:
        post_to_bluesky(post_text)
    except Exception as e:
        print(f"✗ Bluesky failed: {e}", file=sys.stderr)
        errors.append("bluesky")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
