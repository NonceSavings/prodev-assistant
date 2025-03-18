from flask import Flask
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from config.settings import (
    SIGNING_SECRET, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SLACK_APP_TOKEN,
    oauth_settings, state_store, authorize_url_generator
)
from slacke.events import handle_message_events, handle_app_mention_events
from slacke.commands import handle_update_bot
from slacke.oauth import install, oauth_redirect
from agents.llm_agent import agent, llm

flask_app = Flask(__name__)

bolt_app = App(
    signing_secret=SIGNING_SECRET,
    oauth_settings=oauth_settings,
    token_verification_enabled=False
)

handler = SlackRequestHandler(bolt_app)

# Register Slack event handlers
bolt_app.event("message")(handle_message_events)
bolt_app.event("app_mention")(handle_app_mention_events)
bolt_app.command("/update-bot")(handle_update_bot)

# Flask routes
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/slack/install", methods=["GET"])
def slack_install():
    return handler.handle(request)

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def slack_oauth_redirect():
    return oauth_redirect()

@flask_app.route('/slack/commands/change-profile', methods=['POST'])
def change_profile():
    # Get data from the slash command
    data = request.form
    text = data.get('text', '')
    team_id = data.get('team_id')
    # team_id = 
    
    # Parse the command arguments (username and profile_url)
    args = text.split()
    if len(args) >= 2:
        new_username = args[0]
        new_profile_url = args[1]
        
        try:
            installation_store = FileInstallationStore(base_dir="./data/installations")
            installation = installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id,
            is_enterprise_install=False
           )
            if not installation:
               logger.error(f"No installation found for team: {team_id}")
               return
            # installation_store.find
    
            if not installation:
              logger.error(f"No installation found for team: {team_id}")
              return
            # For user tokens only (not bot tokens)
            # This requires user token with users.profile:write scope
            # Note: This doesn't work with bot tokens as mentioned earlier
         
            # For the specific message posting with custom appearance
            # This works with bot tokens if you have chat:write.customize scope
            client = WebClient(token=installation.bot_token)
            channel_id = data.get('channel_id')
            client.chat_postMessage(
                channel=channel_id,
                text=f"This message appears with my new identity!",
                username=new_username,
                icon_url=new_profile_url
            )
            supabase.table("teams").insert([{
                "team_id":team_id,
                "username":new_username,
                "image_url":new_profile_url
            }]).execute()
                
        except SlackApiError as e:
            return jsonify({
                "response_type": "ephemeral",
                "text": f"Error: {e.response['error']}"
            })
    else:
        return jsonify({
            "response_type": "ephemeral",
            "text": "Usage: /change-profile [new_username] [profile_image_url]"
        })

@flask_app.route("/", methods=["GET"])
def home():
    return "Slack Bot is running! <a href='/slack/install'>Install this bot</a>"

# if __name__ == "__main__":
#     app.run(port=int(os.getenv("PORT", 3000)))
app = flask_app