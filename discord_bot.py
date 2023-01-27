import datetime
import os

import discord
import dotenv

from admin_command_handler import AdminCommandHandler
from airtable_client import AirtableClient
from discord_client import DiscordClient
from event_handler import EventHandler
from google_client import GoogleClient
from player_command_handler import PlayerCommandHandler
from reviewer_command_handler import ReviewerCommandHandler
from slash_command import SlashCommand
from state import State
from time_limit_config import TimeLimitConfig

dotenv.load_dotenv()
airtable_api_key = os.environ["airtable_api_key"]
airtable_database_id = os.environ["airtable_database_id"]
discord_guild_id = int(os.environ["discord_guild_id"])
discord_secret_token = os.environ["discord_secret_token"]

airtable_client = AirtableClient(api_key=airtable_api_key, base_id=airtable_database_id)
discord_client = DiscordClient(
    guild_id=discord_guild_id,
    secret_token=discord_secret_token,
)
google_client = GoogleClient()

time_limit_config = TimeLimitConfig(
    design=datetime.timedelta(minutes=60),
    code=datetime.timedelta(minutes=20),
    unclaimed_review=datetime.timedelta(minutes=10),
    claimed_review=datetime.timedelta(minutes=20),
)

state = State(
    airtable_client=airtable_client,
    discord_client=discord_client,
    google_client=google_client,
    enforce_time_limits_every=datetime.timedelta(seconds=10),
    time_limit_config=time_limit_config,
)
admin_command_handler = AdminCommandHandler(state=state)
player_command_handler = PlayerCommandHandler(state=state)
reviewer_command_handler = ReviewerCommandHandler(state=state)
event_handler = EventHandler(state)


def register_slash_command(slash_command_to_register: SlashCommand):
    return discord_client.command_tree.command(
        name=slash_command_to_register.name(),
        description=slash_command_to_register.description(),
        guild=discord.Object(id=discord_guild_id),
    )


# ======================= #
# === Player commands === #
# ======================= #
@register_slash_command(SlashCommand(SlashCommand.train))
async def register_train_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await player_command_handler.train_command(interaction)


@register_slash_command(SlashCommand(SlashCommand.submit))
async def register_submit_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await player_command_handler.submit_command(interaction)


@register_slash_command(SlashCommand(SlashCommand.time))
async def register_time_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await player_command_handler.time_command(interaction)


@register_slash_command(SlashCommand(SlashCommand.give_up))
async def register_give_up_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await player_command_handler.give_up_command(interaction)


# ========================= #
# === Reviewer commands === #
# ========================= #
@register_slash_command(SlashCommand(SlashCommand.claim))
@discord.app_commands.default_permissions(administrator=True)
async def register_claim_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await reviewer_command_handler.claim_command(interaction)


@register_slash_command(SlashCommand(SlashCommand.reject))
@discord.app_commands.default_permissions(administrator=True)
async def register_reject_command(interaction: discord.Interaction):
    await interaction.response.defer()
    return await reviewer_command_handler.reject_command(interaction)


@register_slash_command(SlashCommand(SlashCommand.approve))
@discord.app_commands.default_permissions(administrator=True)
async def register_approve_command(interaction: discord.Interaction, score: float):
    await interaction.response.defer()
    return await reviewer_command_handler.approve_command(interaction, score)


# ====================== #
# === Admin commands === #
# ====================== #
@register_slash_command(SlashCommand(SlashCommand.set_rank))
@discord.app_commands.default_permissions(administrator=True)
async def register_set_rank_command(
    interaction: discord.Interaction, user_discord_name: str, rank: str
):
    await interaction.response.defer()
    return await admin_command_handler.set_rank(
        interaction=interaction, user_discord_name=user_discord_name, rank=rank
    )


@register_slash_command(SlashCommand(SlashCommand.wipe_state))
@discord.app_commands.default_permissions(administrator=True)
async def register_wipe_state_command(
    interaction: discord.Interaction,
    users: bool = True,
    missions: bool = True,
    channels: bool = True,
    threads: bool = True,
    all_reviews_channel_messages: bool = True,
):
    await interaction.response.defer()
    return await admin_command_handler.wipe_state(
        interaction=interaction,
        users=users,
        missions=missions,
        channels=channels,
        threads=threads,
        all_reviews_channel_messages=all_reviews_channel_messages,
    )


@discord_client.client.event
async def on_ready():
    return await event_handler.on_ready()


@discord_client.client.event
async def on_member_join(member):
    return await event_handler.on_member_join(member)


discord_client.client.run(discord_client.secret_token)
