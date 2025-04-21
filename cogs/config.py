import discord
from discord import app_commands
from discord.ext import commands
from main import authorized_roles, GUILD_ID
from authorized_role_management import save_auth_roles

async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))

def is_admin_or_owner():
    async def util_check(interaction: discord.Interaction):
        # Check if the user is the bot owner
        app_info = await interaction.client.application_info()
        if interaction.user.id == app_info.owner.id:
            return True

        # Check if the user has administrator permissions in the guild
        if interaction.user.guild_permissions.administrator:
            return True

        return False

    return commands.check(util_check)


class Config(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="addauthrole",
        description="Adds an authorized role to the list of authorized roles",
    )
    @app_commands.describe(role="The role to add to the authorized roles list")
    @is_admin_or_owner()
    async def addauthrole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = interaction.guild.id

        if guild_id not in authorized_roles:
            authorized_roles[guild_id] = []

        if role.id in authorized_roles[guild_id]:
            await interaction.response.send_message(f"Role {role.mention} is already authorized.")
            return

        authorized_roles[guild_id].append(role.id)
        save_auth_roles(authorized_roles)
        await interaction.response.send_message(f"Role {role.mention} added to authorized roles.")
        await interaction.client.tree.sync(guild=interaction.guild)

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="delauthrole",
        description="Deletes an authorized role from the list of authorized roles",
    )
    @app_commands.describe(role="The role to delete from the authorized roles list")
    @is_admin_or_owner()
    async def delauthrole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = interaction.guild.id

        if guild_id not in authorized_roles:
            await interaction.response.send_message(f"No authorized roles found for this guild.")
            return
        if role.id not in authorized_roles[guild_id]:
            await interaction.response.send_message(f"Role {role.mention} is not authorized.")

        authorized_roles[guild_id].remove(role.id)
        save_auth_roles(authorized_roles)

        await interaction.response.send_message(f"Role {role.mention} removed from authorized roles.")
        await interaction.client.tree.sync(guild=interaction.guild)

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="listauthroles",
        description="Lists all authorized roles for the current guild",
    )
    @is_admin_or_owner()
    async def listauthroles(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        if guild_id not in authorized_roles or authorized_roles[guild_id] == []:
            await interaction.response.send_message(f"No authorized roles found for this guild.")
            return
        role_names = []

        for role_id in authorized_roles[guild_id]:
            role = discord.utils.get(interaction.guild.roles, id=role_id)
            role_names.append(role.name if role else f"Unknown role (ID: {role_id})")

        await interaction.response.send_message(f"Authorized roles for this guild: {'\n '.join(role_names)}")

    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="caller_check",
        description="Checks if the user is the bot owner or has the required role to use the command")
    async def caller_check(self, interaction: discord.Interaction, ephemeral: bool = True) -> None:
        guild_authorized_roles = authorized_roles.get(interaction.guild.id, [])
        user_roles = [role.id for role in interaction.user.roles]
        has_required_role = any(role_id in guild_authorized_roles for role_id in user_roles)

        is_owner = interaction.user.id == interaction.guild.owner_id
        is_admin = interaction.user.guild_permissions.administrator


        embed = discord.Embed(title="User Info", color=0x00ff00)
        embed.add_field(name="User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Join Date", value=str(interaction.user.joined_at), inline=False)
        embed.add_field(name="Created At", value=str(interaction.user.created_at), inline=False)
        embed.add_field(name="Server Owner?", value=is_owner, inline=False)
        embed.add_field(name="Admin?", value=is_admin, inline=False)
        embed.add_field(name="Has Moderation Role(s)?", value=has_required_role, inline=False)
        embed.add_field(name="Roles", value="\n".join([role.mention for role in interaction.user.roles]), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)





