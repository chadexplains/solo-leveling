import asyncio
import json
import os
from datetime import datetime

import dotenv

import question
from airtable_client import AirtableClient
from question import Question

dotenv.load_dotenv()

airtable_api_key = os.environ["airtable_api_key"]
airtable_database_id = os.environ["airtable_database_id"]

airtable_client = AirtableClient(api_key=airtable_api_key, base_id=airtable_database_id)

snapshot_date_format = "%Y-%m-%d"

snapshots_parent_directory = "leetcode-questions/snapshots"


def snapshot_date(snapshot_directory: str):
    return datetime.strptime(snapshot_directory, snapshot_date_format)


snapshots = sorted(
    [
        snapshot_date(snapshot_directory)
        for snapshot_directory in os.listdir(snapshots_parent_directory)
    ],
    reverse=True,
)

latest_snapshot_directory = "/".join(
    [
        snapshots_parent_directory,
        snapshots[0].strftime(snapshot_date_format),
    ]
)


async def main():
    questions_to_add = []

    print(f"""parsing questions from {latest_snapshot_directory}""")

    for question_filename in os.listdir(latest_snapshot_directory):
        with open("/".join([latest_snapshot_directory, question_filename])) as question_data_file:
            question_data = json.load(question_data_file)

        question_id = question_data["id"]

        description = question_data["description"]
        if description != "":
            questions_to_add.append(
                question.Fields(
                    question_id,
                    description,
                    tags=question_data["tags"],
                    leetcode_url=f"""https://www.leetcode.com/problems/{question_id}""",
                )
            )

    print("uploading questions to airtable")

    questions_uploaded = await Question.create_many(
        all_fields=questions_to_add[:10], airtable_client=airtable_client
    )

    questions_uploaded = len(questions_uploaded)

    print(f"""uploaded {questions_uploaded} questions to airtable""")


asyncio.run(main())
