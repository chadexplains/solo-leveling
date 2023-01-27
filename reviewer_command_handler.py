import discord
import pyairtable

import mission
import question
import user
from mission import Mission
from question import Question
from stage import Stage
from state import State
from user import User
from utc_time import UtcTime


class ReviewerCommandHandler:
    def __init__(self, *, state: State):
        self.__state = state

    async def claim_command(self, interaction: discord.Interaction):
        try:
            # TODO: store thread id in mission row so we can look up by it
            question_discord_channel_id = str(interaction.channel.name.split("-")[1])
            mission_to_update = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.discord_channel_id_field: question_discord_channel_id}
                ),
                airtable_client=self.__state.airtable_client,
            )
        except Exception:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=None,
                suggested_command=None,
            )
            return None
        else:
            if not mission_to_update.fields.stage.in_review():
                return await interaction.followup.send("""Review already claimed!""")

            question_to_update = await Question.row(
                formula=pyairtable.formulas.match(
                    {question.Fields.question_id_field: mission_to_update.fields.question_id}
                ),
                airtable_client=self.__state.airtable_client,
            )

            await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(
                    {
                        mission.Fields.review_discord_channel_id_field: str(interaction.channel.id),
                        mission.Fields.reviewer_discord_id_field: interaction.user.id,
                    }
                ),
                airtable_client=self.__state.airtable_client,
            )

            await self.__state.messenger.review_was_claimed(
                mission_to_update, question_to_update, interaction.followup
            )

    async def approve_command(self, interaction: discord.Interaction, score: float):
        try:
            mission_to_update = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.review_discord_channel_id_field: str(interaction.channel.id)}
                ),
                airtable_client=self.__state.airtable_client,
            )
        except Exception:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=None,
                suggested_command=None,
            )
            return None
        else:
            if not mission_to_update.fields.stage.in_review():
                return await interaction.followup.send("""Approval already provided!""")

            # 1) update mission to reflect review values/scores
            state_field = mission.Fields.stage_field
            state_value = mission_to_update.fields.stage.next()

            score_field = (
                mission.Fields.code_score_field
                if mission_to_update.fields.stage.in_code()
                else mission.Fields.design_score_field
            )

            time_field = f"{mission_to_update.fields.stage}_completion_time"
            updated_mission = await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(
                    {
                        state_field: state_value,
                        score_field: score,
                        mission.Fields.entered_stage_time_field: UtcTime.now(),
                        mission.Fields.review_discord_channel_id_field: "",
                        mission.Fields.reviewer_discord_id_field: "",
                        time_field: UtcTime.now(),
                    }
                ),
                airtable_client=self.__state.airtable_client,
            )

            # 2) tell the player about the review outcome
            user_to_update = await User.row(
                formula=pyairtable.formulas.match(
                    {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
                ),
                airtable_client=self.__state.airtable_client,
            )

            question_channel = await self.__state.discord_client.channel(
                updated_mission.fields.discord_channel_id
            )

            path_channel = await self.__state.discord_client.channel(
                user_to_update.fields.discord_channel_id
            )

            player_discord_member = await self.__state.discord_client.member(
                user_to_update.fields.discord_id
            )

            # 3) update the google doc with the score
            self.__state.google_client.update_document(
                link=updated_mission.fields.link, score_field=score_field, score_value=score
            )

            await self.__state.messenger.mission_approved(
                player_discord_member,
                updated_mission,
                question_channel,
                interaction.followup,
                path_channel,
                score,
            )

            # 4) tell player about level changes
            user_to_update = await User.row(
                formula=pyairtable.formulas.match(
                    {user.Fields.discord_id_field: mission_to_update.fields.player_discord_id}
                ),
                airtable_client=self.__state.airtable_client,
            )
            if updated_mission.fields.stage.has_value(Stage.completed):
                (
                    new_level,
                    level_delta,
                    levels_until_evolution,
                    evolving,
                    current_rank,
                ) = await self.__state.get_level_changes(updated_mission)

                await self.__state.messenger.mission_completed(
                    user_to_update,
                    question_channel,
                    path_channel,
                    self.__state.set_rank,
                    evolving=evolving,
                    current_rank=current_rank,
                    level_delta=level_delta,
                    new_level=new_level,
                    levels_until_evolution=levels_until_evolution,
                )

    async def reject_command(self, interaction: discord.Interaction):
        try:
            mission_to_update = await Mission.row(
                formula=pyairtable.formulas.match(
                    {mission.Fields.review_discord_channel_id_field: str(interaction.channel.id)}
                ),
                airtable_client=self.__state.airtable_client,
            )
        except Exception:
            _ = await self.__state.messenger.command_cannot_be_run_here(
                where_to_follow_up=interaction.followup,
                expected_location=None,
                suggested_command=None,
            )
            return None
        else:
            if not mission_to_update.fields.stage.in_review():
                return await interaction.followup.send("""Review already completed!""")

            state_field = mission.Fields.stage_field
            state_value = mission_to_update.fields.stage.previous()
            time_field = f"{mission_to_update.fields.stage}_completion_time"

            await mission_to_update.update(
                fields=mission_to_update.fields.immutable_updates(
                    {
                        state_field: state_value,
                        mission.Fields.entered_stage_time_field: UtcTime.now(),
                        time_field: UtcTime.now(),
                    }
                ),
                airtable_client=self.__state.airtable_client,
            )

            question_channel = await self.__state.discord_client.channel(
                mission_to_update.fields.discord_channel_id
            )

            player = await self.__state.discord_client.member(
                mission_to_update.fields.player_discord_id
            )

            await self.__state.messenger.mission_rejected(
                player, mission_to_update, question_channel, interaction.followup
            )
