"""
Discord Bot - Listens to messages and responds using the chatbot API
"""

import os
import discord
import aiohttp
import logging
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_IDS = [int(ch_id.strip()) for ch_id in os.getenv('DISCORD_CHANNEL_IDS', '').split(',') if ch_id.strip()]
CHATBOT_API_URL = os.getenv('CHATBOT_API_URL', 'http://app:8000/chat')

# Setup Discord bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    """Called when bot is ready"""
    logger.info(f'Discord bot logged in as {bot.user}')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info(f'Listening to channels: {CHANNEL_IDS}')
    logger.info(f'Chatbot API URL: {CHATBOT_API_URL}')


@bot.event
async def on_message(message):
    """Called when a message is received"""

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Only respond to messages in configured channels
    if message.channel.id not in CHANNEL_IDS:
        return

    # Log the message
    logger.info(f'Message from {message.author} in #{message.channel.name}: {message.content}')

    # Show typing indicator
    async with message.channel.typing():
        try:
            # Call chatbot API
            response = await call_chatbot_api(message.content, str(message.author.id))

            # Send response back to Discord
            if response:
                # Discord has a 2000 character limit per message
                if len(response) > 2000:
                    # Split into multiple messages
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(response)
            else:
                await message.channel.send("Sorry, I couldn't process your request.")

        except Exception as e:
            logger.error(f'Error processing message: {str(e)}', exc_info=True)
            await message.channel.send(f"Sorry, an error occurred: {str(e)}")

    # Process commands if any
    await bot.process_commands(message)


async def call_chatbot_api(message: str, user_id: str) -> str:
    """Call the chatbot API and return the response"""

    try:
        payload = {
            "message": message,
            "conversation_id": f"discord_{user_id}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                CHATBOT_API_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data.get('answer', '')

                    # Parse the answer to extract clean message
                    clean_answer = parse_agent_response(answer)

                    if clean_answer:
                        return clean_answer
                    else:
                        return "I received your message but couldn't generate a proper response. Please try rephrasing your question."

                else:
                    error_text = await response.text()
                    logger.error(f'API error: {response.status} - {error_text}')
                    return f"API error: {response.status}"

    except asyncio.TimeoutError:
        logger.error('API call timed out')
        return "Sorry, the request timed out. Please try again."
    except Exception as e:
        logger.error(f'Error calling API: {str(e)}', exc_info=True)
        return f"Error: {str(e)}"


def parse_agent_response(answer) -> str:
    """Parse agent response to extract clean message"""

    # If it's already a clean string
    if isinstance(answer, str):
        # Check if it contains AgentAction or other debug info
        if 'AgentAction' in answer or answer.startswith('['):
            # Try to extract error messages
            if 'Error:' in answer:
                import re
                errors = re.findall(r"'(Error:[^']+)'", answer)
                if errors:
                    # Found configuration error
                    if 'No messaging service is configured' in errors[0]:
                        return "Hello! I'm your AI assistant. How can I help you today?"
                    return errors[0]
            return None
        return answer

    # If it's a list (AgentAction logs)
    if isinstance(answer, list):
        # Look for string responses (errors or messages)
        for item in answer:
            if isinstance(item, str):
                # Extract error messages
                if 'Error:' in item:
                    if 'No messaging service is configured' in item:
                        return "Hello! I'm your AI assistant. How can I help you today?"
                    return item
                # Skip AgentAction strings
                if not item.startswith('AgentAction') and not item.startswith('['):
                    return item

        # If no string found, return generic message
        return "Hello! I'm here to help. What would you like to know?"

    return None


@bot.command(name='info')
async def info_command(ctx):
    """Show chatbot information"""
    help_text = """
**Chatbot Information**

Just send a message and I'll respond using AI!

You can ask me to:
- Search for information in the knowledge base
- Summarize project updates
- Generate reports
- Review code
- Answer questions

Example messages:
- "What are the recent updates?"
- "Summarize the bug reports"
- "Tell me about project status"
    """
    await ctx.send(help_text)


@bot.command(name='ping')
async def ping_command(ctx):
    """Check if bot is responsive"""
    await ctx.send(f'Pong! Latency: {round(bot.latency * 1000)}ms')


def main():
    """Start the Discord bot"""

    if not BOT_TOKEN:
        logger.error('DISCORD_BOT_TOKEN environment variable is required')
        return

    if not CHANNEL_IDS:
        logger.error('DISCORD_CHANNEL_IDS environment variable is required')
        return

    logger.info('Starting Discord bot...')
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    import asyncio
    main()
