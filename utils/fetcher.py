from typing import Any, Optional, Tuple

import discord
from discord.ext import commands


async def fetch_target_message(
    bot: commands.Bot, guild_id: int, channel_id: int, message_id: int
) -> Tuple[Optional[discord.Message], Optional[Any], Optional[discord.Guild]]:
    """Attempt to locate and fetch a message by guild/channel/message ids.

    Returns tuple (message, channel, guild) or (None, None, None) if not found.
    """
    guild = bot.get_guild(guild_id)
    if not guild:
        return None, None, None

    # Resolve channel
    channel = guild.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            return None, None, guild

    # Try direct fetch
    target_message: Optional[discord.Message] = None
    fetch_msg = getattr(channel, "fetch_message", None)
    if fetch_msg:
        try:
            target_message = await fetch_msg(message_id)
        except Exception:
            target_message = None

    # If not found, search threads (active -> public archived -> private archived)
    if target_message is None:
        try:
            # active threads
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
                msg = await fetch_thread_msg(message_id)
                target_message = msg
                channel = thread
                break
            except Exception:
                continue

        if target_message is None:
            # public archived
            try:
                fetch_pub = getattr(guild, "fetch_public_archived_threads", None)
                if fetch_pub:
                    archived = await fetch_pub(limit=100)
                    athreads = getattr(archived, "threads", [])
                else:
                    athreads = []
            except Exception:
                athreads = []

            for thread in athreads:
                fetch_thread_msg = getattr(thread, "fetch_message", None)
                if not fetch_thread_msg:
                    continue
                try:
                    msg = await fetch_thread_msg(message_id)
                    target_message = msg
                    channel = thread
                    break
                except Exception:
                    continue

        if target_message is None:
            # private archived
            try:
                fetch_priv = getattr(guild, "fetch_private_archived_threads", None)
                if fetch_priv:
                    archived_priv = await fetch_priv(limit=100)
                    patr = getattr(archived_priv, "threads", [])
                else:
                    patr = []
            except Exception:
                patr = []
            for thread in patr:
                fetch_thread_msg = getattr(thread, "fetch_message", None)
                if not fetch_thread_msg:
                    continue
                try:
                    msg = await fetch_thread_msg(message_id)
                    target_message = msg
                    channel = thread
                    break
                except Exception:
                    continue

    return target_message, channel, guild
