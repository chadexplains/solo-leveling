import datetime
from typing import Dict, Optional

import airtable_client
from airtable_client import AirtableClient
from stage import Stage
from utc_time import UtcTime


class Fields:

    discord_channel_id_field = "discord_channel_id"
    review_discord_channel_id_field = "review_discord_channel_id"
    player_discord_id_field = "player_discord_id"
    reviewer_discord_id_field = "reviewer_discord_id"
    question_id_field = "question_id"
    stage_field = "stage"
    design_score_field = "design_score"
    code_score_field = "code_score"
    start_time_field = "start_time"
    design_completion_time_field = "design_completion_time"
    design_review_completion_time_field = "design_review_completion_time"
    code_completion_time_field = "code_completion_time"
    code_review_completion_time_field = "code_review_completion_time"
    entered_stage_time_field = "entered_stage_time"
    link_field = "link"

    def __init__(
        self,
        discord_channel_id: str,
        review_discord_channel_id: Optional[str],
        player_discord_id: str,
        reviewer_discord_id: Optional[str],
        question_id: str,
        stage: Stage,
        design_score: Optional[float],
        code_score: Optional[float],
        start_time: UtcTime,
        design_completion_time: UtcTime,
        design_review_completion_time: UtcTime,
        code_completion_time: UtcTime,
        code_review_completion_time: UtcTime,
        entered_stage_time: UtcTime,
        link: Optional[str],
    ):
        self.discord_channel_id = discord_channel_id
        self.review_discord_channel_id = review_discord_channel_id
        self.player_discord_id = player_discord_id
        self.reviewer_discord_id = reviewer_discord_id
        self.question_id = question_id
        self.stage = stage
        self.design_score = design_score
        self.code_score = code_score
        self.start_time = start_time
        self.design_completion_time = design_completion_time
        self.design_review_completion_time = design_review_completion_time
        self.code_completion_time = code_completion_time
        self.code_review_completion_time = code_review_completion_time
        self.entered_stage_time = entered_stage_time
        self.link = link

    def to_dict(self):
        def optional_to_string(optional: Optional[str]):
            return str(optional) if optional is not None else ""

        def optional_to_float(optional: Optional[float]):
            return optional if optional is not None else 0.0

        return {
            self.discord_channel_id_field: self.discord_channel_id,
            self.review_discord_channel_id_field: optional_to_string(
                self.review_discord_channel_id
            ),
            self.player_discord_id_field: self.player_discord_id,
            self.reviewer_discord_id_field: optional_to_string(self.reviewer_discord_id),
            self.question_id_field: self.question_id,
            self.stage_field: str(self.stage),
            self.design_score_field: optional_to_float(self.design_score),
            self.code_score_field: optional_to_float(self.code_score),
            self.start_time_field: str(self.start_time),
            self.design_completion_time_field: str(self.design_completion_time),
            self.design_review_completion_time_field: str(self.design_review_completion_time),
            self.code_completion_time_field: str(self.code_completion_time),
            self.code_review_completion_time_field: str(self.code_review_completion_time),
            self.entered_stage_time_field: str(self.entered_stage_time),
            self.link_field: optional_to_string(self.link),
        }

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(
            discord_channel_id=fields[cls.discord_channel_id_field],
            review_discord_channel_id=fields.get(cls.review_discord_channel_id_field, None),
            player_discord_id=fields[cls.player_discord_id_field],
            reviewer_discord_id=fields.get(cls.reviewer_discord_id_field, None),
            question_id=fields[cls.question_id_field],
            stage=Stage.of_string(fields[cls.stage_field]),
            design_score=fields.get(cls.design_score_field, None),
            code_score=fields.get(cls.code_score_field, None),
            start_time=UtcTime.of_string(fields.get(cls.start_time_field)),
            design_completion_time=UtcTime.of_string(fields.get(cls.design_completion_time_field)),
            design_review_completion_time=UtcTime.of_string(
                fields.get(cls.design_review_completion_time_field)
            ),
            code_completion_time=UtcTime.of_string(fields.get(cls.code_completion_time_field)),
            code_review_completion_time=UtcTime.of_string(
                fields.get(cls.code_review_completion_time_field)
            ),
            entered_stage_time=UtcTime.of_string(fields.get(cls.entered_stage_time_field)),
            link=fields.get(cls.link_field, None),
        )

    def immutable_updates(self, updates):
        updated = self.to_dict()
        for key, value in updates.items():
            if type(value) is float:
                updated[key] = float(value)
            else:
                updated[key] = str(value)

        return self.of_dict(updated)

    def immutable_update(self, field, value):
        return self.immutable_updates({field: value})


class Mission:

    HOW_MANY_PREVIOUS_QUESTIONS_TO_SCORE = 5
    table_name = "missions"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    def of_dict(cls, data):
        return cls(record_id=data.record_id, fields=data.fields)

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(record_id=response.record_id, fields=Fields.of_dict(response.fields))

    @classmethod
    async def create(cls, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.write_row(
            table_name=cls.table_name, fields=fields.to_dict()
        )
        return cls.__of_airtable_response(response)

    @classmethod
    async def row(cls, formula: Optional[str], airtable_client: AirtableClient):
        response = await airtable_client.row(table_name=cls.table_name, formula=formula)
        return cls.__of_airtable_response(response)

    @classmethod
    async def rows(cls, formula: Optional[str], airtable_client: AirtableClient):
        responses = await airtable_client.rows(table_name=cls.table_name, formula=formula)
        return [cls.__of_airtable_response(response) for response in responses]

    @classmethod
    async def delete_rows(cls, missions_to_delete, airtable_client: AirtableClient):
        await airtable_client.delete_rows(
            table_name=cls.table_name,
            record_ids=[mission_to_delete.record_id for mission_to_delete in missions_to_delete],
        )
        return None

    async def update(self, fields: Fields, airtable_client: AirtableClient):
        response = await airtable_client.update_row(
            table_name=self.table_name,
            record_id=self.record_id,
            fields=fields.to_dict(),
        )
        return self.__of_airtable_response(response)

    def time_elapsed(self, now: UtcTime) -> datetime.timedelta:
        return now.diff_to_nearest_second(self.fields.start_time)

    def time_in_stage(self, now: UtcTime) -> datetime.timedelta:
        return now.diff_to_nearest_second(self.fields.entered_stage_time)

    # TODO make a helper for calculating time in different
    # stages (code is mostly the same)
    def time_in_design(self) -> datetime.timedelta:
        completion_time = UtcTime.of_string(self.fields.design_completion_time)
        start_time = UtcTime.of_string(self.fields.start_time)
        return completion_time.diff_to_nearest_second(start_time)

    def time_in_design_review(self) -> datetime.timedelta:
        completion_time = UtcTime.of_string(self.fields.design_review_completion_time)
        start_time = UtcTime.of_string(self.fields.design_completion_time)
        return completion_time.diff_to_nearest_second(start_time)

    def time_in_code(self) -> datetime.timedelta:
        completion_time = UtcTime.of_string(self.fields.code_completion_time)
        start_time = UtcTime.of_string(self.fields.design_review_completion_time)
        return completion_time.diff_to_nearest_second(start_time)

    def time_in_code_review(self) -> datetime.timedelta:
        completion_time = UtcTime.of_string(self.fields.code_review_completion_time)
        start_time = UtcTime.of_string(self.fields.code_completion_time)
        return completion_time.diff_to_nearest_second(start_time)
