import discord
import os
from datetime import datetime

async def generate_transcript(channel: discord.TextChannel) -> str:
    lines = []

    async for msg in channel.history(limit=None, oldest_first=True):
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
        content = msg.content if msg.content else "[Non-text content]"
        lines.append(f"[{timestamp}] {msg.author.display_name}: {content}")

    filename = f"transcripts/{channel.name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt"
    os.makedirs("transcripts", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filename
