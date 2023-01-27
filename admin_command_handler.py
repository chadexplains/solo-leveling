import discord
import pyairtable.formulas

import user
from rank import Rank
from state import State
from user import User


class AdminCommandHandler:
    def __init__(self, *, state: State):
        self.__state = state

    async def wipe_state(
        self,
        *,
        interaction: discord.Interaction,
        users: bool,
        missions: bool,
        channels: bool,
        threads: bool,
        all_reviews_channel_messages: bool,
    ):
        all_reviews_channel = await self.__state.discord_client.all_reviews_channel()
        chat_channel = await self.__state.discord_client.chat_channel()
        music_channel = await self.__state.discord_client.music_channel()

        if interaction.channel.id != all_reviews_channel.id:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=all_reviews_channel,
                suggested_command=None,
            )
            return None

        if users:
            _ = await all_reviews_channel.send("deleting all users")
            users_deleted = await self.__state.delete_all_users()
            users_deleted = len(users_deleted)
            _ = await all_reviews_channel.send(f"""deleted {users_deleted} users""")

        if missions:
            _ = await all_reviews_channel.send("deleting all missions")
            missions_deleted = await self.__state.delete_all_missions()
            missions_deleted = len(missions_deleted)
            _ = await all_reviews_channel.send(f"""deleted {missions_deleted} missions""")

        if channels:
            _ = await all_reviews_channel.send("deleting all channels")
            channels_deleted = await self.__state.delete_all_channels(
                except_for=frozenset([all_reviews_channel, chat_channel, music_channel])
            )
            channels_deleted = len(channels_deleted)
            _ = await all_reviews_channel.send(f"""deleted {channels_deleted} channels""")

        _ = await all_reviews_channel.send("syncing bot user to db")
        bot_discord_member = await self.__state.discord_client.bot_member()
        _, bot_user = await self.__state.create_user(discord_member=bot_discord_member)
        _ = await all_reviews_channel.send("synced bot user to db")

        users_in_discord = await self.__state.discord_client.members()
        for user_to_sync in users_in_discord:
            if user_to_sync.id != bot_discord_member.id:
                _ = await all_reviews_channel.send(f"""syncing user {user_to_sync.name} to db""")
                new_user, _user_channel = await self.__state.create_user(
                    discord_member=user_to_sync
                )

        if threads:
            _ = await all_reviews_channel.send("deleting all threads")
            threads_to_delete = all_reviews_channel.threads
            for thread_to_delete in threads_to_delete:
                _ = await thread_to_delete.delete()
            threads_deleted = len(threads_to_delete)
            _ = await all_reviews_channel.send(f"""deleted {threads_deleted} threads""")

        _ = await interaction.followup.send("""Finished""")

        if all_reviews_channel_messages:
            _ = await all_reviews_channel.purge(limit=None)

    async def set_rank(self, interaction: discord.Interaction, user_discord_name: str, rank: str):
        user_to_update = await User.row(
            formula=pyairtable.formulas.match({user.Fields.discord_name_field: user_discord_name}),
            airtable_client=self.__state.airtable_client,
        )

        await self.__state.set_rank(for_user=user_to_update, rank=Rank.of_string(rank))

        return await interaction.followup.send(f"""Updated {user_discord_name}'s rank to {rank}""")
