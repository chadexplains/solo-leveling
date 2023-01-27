import datetime
import os
import unittest
from unittest.mock import AsyncMock

import dotenv

from airtable_client import AirtableClient
from discord_client import DiscordClient
from google_client import GoogleClient
from mission import Mission
from stage import Stage
from state import State
from time_limit_config import TimeLimitConfig
from user import User
from utc_time import UtcTime

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


class dotdict(dict):
    def __getattr__(self, name):
        return self[name]


fake_missions = []
fake_user = User.of_dict(
    dotdict(
        {
            "record_id": "record_id",
            "fields": dotdict(
                {
                    "discord_name": "discord_name",
                    "discord_channel_id": "discord_channel_id",
                    "discord_id": "discord_id",
                    "rank": "foundation",
                }
            ),
        }
    )
)

airtable_client.rows = AsyncMock(return_value=fake_missions)
airtable_client.row = AsyncMock(return_value=fake_user)

time_limit_config = TimeLimitConfig(
    design=datetime.timedelta(minutes=10),
    code=datetime.timedelta(minutes=20),
    unclaimed_review=datetime.timedelta(minutes=10),
    claimed_review=datetime.timedelta(minutes=20),
)

state = State(
    airtable_client=airtable_client,
    discord_client=discord_client,
    google_client=google_client,
    enforce_time_limits_every=datetime.timedelta(minutes=1),
    time_limit_config=time_limit_config,
)


def add_mission_with_scores(design_score: float, code_score: float):
    fake_missions.append(
        Mission.of_dict(
            dotdict(
                {
                    "record_id": "record_id",
                    "fields": dotdict(
                        {
                            "discord_channel_id": "discord_channel_id",
                            "player_discord_id": "player_discord_id",
                            "question_id": "question_id",
                            "reviewer_discord_id": "reviewer_discord_id",
                            "stage": Stage.of_string("completed"),
                            "design": "design",
                            "code": "code",
                            "design_score": design_score,
                            "code_score": code_score,
                            "start_time": str(UtcTime.now()),
                            "entered_stage_time": str(UtcTime.now()),
                            "design_completion_time": str(UtcTime.now()),
                            "design_review_completion_time": str(UtcTime.now()),
                            "code_completion_time": str(UtcTime.now()),
                            "code_review_completion_time": str(UtcTime.now()),
                        }
                    ),
                }
            )
        )
    )


class TestState(unittest.IsolatedAsyncioTestCase):
    async def test_level_changes_only_mission(self):
        add_mission_with_scores(design_score=1.0, code_score=2.0)  # adds 3 levels (3 total)
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 3
        assert level_delta == 3
        assert levels_until_evolution == 7
        assert not evolving
        assert current_rank == "foundation"

        add_mission_with_scores(design_score=2.0, code_score=3.0)  # adds 5 levels (8 total)
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 8
        assert level_delta == 5
        assert levels_until_evolution == 2
        assert not evolving
        assert current_rank == "foundation"

        add_mission_with_scores(design_score=3.0, code_score=4.0)  # adds 7 levels (15 total)
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 15
        assert level_delta == 7
        assert levels_until_evolution == 5
        assert evolving
        assert current_rank == "copper"

        add_mission_with_scores(design_score=8.0, code_score=4.0)  # adds 12 levels (27 total)
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 27
        assert level_delta == 12
        assert levels_until_evolution == 3
        assert evolving
        assert current_rank == "iron"

        add_mission_with_scores(design_score=8.0, code_score=4.0)  # adds 12 levels (39 total)
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 39
        assert level_delta == 12
        assert levels_until_evolution == 1
        assert evolving
        assert current_rank == "jade"

        add_mission_with_scores(
            design_score=1.0, code_score=2.0
        )  # adds 0 levels (39 total), since first mission is no longer counted
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 39
        assert level_delta == 0
        assert levels_until_evolution == 1
        assert not evolving
        assert current_rank == "jade"

        add_mission_with_scores(
            design_score=0.0, code_score=0.0
        )  # reduces 5 levels (34 total), since second missions is no longer counted
        mission = fake_missions[-1]
        (
            new_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        ) = await state.get_level_changes(mission)

        assert new_level == 34
        assert level_delta == -5
        assert levels_until_evolution == 6
        assert not evolving
        assert current_rank == "jade"
