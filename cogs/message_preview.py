"""
Message Preview Cog
Handles detection and preview of Discord message links
"""

import logging
import os
import re
from io import BytesIO
from typing import Any, List, Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image  # type: ignore[reportMissingImports]

from utils.embed_builder import create_preview_embed
from utils.fetcher import fetch_target_message
from utils.helpers import compose_grid_image, make_message_buttons
from utils.preview_core import preview_message_link as preview_core_link

logger = logging.getLogger(__name__)

# Pattern to match Discord message links
# Formats:
# - https://discord.com/channels/{guild_id}/{channel_id}/{message_id}
# - https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id}
MESSAGE_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord(?:app)?\.com|canary\.discord\.com|ptb\.discord\.com)/"
    r"channels/(\d+)/(\d+)/(\d+)"
)


class MessagePreview(commands.Cog):
    """Cog for previewing Discord message links"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen to all messages and check for Discord message links"""

        # Don't process bot's own messages
        if message.author.bot:
            return
        # If bot user not ready yet, skip
        if self.bot.user is None:
            await self.bot.process_commands(message)
            return

        # Check for links, but only react to raw links when message mentions bot at start
        links = MESSAGE_LINK_PATTERN.findall(message.content)

        if not links:
            await self.bot.process_commands(message)
            return

        # require mention at start for plain messages: formats <@id> or <@!id> followed by space
        mention1 = f"<@{self.bot.user.id}> "
        mention2 = f"<@!{self.bot.user.id}> "
        if not (
            message.content.startswith(mention1) or message.content.startswith(mention2)
        ):
            # do not auto-respond to plain links unless mentioned
            await self.bot.process_commands(message)
            return

        # Process each message link found
        for guild_id, channel_id, message_id in links:
            await preview_core_link(
                self.bot, message, int(guild_id), int(channel_id), int(message_id)
            )

        await self.bot.process_commands(message)

    # Embed construction moved to `cogs/embed_builder.py` (function `create_preview_embed`).
    # Use `from .embed_builder import create_preview_embed` at module level.

    # context menu implementation removed per user request

    # image composition moved to cogs/helpers.py (compose_grid_image)

    # Slash command to preview a message link
    @app_commands.command(name="preview", description="Preview a Discord message link")
    async def slash_preview(self, interaction: discord.Interaction, link: str) -> None:
        await interaction.response.defer()
        match = MESSAGE_LINK_PATTERN.findall(link)
        if not match:
            await interaction.followup.send("Invalid message link.", ephemeral=True)
            return
        guild_id, channel_id, message_id = match[0]
        try:
            # fetch target message and reuse preview logic but send as followup
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                await interaction.followup.send("Guild not found.", ephemeral=True)
                return
            channel = guild.get_channel(int(channel_id))
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(int(channel_id))
                except Exception:
                    await interaction.followup.send(
                        "Channel not found.", ephemeral=True
                    )
                    return

            target_message = None
            fetch_msg = getattr(channel, "fetch_message", None)
            if fetch_msg:
                try:
                    target_message = await fetch_msg(int(message_id))
                except Exception:
                    target_message = None

            if target_message is None:
                # try threads similar to preview_message_link
                try:
                    fetch_active = getattr(guild, "fetch_active_threads", None)
                    if fetch_active:
                        active = await fetch_active()
                        threads = getattr(active, "threads", [])
                    else:
                        threads = []
                except Exception:
                    threads = []
                for thread in threads:
                    fetch_thread_msg = getattr(thread, "fetch_message", None)
                    if not fetch_thread_msg:
                        continue
                    try:
                        msg = await fetch_thread_msg(int(message_id))
                        target_message = msg
                        channel = thread
                        break
                    except Exception:
                        continue

            if target_message is None:
                await interaction.followup.send("Message not found.", ephemeral=True)
                return

            # Build preview (reuse code path partially)
            base_embed = create_preview_embed(target_message, channel)
            # prepare view/buttons for original message
            view = None
            try:
                original_url = (
                    f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
                )
                view = make_message_buttons(original_url)
            except Exception:
                view = None
            image_attachments = [
                a
                for a in target_message.attachments
                if (a.content_type or "").startswith("image/")
            ]
            embeds: List[discord.Embed] = []
            files = None

            # Collect video attachments separately
            video_attachments = [
                a
                for a in target_message.attachments
                if (a.content_type or "").startswith("video/")
            ]

            # If there are images, set the first image on the base embed and add up to 3 more as embeds
            if image_attachments:
                base_embed.set_image(url=image_attachments[0].url)
                for att in image_attachments[1:4]:
                    img_embed = discord.Embed(color=0x5865F2)
                    img_embed.set_image(url=att.url)
                    embeds.append(img_embed)

            # Videos: add links
            if video_attachments:
                video_links = "\n".join(
                    f"[Video]({v.url})" for v in video_attachments[:4]
                )
                base_embed.add_field(name="Videos", value=video_links, inline=False)

            # If multiple images, try composing into a grid and attach as a single file
            if len(image_attachments) > 1:
                try:
                    tiles = image_attachments[:4]
                    composed = await compose_grid_image(tiles)
                    files = [composed]
                    base_embed.set_image(url="attachment://grid.png")
                    embeds = []
                except Exception as e:
                    logger.debug(f"Failed to compose grid image: {e}")

            try:
                send_kwargs = {}
                send_kwargs["embeds"] = (
                    [base_embed] + embeds if embeds else [base_embed]
                )
                if view:
                    send_kwargs["view"] = view
                if files:
                    await interaction.followup.send(files=files, **send_kwargs)
                else:
                    await interaction.followup.send(**send_kwargs)
            except Exception as e:
                logger.debug(f"Failed to send followup preview: {e}")

        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Setup function to load the cog"""
    mp = MessagePreview(bot)
    await bot.add_cog(mp)
    # Register slash command on the bot tree (global registration)
    try:
        bot.tree.add_command(mp.slash_preview)
    except Exception:
        pass
