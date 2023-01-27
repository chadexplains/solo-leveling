from typing import Dict, Optional

import airtable_client
from airtable_client import AirtableClient
from rank import Rank


class Fields:

    discord_id_field = "discord_id"
    discord_name_field = "discord_name"
    discord_channel_id_field = "discord_channel_id"
    rank_field = "rank"

    def __init__(self, discord_id: str, discord_name: str, discord_channel_id: str, rank: Rank):
        self.discord_id = discord_id
        self.discord_name = discord_name
        self.discord_channel_id = discord_channel_id
        self.rank = rank

    def to_dict(self):
        return {
            self.discord_id_field: self.discord_id,
            self.discord_name_field: self.discord_name,
            self.discord_channel_id_field: self.discord_channel_id,
            self.rank_field: str(self.rank),
        }

    @classmethod
    def of_dict(cls, fields: Dict[str, str]):
        return cls(
            discord_id=fields[cls.discord_id_field],
            discord_name=fields[cls.discord_name_field],
            discord_channel_id=fields[cls.discord_channel_id_field],
            rank=Rank.of_string(fields[cls.rank_field]),
        )

    def immutable_updates(self, updates):
        updated = self.to_dict()
        for key, value in updates.items():
            updated[key] = str(value)
        return self.of_dict(updated)

    def immutable_update(self, field, value):
        return self.immutable_updates({field: value})


class User:

    table_name = "users"

    def __init__(self, record_id: str, fields: Fields):
        self.record_id = record_id
        self.fields = fields

    @classmethod
    def of_dict(cls, data: Dict[str, str]):
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
    async def delete_rows(cls, users_to_delete, airtable_client: AirtableClient):
        await airtable_client.delete_rows(
            table_name=cls.table_name,
            record_ids=[user_to_delete.record_id for user_to_delete in users_to_delete],
        )
        return None

    async def set_rank(self, rank: Rank, airtable_client: AirtableClient):
        response = await airtable_client.update_row(
            table_name=self.table_name,
            record_id=self.record_id,
            fields=self.fields.immutable_update(field=Fields.rank_field, value=rank).to_dict(),
        )

        return self.__of_airtable_response(response)
