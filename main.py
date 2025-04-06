import asyncio

import discord
from discord.ext import commands
from authorized_role_management import load_auth_roles, save_auth_roles

# Global config variables
authorized_roles = load_auth_roles()
GUILD_ID = 1350725093914972172

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
        return

@bot.event
async def on_guild_join(guild):
    if guild.id not in authorized_roles:
        authorized_roles[guild.id] = []
        save_auth_roles(authorized_roles)
    print(f"Joined {guild.name} (ID: {guild.id}). A blank authorized roles entry was created.")

async def load_extensions():
    await bot.load_extension("cogs.config")
    await bot.load_extension("cogs.slash_moderation")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(token="ENTER TOKEN HERE")
if __name__ == "__main__":
    asyncio.run(main())

### CONTEXT MENU COMMANDS ###
#@app_commands.context_menu(
#    name="Permaban Spammer/Raider",
#    guild=GUILD_ID
#)
#async def permaban_spammer_raider(interaction: discord.Interaction, user: discord.Member) -> None:
#    await interaction.response.send_message(f"Permabanning {user.mention}...", ephemeral=True)
#    return

#@bot.tree.context_menu(name="Mute User")
#async def mute_user(interaction: discord.Interaction, user: discord.Member) -> None:
