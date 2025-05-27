import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv("TOKEN")
STATUS = os.getenv("STATUS")


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True 

class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("/"), intents=intents)
        self.synced = False  

    async def setup_hook(self):
        from cogs.ticket import OpenTicketView
        self.add_view(OpenTicketView(self, {"admin_roles": []}))
        await self.load_extension("cogs.ticket")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name=STATUS))
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")

        if not self.synced:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash command(s)")
            self.synced = True

bot = TicketBot()
bot.run(TOKEN)
