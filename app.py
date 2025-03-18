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
    return install()

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def slack_oauth_redirect():
    return oauth_redirect()

@flask_app.route("/", methods=["GET"])
def home():
    return "Slack Bot is running! <a href='/slack/install'>Install this bot</a>"

# if __name__ == "__main__":
#     app.run(port=int(os.getenv("PORT", 3000)))
app = flask_app