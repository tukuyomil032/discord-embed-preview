from io import BytesIO
from typing import List

import aiohttp
import discord
from PIL import Image  # type: ignore[reportMissingImports]


async def compose_grid_image(attachments: List[discord.Attachment]) -> discord.File:
    """Download up to 4 image attachments and compose a 2x2 grid PNG file (small thumbnails)."""
    tile = 320
    size = (tile * 2, tile * 2)

    imgs: List[Image.Image] = []
    async with aiohttp.ClientSession() as session:
        for a in attachments[:4]:
            try:
                async with session.get(a.url) as resp:
                    data = await resp.read()
                    img = Image.open(BytesIO(data)).convert("RGBA")
                    img.thumbnail((tile, tile), Image.LANCZOS)
                    imgs.append(img)
            except Exception:
                continue

    canvas = Image.new("RGBA", size, (54, 57, 63, 255))
    positions = [(0, 0), (tile, 0), (0, tile), (tile, tile)]
    for idx, img in enumerate(imgs):
        x, y = positions[idx]
        w, h = img.size
        offset = (x + (tile - w) // 2, y + (tile - h) // 2)
        canvas.paste(img, offset, img)

    bio = BytesIO()
    canvas.save(bio, format="PNG")
    bio.seek(0)
    return discord.File(bio, filename="grid.png")


def make_message_buttons(original_url: str) -> discord.ui.View:
    """Return a View with a colored primary button that replies the URL ephemerally and a direct link button."""
    view = discord.ui.View()

    coloured_btn = discord.ui.Button(
        label="Open original message", style=discord.ButtonStyle.primary
    )

    async def _coloured_callback(interaction: discord.Interaction):
        await interaction.response.send_message(original_url, ephemeral=True)

    coloured_btn.callback = _coloured_callback
    view.add_item(coloured_btn)

    try:
        link_btn = discord.ui.Button(
            label="Direct link", url=original_url, style=discord.ButtonStyle.link
        )
        view.add_item(link_btn)
    except Exception:
        pass

    return view
