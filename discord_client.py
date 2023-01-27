import asyncio
from typing import List

import discord

from slash_command import SlashCommand


class DiscordClient:

    all_reviews_channel_name = "reviews"
    chat_channel_name = "chat"
    music_channel_name = "music"
    seconds_to_type_one_word = 0.15

    default_permissions = discord.Permissions(
        read_messages=True,
        send_messages=True,
        create_instant_invite=True,
        read_message_history=True,
        use_application_commands=True,
    )

    admin_permissions = discord.Permissions.all

    def __init__(
        self,
        guild_id: int,
        secret_token: str,
    ):
        self.client = discord.Client(intents=discord.Intents.all())
        self.guild_id = guild_id
        self.command_tree = discord.app_commands.CommandTree(self.client)
        self.secret_token = secret_token
        self.__all_reviews_channel_id = None
        self.__chat_channel_id = None
        self.__music_channel_id = None

    async def __guild(self):
        return await self.client.fetch_guild(self.guild_id)

    def get_guild_id(self):
        return self.guild_id

    async def member(self, member_id: str):
        guild = await self.__guild()
        return await guild.fetch_member(member_id)

    async def members(self):
        guild = await self.__guild()
        members = [member async for member in guild.fetch_members(limit=None)]
        return members

    async def channel(self, channel_id: str) -> discord.TextChannel:
        return await self.client.fetch_channel(channel_id)

    async def channels(self):
        guild = await self.__guild()
        return await guild.fetch_channels()

    async def messages(self, channel_id) -> List[discord.Message]:
        channel = await self.channel(channel_id)
        return [
            message
            async for message in channel.history()
            if message.type == discord.MessageType.default
        ]

    async def bot_member(self) -> discord.Member:
        return await self.member(member_id=str(self.client.user.id))

    async def guild_owner(self):
        guild = await self.__guild()
        return await self.member(member_id=guild.owner_id)

    async def slash_command(self, slash_command: SlashCommand) -> discord.app_commands.AppCommand:
        all_commands = await self.command_tree.fetch_commands(
            guild=discord.Object(id=self.guild_id)
        )
        for command in all_commands:
            if command.name == slash_command.name():
                return command

    async def create_private_channel(self, member_id: str, channel_name: str):
        guild = await self.__guild()
        member = await guild.fetch_member(member_id)
        permission_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True),
        }
        return await guild.create_text_channel(channel_name, overwrites=permission_overwrites)

    @staticmethod
    def __get_role(role_name: str, roles: List[discord.Role]):
        for role in roles:
            if role.name == role_name:
                return role

    async def set_role(self, member_id: str, role_name: str):
        guild = await self.__guild()
        member = await guild.fetch_member(member_id)

        old_roles = [role for role in member.roles if role != guild.default_role]
        new_role = self.__get_role(role_name, roles=guild.roles)

        if new_role.id not in [role.id for role in old_roles]:
            await member.add_roles(new_role)

            if len(old_roles) > 0:
                await member.remove_roles(*old_roles)

        _ = await member.edit(nick=f"""[{role_name}] {member.name}""")

    async def __get_all_reviews_channel_id(self) -> str:
        if self.__all_reviews_channel_id is not None:
            return self.__all_reviews_channel_id

        channels = await self.channels()
        for channel in channels:
            if channel.name == self.all_reviews_channel_name:
                self.__all_reviews_channel_id = str(channel.id)

        return self.__all_reviews_channel_id

    async def all_reviews_channel(self) -> discord.TextChannel:
        all_reviews_channel_id = await self.__get_all_reviews_channel_id()
        return await self.channel(channel_id=all_reviews_channel_id)

    async def __get_chat_channel_id(self) -> str:
        if self.__chat_channel_id is not None:
            return self.__chat_channel_id

        channels = await self.channels()
        for channel in channels:
            if channel.name == self.chat_channel_name:
                self.__chat_channel_id = str(channel.id)

        return self.__chat_channel_id

    async def chat_channel(self) -> discord.TextChannel:
        chat_channel_id = await self.__get_chat_channel_id()
        return await self.channel(channel_id=chat_channel_id)

    async def __get_music_channel_id(self) -> str:
        if self.__music_channel_id is not None:
            return self.__music_channel_id

        channels = await self.channels()
        for channel in channels:
            if channel.name == self.music_channel_name:
                self.__music_channel_id = str(channel.id)

        return self.__music_channel_id

    async def music_channel(self) -> discord.TextChannel:
        music_channel_id = await self.__get_music_channel_id()
        return await self.channel(channel_id=music_channel_id)

    @staticmethod
    async def with_typing_time_determined_by_number_of_words(
        message: str, channel: discord.TextChannel, slowness_factor: float = 1.0
    ):
        number_of_words = len(message.split(" "))
        seconds_to_type_one_word = DiscordClient.seconds_to_type_one_word * slowness_factor

        # we don't want to wait that long (e.g., question descriptions)
        if number_of_words > 50:
            seconds_to_type_one_word = 0

        if seconds_to_type_one_word > 0:
            async with channel.typing():
                await asyncio.sleep(number_of_words * seconds_to_type_one_word)

        _ = await channel.send(message)
