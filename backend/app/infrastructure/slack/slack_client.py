from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.config import settings

slack_client = WebClient(token=settings.slack_bot_token)

def post_message(channel: str, text: str):
    try:
        response = slack_client.chat_postMessage(channel=channel, text=text)
        return {"status": "success", "message": response["message"]}
    except SlackApiError as e:
        return {"status": "error", "error": str(e.response["error"])}