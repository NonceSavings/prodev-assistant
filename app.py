import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from llama_index.llms.ollama import Ollama
from slack_bolt.async_app import AsyncApp
from llama_index.llms.gemini import Gemini
from llama_index.core import Settings
import requests
import json
import time
from llama_index.core.agent import ReActAgent
from pydantic import BaseModel,EmailStr,validator
from llama_index.core.tools import FunctionTool
import ollama
from dotenv import load_dotenv
from typing import Optional
from supabase import create_client
from flask import Flask , request
from slack_bolt.adapter.flask import SlackRequestHandler
# from llama_index.core.llms import ChatMessage

# Initializes your app with your bot token and socket mode handler
# app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
load_dotenv()

SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
SIGNING_SECRET=os.getenv("SIGNING_SECRET")

app = App(token=SLACK_BOT_TOKEN,signing_secret=SIGNING_SECRET)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY=os.getenv("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
SLACK_APP_TOKEN=os.getenv("SLACK_APP_TOKEN")


llm = Gemini(
    model="models/gemini-1.5-flash",
    api_key=GEMINI_API_KEY,  # uses GOOGLE_API_KEY env var by default
)

Settings.llm = llm

supabase = create_client(supabase_key=SUPABASE_SERVICE_KEY,supabase_url=SUPABASE_URL)

class UserPaymentInfo(BaseModel):
    email: EmailStr
    username: str
    phone_number: str
    amount: str
    
    # @validator('age')
    # def age_must_be_valid(cls, v):
    #     if v < 18:
    #         raise ValueError('User must be at least 18 years old')
    #     if v > 120:
    #         raise ValueError('Age seems too high, please verify')
    #     return v
    
    # @validator('amount')
    # def amount_must_be_positive(cls, v):
    #     if v <= 0:
    #         raise ValueError('Amount must be greater than 0')
    #     return v

def create_payment_link(
    email: str,
    username: str,
    phone_number: str,
    amount: str,
) -> str:
    """
    Create a payment link for a user and store their information in Supabase.
    
    Args:
        email: User's email address
        username: User's preferred username
        amount: Payment amount in USD
        phone_number: Description of the payment
        
    Returns:
        URL of the payment link
    """

    try:
        # Validate user information using Pydantic model
        user_info = UserPaymentInfo(
            email=email,
            username=username,
            amount=amount,
            phone_number=phone_number
        )
        result = supabase.table("payments").insert([{
            "email":user_info.email,
            "username":user_info.username,
            "amount":user_info.amount,
            "phone_number":user_info.phone_number
        }]).execute()
        payment_id = result.data[0]["id"]
        
        payment_link_url = "http://www.fourier.com/payment/ADF321"

        return f"Payment link created successfully: {payment_link_url} your payment id is {payment_id}"
    except ValueError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        return f"Error creating payment link: {str(e)}" 

payment_link_tool = FunctionTool.from_defaults(
    name="create_payment_link",
    description="Create a payment link and store user information in the database",
    fn=create_payment_link
)

agent = ReActAgent.from_tools(
    [payment_link_tool],
    verbose=True,
    system_prompt=(
        "You are a helpful assistant that can create payment links for users. "
        "You need to collect their email, username, and age. "
        "Users must be at least 18 years old to make payments."
    )
)

def query_gemini(prompt):
    """
    Sends a prompt to ollama and get a response
    """
    try:
        # response = llm.complete(prompt)
        # return response.text
        response = agent.chat(prompt)
        return response.response
        
    except Exception as e:
        return f"Failed to communicate with gemini: {str(e)}"



# Alternative function if using Ollama
def query_ollama(prompt, model="mistral"):
    """
    Send a prompt to Ollama and get a response.
    """
    try:
        import ollama
        
        response = ollama.chat(model=model, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        
        return response['message']['content']
    
    except Exception as e:
        return f"Failed to communicate with Ollama: {str(e)}"


@app.event("message")
def handle_message_events(body, logger):
    # Only respond to messages in DMs with the bot
    if body["event"].get("channel_type") == "im":
        user = body["event"]["user"]
        text = body["event"].get("text", "")
        channel_id = body["event"]["channel"]
        
        # Acknowledge receipt with a typing indicator
        app.client.chat_postMessage(
            channel=channel_id,
            text="Thinking...",
            # thread_ts=body["event"].get("ts")
        )
        
        # Get response from local LLM
        # llm_response = query_ollama(text)
        llm_response = query_gemini(text)
        print(llm_response)
        # Or if using Ollama:
        # llm_response = query_ollama(text)
        
        # Send the LLM's response back to Slack
        app.client.chat_update(
            channel=channel_id,
            ts=app.client.chat_postMessage(
                channel=channel_id,
                text=llm_response,
                # thread_ts=body["event"].get("ts")
            )["ts"],
            text=llm_response
        )

# Make sure your event handler has the exact signature expected by Slack Bolt
@app.event("app_mention")
def handle_app_mention_events(body, logger):
    logger.info(body)
    
    # Extract event details
    event = body["event"]
    channel_id = event["channel"]
    user = event["user"]
    text = event["text"]

    
    # Strip the bot's user ID from the text
    bot_user_id = app.client.auth_test()["user_id"]
    text = text.replace(f"<@{bot_user_id}>", "").strip()
    
    try:
        # Get response from Ollama
        # llm_response = query_ollama(text)
        llm_response = query_gemini(text)
        
        # Send the LLM's response back to Slack
        app.client.chat_postMessage(
            channel=channel_id,
            text=llm_response,
            # thread_ts=event.get("ts")
        )
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        app.client.chat_postMessage(
            channel=channel_id,
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("ts")
        )

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    code = request.args.get("code")
    client = app.client
    response = client.oauth_v2_access(
        client_id=os.environ.get("SLACK_CLIENT_ID"),
        client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
        code=code,
        redirect_uri=os.environ.get("SLACK_REDIRECT_URI")
    )
    if response["ok"]:
        # Store the bot token securely (e.g., in a database) for this workspace
        print("Installed successfully:", response["access_token"])
        return "Bot installed successfully!"
    return "Installation failed."

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# @app.message("hello")
# async def message_hello(message, say):
   
#     # say() sends a message to the channel where the event was triggered
#     await say(f"Hey there <@{user}>! Do you know GOD is the Greatest and The Most Mighty One")
    
#     # Get LLM response asynchronously
#     prompt = "Who is Trump?"  # You can make this dynamic based on message text if desired
#     response = await llm.acomplete(prompt)  # Use acomplete for async
    
#     # Send the LLM response (extract text from CompletionResponse)
#     await say(str(response))



# if __name__ == "__main__":
#     # SocketModeHandler(app, SLACK_APP_TOKEN).start()
#     flask_app.run(port=os.getenv("PORT",3000))
#     # app.start(port=int(os.getenv("PORT",3000)))
app = flask_app