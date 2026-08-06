from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/calendar.events"] 

def get_calendar_service():
    creds = None
    if os.path.exists("calendar_token.json"):
        creds = Credentials.from_authorized_user_file("calendar_token.json", SCOPES)
    if not creds or not creds.valid:
        flow=InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("calendar_token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def create_learning_block(title:str, start_iso:str, end_iso:str) -> str:
    service = get_calendar_service()
    event = {
        "summary": title,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
    }
    created_event = service.events().insert(calendarId="primary", body=event).execute()
    return created_event.get("id")