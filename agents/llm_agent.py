from llama_index.llms.gemini import Gemini
from llama_index.core import Settings
from llama_index.core.agent import ReActAgent
from config.settings import GEMINI_API_KEY
from tools.payment import payment_link_tool
import ollama

llm = Gemini(model="models/gemini-1.5-flash", api_key=GEMINI_API_KEY)
Settings.llm = llm

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
    try:
        response = agent.chat(prompt)
        return response.response
    except Exception as e:
        return f"Failed to communicate with Gemini: {str(e)}"

def query_ollama(prompt, model="mistral"):
    try:
        response = ollama.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Failed to communicate with Ollama: {str(e)}"