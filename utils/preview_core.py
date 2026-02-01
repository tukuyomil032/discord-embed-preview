import logging
from typing import Optional

import discord
from discord.ext import commands

from .embed_builder import create_preview_embed
from .fetcher import fetch_target_message
from .helpers import compose_grid_image, make_message_buttons

logger = logging.getLogger(__name__)


async def preview_message_link(
    bot: commands.Bot,
    source_message: discord.Message,
    guild_id: int,
    channel_id: int,
    message_id: int,
) -> None:
    """Fetch a message and send preview reply to source_message.

    This is extracted from the Cog to reduce file size.
    """
    try:
        target_message, channel, guild = await fetch_target_message(
            bot, guild_id, channel_id, message_id
        )
        if not target_message:
            logger.warning(
                f"Message {message_id} not found in channel/thread {channel_id} (guild {guild_id})"
            )
            return

        base_embed = create_preview_embed(target_message, channel)

        # Collect attachments
        image_attachments = []
        video_attachments = []
        for a in target_message.attachments:
            ctype = a.content_type or ""
            if ctype.startswith("image/"):
                image_attachments.append(a)
            elif ctype.startswith("video/"):
                video_attachments.append(a)

        embeds = []

        if image_attachments:
            base_embed.set_image(url=image_attachments[0].url)
            for att in image_attachments[1:4]:
                img_embed = discord.Embed(color=0x5865F2)
                img_embed.set_image(url=att.url)
                embeds.append(img_embed)

        if video_attachments:
            video_links = "\n".join(f"[Video]({v.url})" for v in video_attachments[:4])
            base_embed.add_field(name="Videos", value=video_links, inline=False)

        view = None
        try:
            original_url = (
                f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            )
            view = make_message_buttons(original_url)
        except Exception:
            view = None

        files = None
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
            send_kwargs["embeds"] = [base_embed] + embeds if embeds else [base_embed]
            if view:
                send_kwargs["view"] = view
            if files:
                await source_message.reply(files=files, **send_kwargs)
            else:
                await source_message.reply(**send_kwargs)
        except discord.HTTPException as e:
            logger.error(f"Failed to send preview: {e}")

    except discord.NotFound:
        logger.warning(f"Message {message_id} not found in channel {channel_id}")
    except discord.Forbidden:
        logger.warning(
            f"No permission to view message {message_id} in channel {channel_id}"
        )
    except Exception as e:
        logger.error(f"Error previewing message link: {e}")
