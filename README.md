# AuspiciousItems ✨

A horoscope and spell bot that posts to Tumblr and Bluesky hourly.
Generated using [Tracery](https://tracery.io/) grammar by Kate Compton.

## Setup

### 1. Create your accounts

- A **Tumblr** blog for the bot
- A **Bluesky** account for the bot

### 2. Get your API credentials

**Tumblr:**
1. Go to https://www.tumblr.com/oauth/apps and register a new application
2. Note your **Consumer Key** and **Consumer Secret**
3. You'll need to do a one-time OAuth dance to get your token and secret —
   the easiest way is to use [this script](https://github.com/tumblr/pytumblr#usage)
   or run `python get_tumblr_tokens.py` (see below)

**Bluesky:**
1. Go to Settings → Privacy and Security → App Passwords
2. Create a new app password — use this instead of your real password

### 3. Add secrets to GitHub

In your repo: Settings → Secrets and variables → Actions → New repository secret

Add all seven of these:

| Secret name | Value |
|---|---|
| `TUMBLR_CONSUMER_KEY` | From Tumblr app registration |
| `TUMBLR_CONSUMER_SECRET` | From Tumblr app registration |
| `TUMBLR_OAUTH_TOKEN` | From OAuth flow |
| `TUMBLR_OAUTH_SECRET` | From OAuth flow |
| `TUMBLR_BLOG_NAME` | e.g. `auspiciousitems.tumblr.com` |
| `BLUESKY_HANDLE` | e.g. `auspiciousitems.bsky.social` |
| `BLUESKY_APP_PASSWORD` | From Bluesky app passwords |

### 4. Enable the workflow

GitHub Actions may need to be enabled on your repo.
Go to the **Actions** tab and enable workflows if prompted.

To test immediately, go to Actions → Post Horoscope → Run workflow.

## Editing the grammar

All words and templates live in `grammar.json`. Edit freely and commit —
the bot will use the updated grammar on its next run.

## Posting frequency

The workflow runs every hour. To change this, edit the `cron` line in
`.github/workflows/post.yml`. Use https://crontab.guru to build cron expressions.

Examples:
- Every 2 hours: `0 */2 * * *`
- Twice a day: `0 9,21 * * *`
- Once a day at noon: `0 12 * * *`
