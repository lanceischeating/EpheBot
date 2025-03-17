import discord
from discord.ext import commands
from discord import app_commands, Role, DiscordException


class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

        try:
            guild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f'{message.author} said: {message.content}')

        if message.content.startswith('!hello'):
            await message.channel.send(f'Hello! {message.author.mention}')

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix='!', intents=intents)

GUILD_ID = discord.Object(id=None) # ENTER GUILD ID HERE


def get_permissions(interaction: discord.Interaction) -> dict[str, Role | bool | list[Role] | bool]:
    required_role = discord.utils.get(interaction.guild.roles, name="Moderator")
    is_owner: bool = interaction.user.id == interaction.guild.owner_id
    user_roles = interaction.user.roles
    has_admin_roles = any(role.permissions.administrator for role in user_roles)

    return {
        "required_role": required_role,
        "is_owner": is_owner,
        "user_roles": user_roles,
        "has_admin_roles": has_admin_roles,
    }

#addrole
@client.tree.command(name="addrole", description="Adds a role to the user", guild=GUILD_ID)
@app_commands.describe(
    user="Who to add the role to",
    role="The role to add",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE"
)
async def add_role(interaction: discord.Interaction, user: discord.Member, role: discord.Role, ephemeral: bool = False) -> None:
    #Check if the invoker has the correct role
    permissions = get_permissions(interaction)
    required_role = permissions["required_role"]
    is_owner: bool = permissions["is_owner"]
    user_roles = permissions["user_roles"]
    has_admin_roles = permissions["has_admin_roles"]


    if is_owner or has_admin_roles or (required_role in user_roles):
        try:
            await user.add_roles(role)
            await interaction.response.send_message(f"Added {role.mention} to {user.mention}", ephemeral=ephemeral)
        except discord.Forbidden:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"An error occurred while adding the role. Error code{e}", ephemeral=True)
    else:
        await interaction.response.send_message(f"You do not have the required role | {required_role} to use this command.", ephemeral=True)
#remove_role
@client.tree.command(
    name="removerole",
    description="Removes a role from the user",
    guild=GUILD_ID)
@app_commands.describe(
    user="Who to remove the role from",
    role="The role to remove",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE"
)
async def remove_role(interaction: discord.Interaction, user: discord.Member, role: discord.Role, ephemeral: bool = False) -> None:
    permissions = get_permissions(interaction)
    required_role = permissions["required_role"]
    is_owner: bool = permissions["is_owner"]
    user_roles = permissions["user_roles"]
    has_admin_roles = permissions["has_admin_roles"]

    if role not in user.roles:
        await interaction.response.send_message(f"{user.mention} does not have the role {role.mention}", ephemeral=True)
        return

    if is_owner or has_admin_roles or (required_role in user_roles):
        try:
            await user.remove_roles(role)
            await interaction.response.send_message(f"Removed {role.mention} from {user.mention}", ephemeral=ephemeral)
            return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while removing the role. Error code: {e}", ephemeral=False)
    else:
        await interaction.response.send_message(f"You do not have the required role | {required_role} to use this command.", ephemeral=True)
#purge_channel
@client.tree.command(
    name="purge",
    description="Purges a channel",
    guild=GUILD_ID
)
@app_commands.describe(
    channel="The channel to purge",
    limit="The number of messages to purge. LIMIT = 1000",
)
async def purge_channel(interaction: discord.Interaction, channel: discord.TextChannel, limit: int, reason: str) -> None:
    permissions = get_permissions(interaction)

    max_messages = 250


    if permissions["is_owner"] or permissions["has_admin_roles"] or (permissions["required_role"] in permissions["user_roles"]):
        try:
            if limit > max_messages:
                await interaction.response.send_message(f"The limit cannot be greater than {max_messages}",
                                                        ephemeral=True)
                return
            elif limit < 1:
                await interaction.response.send_message(f"The limit must be greater than 0", ephemeral=True)
                return
            await interaction.response.defer()
            await channel.purge(limit=limit, reason=reason)
            await interaction.followup.send(f"Deleted {limit} messages from {channel.mention}", ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while purging the channel. Error code: {e}", ephemeral=False)
    else:
        await interaction.response.send_message(f"You do not have the required role | {required_role} to use this command.", ephemeral=True)

#untimeout
@client.tree.command(
    name="untimeout",
    description="Removes a timeout from a user",
    guild=GUILD_ID
)
@app_commands.describe(
    target="The user to remove the timeout from",
    reason="The reason for removing the timeout",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE"
)
async def untimeout(interaction: discord.Interaction, target: discord.Member, reason: str = None, ephemeral: bool=False) -> None:
    if reason is None:
        reason = "No reason provided"

    permissions = get_permissions(interaction)
    required_role = permissions["required_role"]
    is_owner: bool = permissions["is_owner"]
    user_roles = permissions["user_roles"]
    has_admin_roles = permissions["has_admin_roles"]

    if is_owner or has_admin_roles or (required_role in user_roles):
        try:
            await target.edit(timed_out_until=None, reason=reason)
            await interaction.response.send_message(f"Removed timeout from {target.mention}", ephemeral=ephemeral)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)
    else:
        await interaction.response.send_message(f"You do not have the required role | {required_role} to use this command.", ephemeral=True)

#unban
@client.tree.command(
    name="unban",
    description="Unbans a user",
    guild=GUILD_ID
)
@app_commands.describe(
    target="The user to unban",
    reason="The reason for unbanning the user",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE"
)
async def unban(interaction: discord.Interaction, target: discord.User, reason: str = None, ephemeral: bool=False) -> None:
    if reason is None:
        reason = "No reason provided"

    required_role = discord.utils.get(interaction.guild.roles, name="Moderator")
    is_owner: bool = interaction.user.id == interaction.guild.owner_id
    user_roles = interaction.user.roles
    has_admin_roles = any(role.permissions.administrator for role in user_roles)

    if is_owner or has_admin_roles or (required_role in user_roles):
        try:
            await interaction.guild.fetch_ban(target)
            await interaction.guild.unban(target, reason=reason)
            await interaction.response.send_message(f"Unbanned {target.mention}", ephemeral=ephemeral)
        except discord.NotFound as e:
            await interaction.response.send_message(f"{target.mention} is not banned", ephemeral=False)
            return
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)
            return
    else:
        await interaction.response.send_message(f"You do not have the required role | {required_role} to use this command.", ephemeral=True)
        return

client.run('ENTER TOKEN HERE') 