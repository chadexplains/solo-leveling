import datetime
from typing import FrozenSet, List

import discord
import pyairtable.formulas

import mission
import question
import user
from airtable_client import AirtableClient
from discord_client import DiscordClient
from google_client import GoogleClient
from messenger import Messenger
from mission import Mission
from question import Question
from rank import Rank
from stage import Stage
from time_limit_config import TimeLimitConfig
from user import User
from utc_time import UtcTime


class State:
    def __init__(
        self,
        *,
        airtable_client: AirtableClient,
        discord_client: DiscordClient,
        google_client: GoogleClient,
        enforce_time_limits_every: datetime.timedelta,
        time_limit_config: TimeLimitConfig,
    ):
        self.airtable_client = airtable_client
        self.discord_client = discord_client
        self.google_client = google_client
        self.messenger = Messenger(discord_client=discord_client)
        self.enforce_time_limits_every = enforce_time_limits_every
        self.time_limit_config = time_limit_config

    async def first_unasked_question(self, for_user: User):
        existing_missions = await Mission.rows(
            formula=pyairtable.formulas.match(
                {mission.Fields.player_discord_id_field: for_user.fields.discord_id}
            ),
            airtable_client=self.airtable_client,
        )

        questions_already_asked = set(
            [existing_mission.fields.question_id for existing_mission in existing_missions]
        )

        all_questions = await Question.rows(formula=None, airtable_client=self.airtable_client)

        for potential_question in all_questions:
            if potential_question.fields.question_id not in questions_already_asked:
                return potential_question

        return None

    async def give_up_mission(
        self,
        for_mission: Mission,
        thread: discord.Thread,
        where_to_follow_up: discord.TextChannel,
    ):
        mission_updates = {
            mission.Fields.stage_field: Stage.of_string("gave_up"),
        }
        updated_mission = await for_mission.update(
            fields=for_mission.fields.immutable_updates(mission_updates),
            airtable_client=self.airtable_client,
        )

        player = await self.discord_client.member(updated_mission.fields.player_discord_id)
        for_question = await Question.row(
            formula=pyairtable.formulas.match(
                {question.Fields.question_id_field: updated_mission.fields.question_id}
            ),
            airtable_client=self.airtable_client,
        )

        await self.messenger.player_gave_up(
            player=player,
            question=for_question,
            where_to_follow_up=where_to_follow_up,
        )

    async def get_time_for_mission(
        self,
        for_mission: Mission,
        where_to_follow_up: discord.TextChannel,
    ):
        if for_mission.fields.stage.has_value(Stage.design):
            time_limit = self.time_limit_config.design
        else:
            time_limit = self.time_limit_config.code

        time_remaining = max(
            time_limit - for_mission.time_in_stage(now=UtcTime.now()),
            datetime.timedelta(seconds=0),
        )

        await self.messenger.get_time_for_mission(
            time_remaining=time_remaining,
            where_to_follow_up=where_to_follow_up,
        )

    async def create_mission(
        self,
        player_discord_id: str,
        channel: discord.TextChannel,
        where_to_follow_up: discord.TextChannel,
    ):
        player = await User.row(
            formula=pyairtable.formulas.match({user.Fields.discord_id_field: player_discord_id}),
            airtable_client=self.airtable_client,
        )

        mission_question = await self.first_unasked_question(player)
        if not mission_question:
            return None

        question_id = mission_question.fields.question_id
        mission_channel = await self.discord_client.create_private_channel(
            member_id=player_discord_id,
            channel_name=f"{question_id}",
        )
        player = await self.discord_client.member(player_discord_id)
        link = self.google_client.create_template_instance(mission_question)

        now = UtcTime.now()
        training_mission = await Mission.create(
            fields=mission.Fields(
                discord_channel_id=str(mission_channel.id),
                review_discord_channel_id=None,
                player_discord_id=player_discord_id,
                reviewer_discord_id=None,
                question_id=question_id,
                stage=Stage(value=Stage.design),
                design_score=None,
                code_score=None,
                start_time=now,
                entered_stage_time=now,
                design_completion_time=now,
                design_review_completion_time=now,
                code_completion_time=now,
                code_review_completion_time=now,
                link=link,
            ),
            airtable_client=self.airtable_client,
        )

        _ = await self.messenger.player_started_training_mission(
            player=player,
            channel=channel,
            where_to_follow_up=where_to_follow_up,
            guild_id=self.discord_client.get_guild_id(),
            question_id=question_id,
            link=link,
            training_mission=training_mission,
        )

        return training_mission

    async def update_mission(
        self,
        mission_to_update: Mission,
        channel: discord.TextChannel,
        where_to_follow_up: discord.TextChannel,
    ):
        player = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
            ),
            airtable_client=self.airtable_client,
        )

        now = UtcTime.now()
        time_field = f"{mission_to_update.fields.stage}_completion_time"

        mission_updates = {
            mission.Fields.stage_field: mission_to_update.fields.stage.next(),
            mission.Fields.entered_stage_time_field: now,
            time_field: now,
        }

        stage_submitted = mission_to_update.fields.stage
        if not stage_submitted.has_value(Stage.design) and not stage_submitted.has_value(
            Stage.code
        ):
            raise Exception(
                f"""player attempted to submit a mission in review or completed (stage: {stage_submitted}), but we already filtered for this. is this a bug?"""
            )

        updated_mission = await mission_to_update.update(
            fields=mission_to_update.fields.immutable_updates(mission_updates),
            airtable_client=self.airtable_client,
        )

        _ = await self.messenger.player_submitted_stage(
            player,
            updated_mission,
            stage_submitted,
            time_taken=mission_to_update.time_in_stage(now),
            channel=channel,
            where_to_follow_up=where_to_follow_up,
        )

        # TODO: revert all state changes if theres any exceptions

    async def sync_discord_role(self, for_user: User):
        bot_discord_member = await self.discord_client.bot_member()
        bot_user = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_id_field: str(bot_discord_member.id)}
            ),
            airtable_client=self.airtable_client,
        )

        if for_user.fields.rank >= bot_user.fields.rank:
            return None

        _ = await self.discord_client.set_role(
            member_id=for_user.fields.discord_id,
            role_name=for_user.fields.rank.to_string_hum(),
        )

    @staticmethod
    def get_rank(discord_member: discord.Member):
        highest_rank = Rank(value=Rank.foundation)

        for role in discord_member.roles:
            active_rank = Rank.of_string_hum(role.name)
            if active_rank is not None and active_rank > highest_rank:
                highest_rank = active_rank

        return highest_rank

    async def create_user(self, discord_member: discord.Member):
        discord_id = str(discord_member.id)
        discord_name = discord_member.name
        path_channel = await self.discord_client.create_private_channel(
            discord_id, channel_name=f"""{discord_name}-path"""
        )

        new_user = await User.create(
            fields=user.Fields(
                discord_id,
                discord_name,
                discord_channel_id=str(path_channel.id),
                rank=self.get_rank(discord_member),
            ),
            airtable_client=self.airtable_client,
        )

        _ = await self.sync_discord_role(for_user=new_user)

        _ = await self.messenger.welcome_new_discord_member(
            discord_member=discord_member, path_channel=path_channel
        )

        return (new_user, path_channel)

    async def set_rank(self, for_user: User, rank: Rank):
        updated_user = await for_user.set_rank(rank, airtable_client=self.airtable_client)
        await self.sync_discord_role(for_user=updated_user)
        return updated_user

    async def delete_all_users(self) -> List[User]:
        users_to_delete = await User.rows(formula=None, airtable_client=self.airtable_client)
        _ = await User.delete_rows(users_to_delete, airtable_client=self.airtable_client)
        return users_to_delete

    async def delete_all_missions(self) -> List[Mission]:
        missions_to_delete = await Mission.rows(formula=None, airtable_client=self.airtable_client)
        _ = await Mission.delete_rows(missions_to_delete, airtable_client=self.airtable_client)
        return missions_to_delete

    async def delete_all_channels(
        self, except_for: FrozenSet[discord.TextChannel]
    ) -> List[discord.TextChannel]:
        channels_to_delete = await self.discord_client.channels()
        except_for = frozenset([channel.id for channel in except_for])
        channels_to_delete = [
            channel_to_delete
            for channel_to_delete in channels_to_delete
            if channel_to_delete.id not in except_for
        ]
        for channel_to_delete in channels_to_delete:
            _ = await channel_to_delete.delete()
        return channels_to_delete

    async def enforce_time_limits(self):
        print("enforcing time limits")
        all_missions = await Mission.rows(formula=None, airtable_client=self.airtable_client)

        now = UtcTime.now()

        for mission_to_check in all_missions:
            time_in_stage = mission_to_check.time_in_stage(now)

            if (
                mission_to_check.fields.stage.has_value(Stage.design)
                and time_in_stage >= self.time_limit_config.design
            ) or (
                mission_to_check.fields.stage.has_value(Stage.code)
                and time_in_stage >= self.time_limit_config.code
            ):
                mission_question = await Question.row(
                    formula=pyairtable.formulas.match(
                        {question.Fields.question_id_field: mission_to_check.fields.question_id}
                    ),
                    airtable_client=self.airtable_client,
                )
                _ = await self.messenger.player_is_out_of_time_for_mission(
                    mission_past_due=mission_to_check,
                    expected_solution=mission_question.solution_for_stage(
                        mission_to_check.fields.stage
                    ),
                )
                _ = await mission_to_check.update(
                    fields=mission_to_check.fields.immutable_updates(
                        {mission.Fields.entered_stage_time_field: UtcTime.now()}
                    ),
                    airtable_client=self.airtable_client,
                )
            elif (
                mission_to_check.fields.stage.in_review()
                and mission_to_check.fields.reviewer_discord_id is None
                and time_in_stage >= self.time_limit_config.unclaimed_review
            ):
                _ = await self.messenger.review_needs_to_be_claimed(for_mission=mission_to_check)
            elif (
                mission_to_check.fields.stage.in_review()
                and time_in_stage >= self.time_limit_config.claimed_review
            ):
                _ = await self.messenger.reviewer_needs_to_review(for_mission=mission_to_check)

    async def get_level_changes(self, for_mission):
        # steps:
        # - find previously completed missions
        # - we combine scores of the previous HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE completed missions
        #   to calculate a users level/rank
        # - if the user hasn't completed enough missions, we just add all scores up to get their level
        # - we calculate the score_delta (current level using newest mission - previous level not including
        #   current mission
        completed_missions = await Mission.rows(
            formula=pyairtable.formulas.match(
                {
                    mission.Fields.player_discord_id_field: for_mission.fields.player_discord_id,
                    mission.Fields.stage_field: str(for_mission.fields.stage),
                }
            ),
            airtable_client=self.airtable_client,
        )
        completed_missions.sort(key=lambda mission: mission.fields.code_review_completion_time)

        # filter to just the scores from missions
        scores_from_completed_missions = list(
            map(
                lambda question: (
                    question.fields.design_score,
                    question.fields.code_score,
                ),
                completed_missions,
            )
        )
        not_enough_scores = (
            len(scores_from_completed_missions) <= Mission.HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE
        )

        # calculate the existing level for the user
        previous_scores = (
            scores_from_completed_missions[:-1]
            if not_enough_scores
            else scores_from_completed_missions[
                -(Mission.HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE + 1) : -1
            ]
        )
        previous_level = int(State.calculate_level(previous_scores))

        current_scores = [scores_from_completed_missions[-1]]
        current_level = None

        # calculate the new level for the user
        if not_enough_scores:
            current_level = int(State.calculate_level(previous_scores + current_scores))
        else:
            current_level = int(State.calculate_level(previous_scores[1:] + current_scores))

        # calculate what the level delta (what is the current level - previous level of the user)
        level_delta = current_level - previous_level
        levels_until_evolution = ((int(current_level / 10) + 1) * 10) - current_level

        # fetch ranks and see if this user is evolving
        user_to_update = await User.row(
            formula=pyairtable.formulas.match(
                {user.Fields.discord_id_field: for_mission.fields.player_discord_id}
            ),
            airtable_client=self.airtable_client,
        )
        previous_rank = user_to_update.fields.rank.get_rank_for_level(previous_level)
        current_rank = user_to_update.fields.rank.get_rank_for_level(current_level)
        evolving = True if previous_rank != current_rank else False

        return (
            current_level,
            level_delta,
            levels_until_evolution,
            evolving,
            current_rank,
        )

    @staticmethod
    def calculate_level(scores):
        aggregate_score = 0.0

        for score in scores:
            aggregate_score += score[0]
            aggregate_score += score[1]

        return aggregate_score
