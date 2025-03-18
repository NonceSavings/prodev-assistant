from slack_sdk import WebClient
from agents.llm_agent import query_gemini
from config.settings import oauth_settings
from slack_sdk.oauth.installation_store import FileInstallationStore
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_SERVICE_KEY
import re

supabase = create_client(supabase_key=SUPABASE_SERVICE_KEY, supabase_url=SUPABASE_URL)

def handle_message_events(body, logger):
    if body["event"].get("channel_type") == "im":
        user = body["event"]["user"]
        text = body["event"].get("text", "")
        channel_id = body["event"]["channel"]
        
        bolt_app.client.chat_postMessage(channel=channel_id, text="Thinking...")
        llm_response = query_gemini(text)
        bolt_app.client.chat_update(
            channel=channel_id,
            ts=bolt_app.client.chat_postMessage(channel=channel_id, text=llm_response)["ts"],
            text=llm_response
        )

def handle_app_mention_events(body, logger):
    event = body["event"]
    channel_id = event["channel"]
    user = event["user"]
    text = event["text"]
    team_id = body.get("team_id")

    if not team_id:
        logger.error("No team_id found in request body")
        return

    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
        enterprise_id=None, team_id=team_id, is_enterprise_install=False
    )
    if not installation:
        logger.error(f"No installation found for team: {team_id}")
        return

    response = supabase.table("teams").select('*').eq("team_id", team_id).execute()
    username, image_url = None, None
    if response.data:
        user_data = response.data[0]
        username = user_data.get('username')
        image_url = user_data.get('image_url')

    mention_pattern = re.compile(r'<@([A-Z0-9]+)>')
    match = mention_pattern.search(text)
    if match:
        bot_user_id = match.group(1)
        text = text.replace(f"<@{bot_user_id}>", "").strip()

    try:
        llm_response = query_gemini(text)
        client = WebClient(token=installation.bot_token)
        if username and image_url:
            client.chat_postMessage(
                channel=channel_id, text=llm_response, username=username, icon_url=image_url
            )
        else:
            client.chat_postMessage(channel=channel_id, text=llm_response)
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        bolt_app.client.chat_postMessage(
            channel=channel_id, text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("ts")
        )