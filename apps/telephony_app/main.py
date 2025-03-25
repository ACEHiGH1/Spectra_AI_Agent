# Standard library imports
import os
import sys

from dotenv import load_dotenv

# Third-party imports
from fastapi import FastAPI
from loguru import logger
from pyngrok import ngrok

# Local application/library specific imports
from knowledge_manager import SpectraKnowledgeManager
from speller_agent import SpellerAgentFactory

from vocode.logging import configure_pretty_logging
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.telephony.server.base import TelephonyServer, TwilioInboundCallConfig

# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
load_dotenv()

configure_pretty_logging()

app = FastAPI(docs_url=None)

config_manager = RedisConfigManager()

BASE_URL = os.getenv("BASE_URL")

if not BASE_URL:
    ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
    if ngrok_auth is not None:
        ngrok.set_auth_token(ngrok_auth)
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 3000

    # Open a ngrok tunnel to the dev server
    BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
    logger.info('ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))

if not BASE_URL:
    raise ValueError("BASE_URL must be set in environment if not using pyngrok")

# Initialize knowledge base
knowledge_manager = SpectraKnowledgeManager()

def create_agent_prompt():
    company_info = knowledge_manager.get_company_info()
    services = knowledge_manager.get_all_services()
    
    # Create a dynamic prompt based on our knowledge base
    prompt = f"You are the AI Chat Agent for {company_info['name']}, {company_info['description']}\n\n"
    prompt += "Our core values are: " + ", ".join(company_info['values']) + "\n\n"
    prompt += "We offer the following services:\n"
    
    for service in services:
        prompt += f"- {service['name']}: {service['description']}\n"
        prompt += "  Features: " + ", ".join(service['features']) + "\n"
    
    prompt += "\nYour goal is to engage with prospective clients, understand their needs, and recommend our services. "
    prompt += "Use the knowledge base to provide accurate information about our services and capabilities. "
    prompt += "Always maintain a professional yet friendly tone, be clear and concise, and emphasize our expertise and commitment to client success."
    
    return prompt

telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inbound_call",
            agent_config=ChatGPTAgentConfig(
                initial_message=BaseMessage(text="Hello, thank you for calling Spectra. How can I assist you today?"),
                prompt_preamble=create_agent_prompt(),
                generate_responses=True,
            ),
            twilio_config=TwilioConfig(
                account_sid=os.environ["TWILIO_ACCOUNT_SID"],
                auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            ),
        )
    ],
    agent_factory=SpellerAgentFactory(),
)

app.include_router(telephony_server.get_router())
