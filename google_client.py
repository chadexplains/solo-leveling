from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from question import Question

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]
ACCOUNT_FILE = "token.json"


class GoogleClient:
    def __init__(self):
        credentials = Credentials.from_service_account_file(ACCOUNT_FILE, scopes=SCOPES)
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.docs_service = build("docs", "v1", credentials=credentials)

    def create_template_instance(self, mission_question: Question):
        file_id = "1N1RvJ9sFoaJpsGDJ3f1gg6dYpvmKLBaEWpte60RSeok"
        copied_template = (
            self.drive_service.files()
            .copy(
                fileId=file_id,
                fields="id",
                body={"name": f"Mission: {mission_question.fields.question_id}"},
            )
            .execute()
        )
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": "{{question_id}}", "matchCase": "true"},
                    "replaceText": mission_question.fields.question_id,
                }
            },
            {
                "replaceAllText": {
                    "containsText": {"text": "{{question_description}}", "matchCase": "true"},
                    "replaceText": mission_question.fields.description.strip(),
                }
            },
            {
                "updateTextStyle": {
                    "textStyle": {"link": {"url": f"{mission_question.fields.leetcode_url}"}},
                    "range": {"startIndex": 24, "endIndex": 28},
                    "fields": "link",
                }
            },
        ]
        result = (
            self.docs_service.documents()
            .batchUpdate(
                documentId=copied_template.get("id"),
                body={"requests": requests},
                fields="documentId",
            )
            .execute()
        )
        permission = {
            "type": "anyone",
            "role": "writer",
        }
        self.drive_service.permissions().create(
            fileId=result.get("documentId"), body=permission
        ).execute()
        return f"https://docs.google.com/document/d/{result.get('documentId')}/edit"

    def update_document(self, link: str, score_field: str, score_value: float):
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": f"{score_field}", "matchCase": "true"},
                    "replaceText": str(score_value) + "/10",
                }
            }
        ]

        file = (
            self.docs_service.documents()
            .batchUpdate(
                documentId=self.get_document_id(link),
                body={"requests": requests},
                fields="documentId",
            )
            .execute()
        )

        return f"https://docs.google.com/document/d/{file.get('documentId')}/edit"

    def get_document_id(self, link: str):
        return link.split("/d/")[1].split("/edit")[0]
