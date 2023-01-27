from typing import Dict, List, Optional

import airtable_client
from airtable_client import AirtableClient
from stage import Stage


class Fields:

    question_id_field = "question_id"
    description_field = "description"
    solution_field = "solution"
    tags_field = "tags"
    leetcode_url_field = "leetcode_url"

    def __init__(
        self,
        question_id: str,
        description: str,
        solution: str,
        tags: List[str],
        leetcode_url: str,
    ):
        self.question_id = question_id
        self.description = description
        self.solution = solution
        self.tags = tags
        self.leetcode_url = leetcode_url

    def to_dict(self):
        return {
            self.question_id_field: self.question_id,
            self.description_field: self.description,
            self.solution_field: self.solution,
            self.tags_field: ",".join(self.tags),
            self.leetcode_url_field: self.leetcode_url,
        }

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(
            question_id=fields[cls.question_id_field],
            description=fields[cls.description_field],
            solution=fields[cls.solution_field],
            tags=fields[cls.tags_field].split(","),
            leetcode_url=fields[cls.leetcode_url_field],
        )


class Question:

    table_name = "questions"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    async def create_many(cls, all_fields: List[Fields], airtable_client: AirtableClient):
        responses = await airtable_client.write_rows(
            table_name=cls.table_name,
            all_fields=[fields.to_dict() for fields in all_fields],
        )
        return [cls.__of_airtable_response(response) for response in responses]

    @classmethod
    def __of_airtable_response(cls, response: airtable_client.Response):
        return cls(record_id=response.record_id, fields=Fields.of_dict(response.fields))

    @classmethod
    async def row(cls, formula: Optional[str], airtable_client: AirtableClient):
        response = await airtable_client.row(table_name=cls.table_name, formula=formula)
        return cls.__of_airtable_response(response)

    @classmethod
    async def rows(cls, formula: Optional[str], airtable_client: AirtableClient):
        responses = await airtable_client.rows(table_name=cls.table_name, formula=formula)
        return [cls.__of_airtable_response(response) for response in responses]

    def solution_for_stage(self, stage: Stage):
        if not stage.players_turn():
            raise Exception("cant get solution for a stage that isnt the players turn")

        return self.fields.solution
