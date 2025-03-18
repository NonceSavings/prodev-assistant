import os
from dotenv import load_dotenv
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_bolt.oauth.oauth_settings import OAuthSettings

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SIGNING_SECRET = os.getenv("SIGNING_SECRET")
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URL")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

oauth_settings = OAuthSettings(
    client_id=SLACK_CLIENT_ID,
    client_secret=SLACK_CLIENT_SECRET,
    scopes=[
        "app_mentions:read", "assistant:write", "bookmarks:read",
        "bookmarks:write", "calls:read", "channels:history", "channels:read",
        "chat:write", "groups:history", "im:history", "chat:write.customize"
    ],
    installation_store=FileInstallationStore(base_dir="./data/installations"),
    state_store=FileOAuthStateStore(expiration_seconds=900, base_dir="./data/states"),
    install_path="/slack/install",
    redirect_uri_path="/slack/oauth_redirect",
)

state_store = FileOAuthStateStore(expiration_seconds=300, base_dir="./data")

authorize_url_generator = AuthorizeUrlGenerator(
    client_id=SLACK_CLIENT_ID,
    scopes=["app_mentions:read", "chat:write"],
    user_scopes=["search:read"],
)