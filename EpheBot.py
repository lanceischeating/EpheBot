from datetime import timedelta

import discord
from discord.ext import commands
from discord import app_commands, Role, DiscordException

required_role = None

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        try:
            guild = discord.Object(id=ENTER GUILD ID HERE)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
            return

        global required_role
        if guild:
            required_role = discord.utils.get(self.get_guild(ENTER GUILD ID HERE).roles, name="Moderator")
            if required_role:
                print(f"Found required role: {required_role}")
            else:
                print("Required role not found")

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f'{message.author} said: {message.content}')

        if message.content.startswith('!hello'):
            await message.channel.send(f'Hello! {message.author.mention}')


# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = Client(command_prefix='!', intents=intents)

GUILD_ID = discord.Object(id=ENTER GUILD ID HERE)


def is_authorized(interaction: discord.Interaction) -> bool:
    is_owner: bool = interaction.user.id == interaction.guild.owner_id
    user_roles = interaction.user.roles
    has_admin_roles = any(role.permissions.administrator for role in user_roles)

    if is_owner or has_admin_roles or (required_role in user_roles) or interaction.user.top_role > required_role:
        return True

    else:
        return False


#addrole
@client.tree.command(
    name="addrole",
    description="Adds a role to the user",
    guild=GUILD_ID)
@app_commands.describe(
    target="Who to add the role to",
    role="The role to add",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
async def add_role(interaction: discord.Interaction, target: discord.Member, role: discord.Role,
                   ephemeral: bool = False) -> None:
    #Check if the invoker has the correct role

    if is_authorized(interaction) and interaction.user.id != target.id:
        try:
            await target.add_roles(role)
            await interaction.response.send_message(f"Added {role.mention} to {target.mention}", ephemeral=ephemeral)
        except discord.Forbidden:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.response.send_message(f"An error occurred while adding the role. Error code{e}",
                                                    ephemeral=True)
    else:
        await interaction.response.send_message(
            f"You do not have the required role | {required_role} to use this command.", ephemeral=True)


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
async def remove_role(interaction: discord.Interaction, user: discord.Member, role: discord.Role,
                      ephemeral: bool = False) -> None:
    if role not in user.roles:
        await interaction.response.send_message(f"{user.mention} does not have the role {role.mention}", ephemeral=True)
        return

    if is_authorized(interaction):
        try:
            await user.remove_roles(role)
            await interaction.response.send_message(f"Removed {role.mention} from {user.mention}", ephemeral=ephemeral)
            return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while removing the role. Error code: {e}",
                                                    ephemeral=False)
    else:
        await interaction.response.send_message(
            f"You do not have the required role | {required_role} to use this command.", ephemeral=True)


#purge_channel
@client.tree.command(
    name="purge",
    description="Mass delete messages from a channel. LIMIT = 250",
    guild=GUILD_ID
)
@app_commands.describe(
    channel="The channel to purge",
    limit="The number of messages to purge. LIMIT = 250",
)
async def purge_channel(interaction: discord.Interaction, channel: discord.TextChannel, limit: int,
                        reason: str = None) -> None:
    MAX_MESSAGES = 250

    if reason is None:
        reason = "No reason provided"

    if is_authorized(interaction):
        try:
            if limit > MAX_MESSAGES:
                await interaction.response.send_message(f"The limit cannot be greater than {MAX_MESSAGES}",
                                                        ephemeral=True)
                return
            elif limit < 1:
                await interaction.response.send_message(f"The limit must be greater than 0", ephemeral=True)
                return

            await interaction.response.defer()
            original_response = await interaction.original_response()

            def not_interaction_message(message: discord.Message) -> bool:
                return message.id != original_response.id

            deleted = await channel.purge(limit=limit, check=not_interaction_message, reason=reason)

            await interaction.followup.send(
                f"Deleted {len(deleted)} messages from {channel.mention} | Caller: {interaction.user.mention} | Reason: {reason}",
                ephemeral=False)
        except Exception as e:
            await interaction.followup.send(f"An error occurred while purging the channel. Error code: {e}",
                                            ephemeral=False)
    else:
        await interaction.response.send_message(
            f"You do not have the required role | {required_role} to use this command.", ephemeral=True)


#untimeout
@client.tree.command(
    name="untimeout",
    description="Removes a timeout from a user",
    guild=GUILD_ID)
@app_commands.describe(
    target="The user to remove the timeout from",
    reason="The reason for removing the timeout",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
async def untimeout(interaction: discord.Interaction, target: discord.Member, reason: str = None,
                    ephemeral: bool = False) -> None:
    if reason is None:
        reason = "No reason provided"

    if is_authorized(interaction) and target.id != interaction.user.id:
        try:

            await target.edit(timed_out_until=None, reason=reason)
            await interaction.response.send_message(f"Removed timeout from {target.mention}", ephemeral=ephemeral)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)
    else:
        await interaction.response.send_message(
            f"You do not have the required role | {required_role} to use this command.", ephemeral=True)

#timeout
@client.tree.command(
    name="timeout",
    description="Timeouts a user",
    guild=GUILD_ID)
@app_commands.describe(
    target="The user to timeout",
    duration="The duration of the timeout",
    duration_unit="The unit of the duration",
    reason="The reason for the timeout",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE"
)
@app_commands.choices(
    duration_unit=[
        app_commands.Choice(name="minutes", value="minutes"),
        app_commands.Choice(name="hours", value="hours"),
        app_commands.Choice(name="days", value="days"),
        app_commands.Choice(name="weeks", value="weeks"),
    ]
)
async def timeout(interaction: discord.Interaction, target: discord.Member, duration: int, duration_unit: str,
                  reason: str, ephemeral: bool = False) -> None:

    duration_in_seconds = None
    MAX_DURATION = 28
    match duration_unit:
        case "minutes":
            if duration > 40320:
                await interaction.response.send_message(
                    f"You cannot timeout for more than 40320 minutes, setting to maximum of 28 days", ephemeral=ephemeral)
                duration_in_seconds = 40320 * 60
            else:
                duration_in_seconds = duration * 60
        case "hours":
            if duration > 672:
                await interaction.response.send_message(
                    f"You cannot timeout for more than 672 hours, setting to maximum of 28 days", ephemeral=ephemeral)
                duration_in_seconds = 672 * 60 * 60
            else:
                duration_in_seconds = duration * 60 * 60
        case "days":
            if duration > MAX_DURATION:
                await interaction.response.send_message(
                    f"You cannot timeout for more than {MAX_DURATION} days, setting to maximum of 28 days",
                    ephemeral=False)
                duration_in_seconds = MAX_DURATION * 60 * 60 * 24
            else:
                duration_in_seconds = duration * 60 * 60 * 24
        case "weeks":
            if duration > 4:
                await interaction.response.send_message(
                    f"You cannot timeout for more than 4 weeks, setting to maximum of 28 days", ephemeral=ephemeral)
                duration_in_seconds = MAX_DURATION * 60 * 60 * 24 * 7
            else:
                duration_in_seconds = duration * 60 * 60 * 24 * 7

    if not is_authorized(interaction):
        await interaction.response.send_message(f"You are not authorized to use this command.", ephemeral=ephemeral)
        return

    if target.id == interaction.user.id:
        await interaction.response.send_message(f"You cannot timeout yourself", ephemeral=ephemeral)
        return

    if is_authorized(interaction):
        try:
            if target.timed_out_until is not None:
                await interaction.response.send_message(f"{target.mention} is already timed out, consider removing "
                                                        f"the timeout first", ephemeral=ephemeral)
                return

            timedout_until = discord.utils.utcnow() + timedelta(seconds=duration_in_seconds)
            await target.edit(timed_out_until=timedout_until, reason=reason)
            await interaction.response.send_message(
                f"Timed out {target.mention} for {timedelta(seconds=duration_in_seconds)}", ephemeral=ephemeral)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)

#internal fetch_timeout:
async def fetch_timeout(interaction: discord.Interaction) -> list[discord.Member]:
    timeout_list = []
    async for server_member in interaction.guild.fetch_members(limit=None):
        if server_member.timed_out_until is not None:
            timeout_list.append(server_member)
    return timeout_list
#unban
@client.tree.command(
    name="unban",
    description="Unbans a user",
    guild=GUILD_ID)
@app_commands.describe(
    target="The user to unban",
    reason="The reason for unbanning the user",
    ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
async def unban(interaction: discord.Interaction, target: discord.User, reason: str = None,
                ephemeral: bool = False) -> None:
    if reason is None:
        reason = "No reason provided"

    if is_authorized(interaction=interaction):
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
        await interaction.response.send_message(
            f"You do not have the required role | {required_role} to use this command.", ephemeral=True)
        return


client.run('ENTER TOKEN HERE')
