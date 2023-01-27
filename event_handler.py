import asyncio

import discord

from state import State


class EventHandler:
    def __init__(self, state: State):
        self.__state = state

    async def __enforce_time_limits_loop(self):
        while True:
            _ = await self.__state.enforce_time_limits()
            # TODO: pull hard coded constants like this into the state
            _ = await asyncio.sleep(self.__state.enforce_time_limits_every.total_seconds())

    async def on_ready(self):
        guild = discord.Object(id=self.__state.discord_client.guild_id)

        all_reviews_channel = await self.__state.discord_client.all_reviews_channel()
        _ = await all_reviews_channel.send("Running bot")

        await self.__state.discord_client.command_tree.sync(guild=guild)

        asyncio.create_task(self.__enforce_time_limits_loop())

        print("Running bot")

    async def on_member_join(self, member: discord.Member):
        _new_user, _user_channel = await self.__state.create_user(discord_member=member)
