import discord
from discord import app_commands
from discord.ext import commands
import datetime
from time import strftime, gmtime
from discord.ext.commands import bot
from main import GUILD_ID, authorized_roles
from authorized_role_management import load_auth_roles

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashModeration(bot))

class SlashModeration(commands.Cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.GUILD_ID = GUILD_ID

    @staticmethod
    def is_authorized(interaction: discord.Interaction) -> bool:
        guild_authorized_roles = authorized_roles.get(interaction.guild.id, [])
        is_owner: bool = interaction.user.id == interaction.guild.owner_id
        user_roles = [role.id for role in interaction.user.roles]

        has_required_role = any(role_id in guild_authorized_roles for role_id in user_roles)

        return is_owner or SlashModeration.admin_authorized(interaction) or has_required_role

    @staticmethod
    def admin_authorized(interaction: discord.Interaction) -> bool:
        return interaction.user.id == interaction.guild.owner_id or any(role.permissions.administrator for role in interaction.user.roles)



    #addrole
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="addrole",
        description="Adds a role to the user",)
    @app_commands.describe(
        target="Who to add the role to",
        role="The role to add",
        ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
    async def add_role(self, interaction: discord.Interaction, target: discord.Member, role: discord.Role,
                    ephemeral: bool = False) -> None:
        if SlashModeration.is_authorized(interaction):
            if role.position >=interaction.guild.me.top_role.position:
                await interaction.response.send_message(f"Not possible. The role {role.mention} is above my highest role.", ephemeral=True)
                return
            try:
                await target.add_roles(role)
                await interaction.response.send_message(f"Added {role.mention} to {target.mention}", ephemeral=ephemeral)
                print(f"[{strftime("%m-%d-%Y %H:%M:%S", gmtime())}] Added {role.name} to {target.name} ({target.id}) in {GUILD_ID}")
            except discord.Forbidden:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            except discord.HTTPException as e:
                await interaction.response.send_message(f"An error occurred while adding the role. Error code{e}",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(
                "You do not have the required role  to use this command.", ephemeral=True)


#remove_role
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="removerole",
        description="Removes a role from the user",)
    @app_commands.describe(
        user="Who to remove the role from",
        role="The role to remove",
        ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role,
                      ephemeral: bool = False) -> None:

        if SlashModeration.is_authorized(interaction):
            if role.position >=interaction.guild.me.top_role.position:
                await interaction.response.send_message(f"Not possible. The role {role.mention} is above my highest role.", ephemeral=True)
                return
            try:
                await user.remove_roles(role)
                await interaction.response.send_message(f"Removed {role.mention} from {user.mention}", ephemeral=ephemeral)
                print(f"[{strftime("%m-%d-%Y %H:%M:%S", gmtime())}] - Removed {role.name} from {user.name} ({user.id}) in {GUILD_ID}")
                return
            except Exception as e:
                await interaction.response.send_message(f"An error occurred while removing the role. Error code: {e}",
                                                    ephemeral=False)
        else:
            await interaction.response.send_message(f"You do not have the required role to use this command.", ephemeral=True)
            print(f"[{strftime("%m-%d-%Y %H:%M:%S", gmtime())}] - {interaction.user.name} tried to remove {role.name} from {user.name} ({user.id}) in {GUILD_ID} but was denied access")


#purge_channel
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="purge",
        description="Mass delete messages from a channel. LIMIT = 250",
    )
    @app_commands.describe(
        channel="The channel to purge",
        limit="The number of messages to purge. LIMIT = 250",
    )
    @commands.has_role("Moderator")
    async def purge_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, limit: int,
                        reason: str = None) -> None:
        MAX_MESSAGES = 250

        if reason is None:
            reason = "No reason provided"

        if SlashModeration.is_authorized(interaction):
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
                print(f"Deleted {len(deleted)} messages from {channel.name} ({channel.id}) in {GUILD_ID}")
            except Exception as e:
                await interaction.followup.send(f"An error occurred while purging the channel. Error code: {e}",
                                            ephemeral=False)
        else:
            await interaction.response.send_message(
                f"You do not have the required role to use this command.", ephemeral=True)


#untimeout
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="untimeout",
        description="Removes a timeout from a user",)
    @app_commands.describe(
        target="The user to remove the timeout from",
        reason="The reason for removing the timeout",
        ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
    async def untimeout(self,interaction: discord.Interaction, target: discord.Member, reason: str = None,
                    ephemeral: bool = False) -> None:
        if reason is None:
            reason = "No reason provided"

        if interaction.user.id == target.id:
            await interaction.response.send_message(f"You cannot remove the timeout from yourself!", ephemeral=ephemeral);
            print(
                f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to remove the timeout from themselves in {GUILD_ID}")
            return

        if SlashModeration.is_authorized(interaction):
            try:
                await target.edit(timed_out_until=None, reason=reason)
                await interaction.response.send_message(f"Removed timeout from {target.mention}", ephemeral=ephemeral)
                await target.send(f"Your timeout has been removed early by {interaction.user.mention}. Reason: {reason}")
                print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - Removed timeout from {target.name} ({target.id}) in {GUILD_ID}")
            except Exception as e:
                await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)
                print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to remove the timeout from {target.name} ({target.id}) in {GUILD_ID} but failed.\n Error code: {e}")
        else:
            await interaction.response.send_message(
                f"You do not have the required role to use this command.", ephemeral=True)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to remove the timeout from {target.name} ({target.id}) in {GUILD_ID} but was denied access")


#timeout
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="timeout",
        description="Timeouts a user",)
    @app_commands.describe(
        target="The user to timeout",
        duration="The duration of the timeout",
        duration_unit="The unit of the duration",
        reason="The reason for the timeout",
        ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
    @app_commands.choices(
        duration_unit=[
        app_commands.Choice(name="minutes", value="minutes"),
        app_commands.Choice(name="hours", value="hours"),
        app_commands.Choice(name="days", value="days"),
        app_commands.Choice(name="weeks", value="weeks"),
        ])
    async def timeout(self, interaction: discord.Interaction, target: discord.Member, duration: int, duration_unit: str,
                  reason: str, ephemeral: bool = False) -> None:
        if not SlashModeration.is_authorized(interaction):
            await interaction.response.send_message(f"You are not authorized to use this command.", ephemeral=ephemeral)
            print(
                f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to timeout {target.name} ({target.id}) in {GUILD_ID} but was denied access")
            return
        input_exceeded_max_duration = False
        duration_in_seconds = None
        MAX_DURATION = 28
        match duration_unit:
            case "minutes":
                if duration > 40320:
                    duration_in_seconds = 40320 * 60
                    input_exceeded_max_duration = True
                else:
                    duration_in_seconds = duration * 60
            case "hours":
                if duration > 672:
                    duration_in_seconds = 672 * 60 * 60
                    input_exceeded_max_duration = True
                else:
                    duration_in_seconds = duration * 60 * 60
            case "days":
                if duration > MAX_DURATION:
                    duration_in_seconds = MAX_DURATION * 60 * 60 * 24
                    input_exceeded_max_duration = True
                else:
                    duration_in_seconds = duration * 60 * 60 * 24
            case "weeks":
                if duration > 4:
                    duration_in_seconds = MAX_DURATION * 60 * 60 * 24 * 7
                    input_exceeded_max_duration = True
                else:
                    duration_in_seconds = duration * 60 * 60 * 24 * 7

        if target.id == interaction.user.id:
            await interaction.response.send_message("You cannot timeout yourself", ephemeral=ephemeral)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to timeout themselves in {GUILD_ID}")
            return

        try:
            if target.timed_out_until is not None:
                await interaction.response.send_message(f"{target.mention} is already timed out, consider removing "
                                                    f"the timeout first", ephemeral=ephemeral)
                print(
                    f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to timeout {target.name} ({target.id}) in {GUILD_ID} but was already timed out")
                return

            timedout_until = discord.utils.utcnow() + timedelta(seconds=duration_in_seconds)
            await target.edit(timed_out_until=timedout_until, reason=reason)

            if not input_exceeded_max_duration:
                await interaction.response.send_message(f"Timed out {target.mention} for {duration} {duration_unit}", ephemeral = ephemeral)
                await target.send(f"You have been timed out by {interaction.user.mention} for {duration} {duration_unit}. Reason: {reason}")
                print(f"Timed out {target.name} ({target.id}) in {GUILD_ID} for {duration} {duration_unit} | Caller: {interaction.user.name}")
            else:
                await interaction.response.send_message(f"Timed out {target.mention} for {MAX_DURATION} days. Discord API does not allow timeouts to exceed {MAX_DURATION}. "
                                                        f"Consider using a /ban if you wish to apply a punishment longer than {MAX_DURATION}", ephemeral = ephemeral)
                await target.send(f"You have been timed out by {interaction.user.mention} for {MAX_DURATION} days.")
                print(f"Timed out {target.name} ({target.id}) in {GUILD_ID} for {MAX_DURATION} days. Discord API does not allow timeouts to exceed {MAX_DURATION}."
                      f"\n Caller: {interaction.user.name} (ID:{interaction.user.id})")
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to timeout {target.name} ({target.id}) in {GUILD_ID} but failed."
                  f"\n Error code: {e}")


#internal fetch_timeout:
    async def fetch_timeout(self, interaction: discord.Interaction) -> list[discord.Member]:
        timeout_list = []
        async for server_member in interaction.guild.fetch_members(limit=None):
            if server_member.timed_out_until is not None:
                timeout_list.append(server_member)
        return timeout_list


#unban
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="unban",
        description="Unbans a user",)
    @app_commands.describe(
        target="The user to unban",
        reason="The reason for unbanning the user",
        ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
    async def unban(self, interaction: discord.Interaction, target: discord.User, reason: str = None,
                ephemeral: bool = False) -> None:
        if not SlashModeration.is_authorized(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=ephemeral)
            print(
                f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} (ID: {interaction.user.id}) "
                f"tried to unban {target.name} ({target.id}) in {GUILD_ID} but was denied access")
            return

        if reason is None:
            reason = "No reason provided"

        try:
            await interaction.guild.fetch_ban(target)
            await interaction.guild.unban(target, reason=reason)
            await interaction.response.send_message(f"Unbanned {target.mention}", ephemeral=ephemeral)
            print(f"Unbanned {target.name} ({target.id}) in {GUILD_ID} | Caller: {interaction.user.name}")
        except discord.NotFound as e:
            await interaction.response.send_message(f"{target.id} is not a valid userID", ephemeral=False)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S')}] - {interaction.user.name} tried to unban {target.name} ({target.id}) in {GUILD_ID} but {target.id} was not a valid ID"
                  f"\n {e}")
            return
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong. Error code: {e}", ephemeral=ephemeral)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to unban {target.name} ({target.id}) in {GUILD_ID} but failed."
                  f"\n Error code: {e}")
            return


#ban
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="ban",
        description="IP Bans a user from your server and optionally deletes messages"
    )
    @app_commands.describe(
        target="The user to be banned",
        reason="The reason for banning the user",
        delete_messages_time="Deletes messages upon banning the user",
        ephemeral="Set whether the bot response and command execution is visible to other users"
    )
    @app_commands.choices(delete_messages_time=[
        app_commands.Choice(name="No deletion", value=0),
        app_commands.Choice(name="1 Day", value=1),
        app_commands.Choice(name="3 day", value=3),
        app_commands.Choice(name="7 days", value=7)
    ])
    async def ban(self, interaction: discord.Interaction, target: discord.User, reason: str, delete_messages_time: int, ephemeral: bool = False) -> None:
        if not SlashModeration.is_authorized(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            print(
                f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} (ID: {interaction.user.id}) "
                f"tried to ban {target.name} ({target.id}) in {GUILD_ID} but was denied access")
            return
        if reason is None:
            reason = "No reason provided."

        if interaction.user.id == target.id:
            await interaction.response.send_message("you cannot ban yourself", ephemeral=True)
            return

        try:
            await interaction.guild.fetch_ban(target)
        except discord.NotFound:
            ban_embed = discord.Embed(title="__User Banned__", color=discord.Color.red(), timestamp=datetime.datetime.now(datetime.UTC))
            ban_embed.set_author(name=f"{target.name} | ID: {target.id}")
            ban_embed.add_field(name="Mention", value=target.mention, inline=True)
            ban_embed.add_field(name="Nickname", value=target.display_name, inline=True)

            ban_authority_roles = [role for role in interaction.user.roles if role.permissions.ban_members]
            ban_auth_string = "\n".join(role.mention for role in ban_authority_roles)

            ban_embed.add_field(name="Invoker", value=interaction.user.mention, inline=True)
            ban_embed.add_field(name="Authorized Role(s)", value=ban_auth_string, inline=False)
            ban_embed.add_field(name="Administrator", value=SlashModeration.admin_authorized(interaction))
            ban_embed.add_field(name="Ban Reason", value=reason, inline=False)
            ban_embed.add_field(name="Deleted messages?", value=delete_messages_time)
            await interaction.guild.ban(user=target, reason=reason, delete_message_days=delete_messages_time)
            await interaction.response.send_message(embed=ban_embed)
        else:
            await interaction.response.send_message(f"{target.id} is already banned!")
            return


#kick
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="kick",
        description="Kicks a user")
    @app_commands.describe(
        target="The user to kick",
        reason="The reason for kicking the user",
        ephemeral="Set whether the bot response is visible to other users TRUE or FALSE")
    async def kick(self, interaction: discord.Interaction, target: discord.Member, reason: str, ephemeral: bool = False) -> None:
        if not SlashModeration.is_authorized(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=ephemeral)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to kick {target.name} ({target.id}) in {GUILD_ID} but was denied access")
            return

        if target.id == interaction.user.id:
            await interaction.response.send_message("You cannot kick yourself!", ephemeral=ephemeral)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to kick themselves in {GUILD_ID}")
            return
        if target.id not in interaction.guild.members:
            await interaction.response.send_message(f"{target.mention} is not on the server.", ephemeral=True)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to kick {target.name} ({target.id}) in {GUILD_ID} but they are not on the server")
            return
        try:
            await interaction.guild.fetch_member(target.id)
            await target.kick(reason=reason)
            await interaction.response.send_message(f"Kicked {target.mention}", ephemeral=ephemeral)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - Kicked {target.name} ({target.id}) in {GUILD_ID} | Caller: {interaction.user.name}")
        except discord.NotFound:
            await interaction.response.send_message(f"{target.mention} is not a valid ID", ephemeral=True)
            print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to kick {target.name} ({target.id}) in {GUILD_ID} but {target.id} was not a valid ID")
            return

#warn
    @app_commands.guild(discord.Object(id=GUILD_ID))
    @app_commands.command(
        name="warn",
        description="Sends a private message to this user indicating that they have been warned"
    )
    @app_commands.describe(
        target="The person to warn",
        reason="The reason for issuing the warning"
    )
    async def warn(self, interaction: discord.Interaction, target: discord.Member, reason: str, ephemeral: bool = False) -> None:
        if not SlashModeration.is_authorized(interaction):
             await interaction.response.send_message("You are not authorized to use this command.", ephemeral=ephemeral)
             print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to kick {target.name} ({target.id}) in {GUILD_ID} but was denied access")
             return
        if target.id == interaction.user.id:
             await interaction.response.send_message("You cannot warn yourself")
             print(f"[{strftime('%m-%d-%Y %H:%M:%S', gmtime())}] - {interaction.user.name} tried to warn  themselves in {GUILD_ID}")
             return

        if target.id not in interaction.guild.members:
            await interaction.response.send_message("You cannot warn a user that is not in the server")
            return

        try:
            await target.send(f"You have been warned in {interaction.guild.name} by {interaction.user.mention} for: {reason}")
        except Exception as e:
            await interaction.send_message(f"{target.mention} was warned by {interaction.user.mention}\n Reason:{reason}")
            await interaction.followup(f"Direct message failed to send {e}")
            
