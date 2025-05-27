import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from utils.transcript import generate_transcript

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "data/config.json"
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w") as f:
                json.dump({"admin_roles": []}, f)
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    @app_commands.command(name="ticket-setup", description="Setup the ticket system (Owner only)")
    async def ticket_setup(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Only the server owner can run this command.", ephemeral=True)

        category = await interaction.guild.create_category("🎟️ Tickets")
        ticket_channel = await category.create_text_channel("🎫│tickets")
        log_channel = await category.create_text_channel("🧾│ticket-log")

        overwrite = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        await ticket_channel.edit(overwrites=overwrite)
        await log_channel.edit(overwrites=overwrite)

        await interaction.response.send_message(
            "✅ Ticket channels created.\nPlease configure the permissions and use `/ticket-message` to send the ticket embed.",
            ephemeral=True
        )

        info_embed = discord.Embed(
            title="📌 Ticket System Setup",
            description="Use `/ticket-admin <role>` to add ticket managers.\nUse `/ticket-message` to post the ticket creation message.\nAdmins can manage opened tickets.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=info_embed)

    @app_commands.command(name="ticket-admin", description="Add a role as ticket admin")
    @app_commands.describe(role="Role to add as ticket admin")
    async def ticket_admin(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Only the server owner can run this command.", ephemeral=True)

        if role.id not in self.config["admin_roles"]:
            self.config["admin_roles"].append(role.id)
            self.save_config()
            await interaction.response.send_message(f"✅ {role.mention} added as ticket admin.")
        else:
            await interaction.response.send_message("That role is already a ticket admin.", ephemeral=True)

    @app_commands.command(name="ticket-remove-admin", description="Remove a role from ticket admins")
    @app_commands.describe(role="Role to remove from ticket admin")
    async def ticket_remove_admin(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Only the server owner can run this command.", ephemeral=True)

        if role.id in self.config["admin_roles"]:
            self.config["admin_roles"].remove(role.id)
            self.save_config()
            await interaction.response.send_message(f"🗑️ {role.mention} removed from ticket admins.")
        else:
            await interaction.response.send_message("That role is not in the ticket admin list.", ephemeral=True)

    @app_commands.command(name="ticket-message", description="Send the ticket embed message")
    @app_commands.describe(channel="Channel to send the embed", content="Embed content", button_label="Button label")
    async def ticket_message(self, interaction: discord.Interaction, channel: discord.TextChannel, content: str, button_label: str):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Only the server owner can run this command.", ephemeral=True)

        embed = discord.Embed(
            title="📩 Need Help?",
            description=content,
            color=discord.Color.green()
        )

        button = discord.ui.Button(label=button_label, style=discord.ButtonStyle.primary, custom_id="open_ticket")
        view = OpenTicketView(self.bot, self.config)

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket message sent to {channel.mention}", ephemeral=True)

class OpenTicketView(discord.ui.View):
    def __init__(self, bot, config):
        super().__init__(timeout=None)
        self.bot = bot
        self.config = config

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        category = None
        for cat in guild.categories:
            if "tickets" in cat.name.lower():
                category = cat
                break

        if not category:
            return await interaction.response.send_message(
                "❌ Ticket category not found. Please run `/ticket-setup` again.", ephemeral=True
            )

        for channel in category.text_channels:
            if channel.name.startswith(f"ticket-{member.name.lower()}"):
                return await interaction.response.send_message(
                    "⚠️ You already have an open ticket.", ephemeral=True
                )

        count = sum(1 for c in category.text_channels if c.name.startswith("ticket-")) + 1
        channel_name = f"ticket-{member.name.lower()}_{count}"
        channel = await guild.create_text_channel(channel_name, category=category)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        for role_id in self.config["admin_roles"]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        await channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            title="🎫 Ticket Opened",
            description=f"Welcome {member.mention}! Our team will assist you shortly.",
            color=discord.Color.orange()
        )
        view = CloseTicketView(bot=self.bot, member=member, config=self.config)
        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self, bot, member, config):
        super().__init__(timeout=None)
        self.bot = bot
        self.member = member
        self.config = config

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild

        overwrites = channel.overwrites
        if self.member in overwrites:
            overwrites[self.member].view_channel = False
            overwrites[self.member].send_messages = False
            await channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description="This ticket has been closed. Only admins can see it now.",
            color=discord.Color.red()
        )

        reopen_view = ReopenDeleteView(bot=self.bot, member=self.member, config=self.config)
        await channel.send(embed=embed, view=reopen_view)
        await interaction.response.send_message("✅ Ticket closed.", ephemeral=True)

class ReopenDeleteView(discord.ui.View):
    def __init__(self, bot, member, config):
        super().__init__(timeout=None)
        self.bot = bot
        self.member = member
        self.config = config

    @discord.ui.button(label="🔓 Open", style=discord.ButtonStyle.success, custom_id="reopen_ticket")
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_admin(interaction.user, interaction.guild):
            return await interaction.response.send_message("Only ticket admins can reopen the ticket.", ephemeral=True)

        channel = interaction.channel
        overwrites = channel.overwrites

        if self.member in overwrites:
            overwrites[self.member].view_channel = True
            overwrites[self.member].send_messages = True
        else:
            overwrites[self.member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        await channel.edit(overwrites=overwrites)
        await channel.send(f"{self.member.mention}, your ticket has been reopened!")
        await interaction.response.send_message("✅ Ticket reopened.", ephemeral=True)

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger, custom_id="delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_admin(interaction.user, interaction.guild):
            return await interaction.response.send_message("Only ticket admins can delete the ticket.", ephemeral=True)

        channel = interaction.channel
        guild = interaction.guild

        transcript_path = await generate_transcript(channel)

        embed = discord.Embed(
            title="🗑️ Ticket Deleted",
            description=f"Ticket by {self.member.mention} deleted by {interaction.user.mention}",
            color=discord.Color.red()
        )

        log_channel = discord.utils.get(guild.text_channels, name="🧾│ticket-log")
        if log_channel:
            await log_channel.send(embed=embed)
            await log_channel.send(file=discord.File(transcript_path))

        try:
            await self.member.send(embed=embed)
            await self.member.send(file=discord.File(transcript_path))
        except:
            pass 

        await interaction.response.send_message("Deleting this ticket...", ephemeral=True)
        await channel.delete()

        try:
            os.remove(transcript_path)
        except:
            pass

    def _is_admin(self, user, guild):
        for role_id in self.config["admin_roles"]:
            role = guild.get_role(role_id)
            if role in user.roles:
                return True
        return user.id == guild.owner_id

async def setup(bot):
    await bot.add_cog(Ticket(bot))