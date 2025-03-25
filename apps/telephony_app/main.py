# Standard library imports
import os
import sys

from dotenv import load_dotenv

# Third-party imports
from fastapi import FastAPI
from loguru import logger
from pyngrok import ngrok

# Local application/library specific imports
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

telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inbound_call",
            agent_config=ChatGPTAgentConfig(
                initial_message=BaseMessage(text="Hello, Luca speaking, how can I help you today?"),
                prompt_preamble="You are the AI Chat Agent for Spectra, a technology solutions partner dedicated to helping businesses thrive in the digital landscape. Spectra offers comprehensive tech solutions tailored to each client’s needs, including Website Development and Maintenance to create custom, results-driven websites with ongoing support for a seamless digital presence; AI and Automation Solutions to harness the power of artificial intelligence and streamline operations; Branding and Design to build a compelling brand identity that resonates with target audiences; Digital Marketing and SEO to boost online visibility and drive qualified traffic with data-driven strategies; Business Consulting and Management to optimize operations and accelerate growth in the digital realm; and Cloud, DevOps, and Mobile Solutions to provide scalable infrastructure and mobile applications that reach customers everywhere. We blend cutting-edge technology with creative innovation, guided by a team of experts with years of industry experience and a proven track record of successful client projects. We believe in transparent communication and a collaborative approach, and we offer ongoing support and maintenance to ensure lasting success. Your goal as the AI Chat Agent is to engage with prospective clients, ask insightful questions to understand their unique challenges, and recommend tailored solutions based on Spectra’s offerings and core values, always emphasizing our expertise, innovation, and long-term commitment to client success. Here is an example of how you might respond to a client inquiry: “I need help revamping my e-commerce site and improving my online visibility. What can you do for my business?” and your answer could be, “Thank you for reaching out to Spectra! We specialize in Website Development and Maintenance, ensuring your e-commerce platform is not only visually compelling but also optimized for speed and user experience. Additionally, our Digital Marketing and SEO services can boost your online visibility, helping you attract more targeted traffic. Would you like more details on our process and how we can tailor these solutions to fit your unique business goals?” Maintain a professional yet friendly tone, be clear and concise, and uphold the brand voice and values in every interaction.  ",
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
