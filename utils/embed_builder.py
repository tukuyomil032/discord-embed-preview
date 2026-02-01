from typing import Any, List

import discord


def create_preview_embed(message: discord.Message, channel: Any) -> discord.Embed:
    """Create an embed preview of a message (moved from message_preview.py)."""
    embed = discord.Embed(
        description=message.content or "*[No content]*",
        color=0x5865F2,
        timestamp=message.created_at,
    )

    embed.set_author(
        name=message.author.display_name or "Unknown",
        icon_url=str(message.author.display_avatar.url)
        if message.author.display_avatar
        else None,
    )

    guild_name = message.guild.name if message.guild else "Unknown"
    embed.set_footer(
        text=f"#{channel.name} | {guild_name}",
        icon_url=str(message.guild.icon.url)
        if message.guild and message.guild.icon
        else None,
    )

    if message.reactions:
        reactions_text = " ".join(
            f"{str(reaction.emoji)} {reaction.count}" for reaction in message.reactions
        )
        if reactions_text:
            embed.add_field(name="Reactions", value=reactions_text, inline=False)

    attachment_names = [
        a.filename
        for a in message.attachments
        if not (a.content_type and a.content_type.startswith("image/"))
    ]
    if attachment_names:
        embed.add_field(
            name="Attachments", value="\n".join(attachment_names), inline=False
        )

    return embed
