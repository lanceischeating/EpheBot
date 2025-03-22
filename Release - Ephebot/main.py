import asyncio

import discord
from discord.ext import commands

# Global config variables
REQUIRED_ROLE = None
GUILD_ID = 'ENTER GUILD ID'

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

    global REQUIRED_ROLE
    if guild:
        REQUIRED_ROLE = discord.utils.get(bot.get_guild(GUILD_ID).roles, name="Moderator")
        if REQUIRED_ROLE:
            print(f"Found required role: {REQUIRED_ROLE}")
        else:
            print("Required role not found")

async def load_extensions():
    await bot.load_extension("cogs.slash_moderation")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(token="ENTER TOKEN")
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
