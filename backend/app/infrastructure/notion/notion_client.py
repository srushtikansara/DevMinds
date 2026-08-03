# app/infrastructure/notion/notion_client.py
from notion_client import Client
from app.config import settings

notion = Client(auth=settings.notion_token, notion_version="2022-06-28")


def log_application(job_title: str, company: str, fit_score: float, summary: str):
    notion.pages.create(
        parent={"database_id": settings.notion_database_id},
        properties={
            "Name": {"title": [{"text": {"content": job_title}}]},
            "Company": {"rich_text": [{"text": {"content": company}}]},
            "Status": {"status": {"name": "Prepared"}},
            "Fit Score": {"number": fit_score},
        },
        children=[
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": summary}}]}}
        ],
    )