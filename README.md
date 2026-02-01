# Discord Embed Preview Bot

This bot previews Discord message links by fetching the referenced message and sending a preview embed.

## Features

- Automatically detects Discord message links in messages
- Shows message content in an embed preview
- Displays attached images (supports composing up to 4 images into a 2x2 grid)
- Preview messages are persistent (not auto-deleted)

## Setup

1. Create file `.env`.
2. Add your discord bot token to `.env`:

```env
DISCORD_TOKEN=your_bot_token_here
```

3. Install dependencies with Poetry:

```bash
poetry install
```

## Run

```bash
poetry run python main.py
```

## Getting a Bot Token

- Open the Discord Developer Portal: https://discord.com/developers
- Create an application and add a Bot; copy the bot token
- Paste the token into the `.env` file

## Notes

- This project uses Poetry for dependency management. Committing `poetry.lock` is recommended for reproducible installs in CI and production.
- If you run the bot in a tmux session, helper scripts are available under `scripts/`.
