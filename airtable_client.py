from typing import Dict, List, Optional

import pyairtable


class Response:
    def __init__(self, response: Dict[str, str]):
        self.record_id = response["id"]
        self.fields = response["fields"]


class AirtableClient:
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id

    def __table(self, table_name: str):
        return pyairtable.Table(api_key=self.api_key, base_id=self.base_id, table_name=table_name)

    async def rows(self, table_name: str, formula: Optional[str]):
        table = self.__table(table_name=table_name)

        responses = None
        if formula is None:
            responses = table.all()
        else:
            responses = table.all(formula=formula)

        return [Response(response) for response in responses]

    async def row(self, table_name: str, formula: Optional[str]):
        responses = await self.rows(table_name, formula)

        if len(responses) != 1:
            return None

        return responses[0]

    async def write_row(self, table_name: str, fields: Dict[str, str]):
        return Response(self.__table(table_name).create(fields))

    async def write_rows(self, table_name: str, all_fields: List[Dict[str, str]]):
        return [
            Response(response) for response in self.__table(table_name).batch_create(all_fields)
        ]

    async def update_row(self, table_name: str, record_id: str, fields: Dict[str, str]):
        return Response(self.__table(table_name).update(record_id, fields))

    async def delete_rows(self, table_name: str, record_ids: List[str]):
        self.__table(table_name).batch_delete(record_ids)
