"""
Discord Bot Main File
Handles bot initialization and loading of cogs
"""

import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    logger.error("DISCORD_TOKEN not found in .env file")
    exit(1)

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord"""
    logger.info(f"Bot logged in as {bot.user}")
    user = bot.user
    if user is not None:
        logger.info(f"Bot ID: {user.id}")
    else:
        logger.info("Bot ID: None (bot.user is not available yet)")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


async def load_cogs():
    """Load all cogs from the cogs directory"""
    cogs_dir = Path(__file__).parent / "cogs"

    if not cogs_dir.exists():
        logger.warning(f"Cogs directory not found at {cogs_dir}")
        return

    for filename in cogs_dir.glob("*.py"):
        if filename.name.startswith("_"):
            continue

        try:
            text = filename.read_text(encoding="utf-8")
        except Exception:
            logger.debug(f"Skipping unreadable file: {filename.name}")
            continue

        # Only attempt to load modules that define a Cog setup function
        if ("def setup(" in text) or ("async def setup(" in text):
            cog_name = filename.stem
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")
        else:
            logger.debug(f"Skipping non-cog module: {filename.name}")


async def main() -> None:
    """Main function to start the bot"""
    async with bot:
        await load_cogs()
        if not isinstance(TOKEN, str):
            logger.error("DISCORD_TOKEN is not a valid string")
            return

        try:
            await bot.start(TOKEN)
        except discord.errors.PrivilegedIntentsRequired:
            logger.error(
                "Privileged intents are required but not enabled.\n"
                "Enable the privileged intents (Message Content / Server Members / Presence)\n"
                "in the Discord Developer Portal for your application and restart the bot:\n"
                "1. Go to https://discord.com/developers/applications\n"
                "2. Select your application -> Bot -> Privileged Gateway Intents\n"
                "3. Enable 'Message Content Intent' (and others if needed) -> Save Changes\n"
            )
            return


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
