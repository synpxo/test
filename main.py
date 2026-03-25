import os
import discord
from discord import app_commands, Interaction
from discord.ui import View, Button
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("ERLC_API_KEY")

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

def get_server_info():
    headers = {"server-key": API_KEY, "Accept": "*/*"}
    general_resp = requests.get("https://api.policeroleplay.community/v1/server", headers=headers).json()
    queue_resp = requests.get("https://api.policeroleplay.community/v1/server/queue", headers=headers).json()
    return {
        "name": general_resp.get("Name", "Unknown"),
        "join_code": general_resp.get("JoinKey", "None"),
        "current_players": general_resp.get("CurrentPlayers", 0),
        "max_players": general_resp.get("MaxPlayers", 0),
        "queue": queue_resp[0] if queue_resp else 0,
        "team_balance": "On" if general_resp.get("TeamBalance", False) else "Off"
    }

class ServerView(View):
    def __init__(self, join_code):
        super().__init__(timeout=None)
        self.add_item(Button(label="Join Server", url=f"https://policeroleplay.community/join/{join_code}"))
        self.add_item(Button(label="Refresh", style=discord.ButtonStyle.gray, custom_id="refresh_button"))

def create_server_embed(bot_user: discord.User, server_info: dict, guild_icon_url=None):
    embed = discord.Embed(title=server_info["name"], color=0x95a5a6)
    embed.set_author(name=bot_user.name, icon_url=bot_user.display_avatar.url)
    if guild_icon_url:
        embed.set_thumbnail(url=guild_icon_url)
    embed.add_field(
        name="General",
        value=f"> **Server Name:** `{server_info['name']}`\n> **Join Code:** `{server_info['join_code']}`",
        inline=False
    )
    embed.add_field(
        name="Players",
        value=f"> **Current Players:** `{server_info['current_players']}/{server_info['max_players']}`\n"
              f"> **Queue:** `{server_info['queue']} players`\n"
              f"> **Team Balance:** `{server_info['team_balance']}`",
        inline=False
    )
    return embed

erlc_group = app_commands.Group(name="erlc", description="ERLC server commands")

@erlc_group.command(name="info", description="Get ERLC server info")
async def erlc_info(interaction: Interaction):
    await interaction.response.defer()
    server_info = get_server_info()
    guild_icon_url = interaction.guild.icon.url if interaction.guild.icon else None
    embed = create_server_embed(bot.user, server_info, guild_icon_url=guild_icon_url)
    await interaction.followup.send(embed=embed, view=ServerView(server_info["join_code"]))

tree.add_command(erlc_group)

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id") == "refresh_button":
        server_info = get_server_info()
        guild_icon_url = interaction.guild.icon.url if interaction.guild.icon else None
        embed = create_server_embed(bot.user, server_info, guild_icon_url=guild_icon_url)
        await interaction.response.edit_message(embed=embed, view=ServerView(server_info["join_code"]))

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}!")

bot.run(TOKEN)
