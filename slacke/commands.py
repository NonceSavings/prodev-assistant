from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config.settings import oauth_settings
from utils.image import download_image
from slack_sdk.oauth.installation_store import FileInstallationStore
import os

def set_bot_name(new_name, team_id):
    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
        enterprise_id=None, team_id=team_id, is_enterprise_install=False
    )
    if not installation:
        return f"No installation found for team: {team_id}"
    try:
        client = WebClient(token=installation.bot_token)
        client.users_profile_set(profile={"first_name": new_name})
        return True
    except SlackApiError as e:
        return f"Error setting name: {e.response['error']}"

def set_bot_image(image_path, team_id):
    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
        enterprise_id=None, team_id=team_id, is_enterprise_install=False
    )
    if not installation:
        return f"No installation found for team: {team_id}"
    try:
        client = WebClient(token=installation.bot_token)
        client.users_setPhoto(image=image_path)
        return True
    except SlackApiError as e:
        return f"Error setting image: {e.response['error']}"
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

def handle_update_bot(ack, body, say):
    ack()
    command_text = body.get("text", "").strip()
    if not command_text:
        say("Please provide a name and image URL, e.g., `/update-bot NewName https://example.com/image.jpg`")
        return

    parts = command_text.split(" ", 1)
    if len(parts) != 2:
        say("Invalid format. Use: `/update-bot [name] [image-url]`")
        return

    new_name, image_url = parts
    team_id = body.get("team_id")

    name_result = set_bot_name(new_name, team_id)
    if name_result is not True:
        say(name_result)
        return

    try:
        image_path = download_image(image_url)
        image_result = set_bot_image(image_path, team_id)
        if image_result is not True:
            say(image_result)
            return
        say(f"Updated bot to name '{new_name}' with new image!")
    except Exception as e:
        say(f"Error processing image: {str(e)}")