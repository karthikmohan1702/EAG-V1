import logging
import time
import schedule
from datetime import datetime
import google.generativeai as genai
from pycoingecko import CoinGeckoAPI
import requests
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import pandas as pd
import numpy as np
from config import *
import asyncio
import random
import re

# Configure detailed logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s\n%(separator)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Custom logging formatter
def log_separator(message="", char="-", length=80):
    if message:
        message = f" {message} "
    separator = char * ((length - len(message)) // 2)
    return f"{separator}{message}{separator}"

def log_step(step_name, details=""):
    logging.info(f"\n{log_separator(f'STEP: {step_name}', '=')}")
    if details:
        logging.info(details)

def log_agent(agent_name, action, data=""):
    logging.info(f"\n{log_separator(f'AGENT: {agent_name}', '-')}")
    logging.info(f"Action: {action}")
    if data:
        logging.info(f"Data: {data}")

def log_api_call(api_name, endpoint, params=""):
    logging.info(f"\n{log_separator(f'API CALL: {api_name}', '*')}")
    logging.info(f"Endpoint: {endpoint}")
    if params:
        logging.info(f"Parameters: {params}")

# Initialize APIs with logging
log_step("Initialization", "Initializing APIs and configurations")
cg = CoinGeckoAPI()
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)
logging.info("APIs initialized successfully")

class BitcoinBot:
    def __init__(self):
        log_step("Bot Initialization")
        self.price_history = []
        self.news_history = []
        self.price_threshold = DEFAULT_PRICE_THRESHOLD
        self.last_price = None
        self.last_news_check = None
        self.application = None
        self.conversation_history = []
        logging.info("Bitcoin bot initialized with default settings")

    async def sleep(self, ms):
        """Helper function for exponential backoff."""
        await asyncio.sleep(ms / 1000)

    async def get_bitcoin_price(self, retries=3):
        """Fetch current Bitcoin price from CoinGecko with retry logic."""
        log_agent("Price Agent", "Fetching current Bitcoin price")
        for attempt in range(retries):
            try:
                log_api_call("CoinGecko", "simple/price", "bitcoin-usd")
                price_data = cg.get_price(ids='bitcoin', vs_currencies='usd')
                price = price_data['bitcoin']['usd']
                logging.info(f"Successfully fetched price: ${price:,.2f}")
                return price
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}/{retries} failed: {str(e)}")
                if attempt == retries - 1:
                    raise
                wait_time = (2 ** attempt) * 1000
                logging.info(f"Retrying in {wait_time}ms...")
                await self.sleep(wait_time)

    async def get_bitcoin_news(self, retries=3):
        """Fetch Bitcoin news with retry logic."""
        log_agent("News Agent", "Fetching Bitcoin news")
        for attempt in range(retries):
            try:
                log_api_call("CoinGecko", "search/trending")
                trending_data = cg.get_search_trending()
                news_items = [{
                    'title': f"{coin['item']['name']} ({coin['item']['symbol'].upper()}) is trending",
                    'source': 'CoinGecko Trends',
                    'url': f"https://www.coingecko.com/en/coins/{coin['item']['id']}"
                } for coin in trending_data['coins'][:3]]
                logging.info(f"Successfully fetched {len(news_items)} trending items")
                return news_items
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}/{retries} failed: {str(e)}")
                if attempt == retries - 1:
                    return []
                wait_time = (2 ** attempt) * 1000
                logging.info(f"Retrying in {wait_time}ms...")
                await self.sleep(wait_time)
        return []

    async def analyze_market_data(self, price_data, news_data):
        """First agent: Analyze market data."""
        log_agent("Analysis Agent 1", "Market Analysis")
        prompt = f"""
        Analyze the current Bitcoin market situation:
        Price: ${price_data:,.2f}
        
        Previous Context:
        {self.format_conversation_history()}
        
        Provide:
        1. Initial market assessment
        2. Key technical indicators
        3. Suggested areas to investigate
        """
        response = model.generate_content(prompt)
        analysis = response.text
        self.conversation_history.append({"role": "agent1", "content": analysis})
        logging.info(f"Market analysis completed:\n{analysis}")
        return analysis

    async def analyze_news_impact(self, market_analysis, news_data):
        """Second agent: Analyze news impact."""
        log_agent("Analysis Agent 2", "News Impact Analysis")
        if not news_data:
            logging.info("No news data available, skipping news analysis")
            return "No recent news data available for analysis."

        prompt = f"""
        Analyze news impact on Bitcoin:
        
        Market Analysis:
        {market_analysis}
        
        News Items:
        {self.format_news_data(news_data)}
        
        Previous Context:
        {self.format_conversation_history()}
        
        Provide:
        1. News sentiment analysis
        2. Potential price impacts
        3. Key risks and opportunities
        """
        response = model.generate_content(prompt)
        analysis = response.text
        self.conversation_history.append({"role": "agent2", "content": analysis})
        logging.info(f"News impact analysis completed:\n{analysis}")
        return analysis

    async def generate_final_recommendation(self, market_analysis, news_analysis):
        """Third agent: Generate final recommendation."""
        log_agent("Analysis Agent 3", "Final Recommendation")
        prompt = f"""
        Provide final Bitcoin analysis and recommendation:
        
        Market Analysis:
        {market_analysis}
        
        News Analysis:
        {news_analysis}
        
        Previous Context:
        {self.format_conversation_history()}
        
        Format as:
        1. Summary
        2. Key Points
        3. Recommendation
        4. Risk Factors
        """
        response = model.generate_content(prompt)
        recommendation = response.text
        self.conversation_history.append({"role": "agent3", "content": recommendation})
        logging.info(f"Final recommendation generated:\n{recommendation}")
        return recommendation

    def format_conversation_history(self):
        """Format conversation history for prompts."""
        return "\n".join([f"{item['role']}: {item['content']}" for item in self.conversation_history[-3:]])

    def format_news_data(self, news_data):
        """Format news data for prompts."""
        return "\n".join([f"- {item['title']} (Source: {item['source']})" for item in news_data])

    async def analyze_bitcoin(self, query):
        """Main analysis workflow showing multi-agent interaction."""
        log_step("Starting Bitcoin Analysis", f"Query: {query}")
        
        # Store user query
        self.conversation_history.append({"role": "user", "content": query})
        
        try:
            # Step 1: Gather Data
            log_step("Data Collection")
            price = await self.get_bitcoin_price()
            news = await self.get_bitcoin_news()
            
            # Step 2: Market Analysis (Agent 1)
            log_step("Market Analysis")
            market_analysis = await self.analyze_market_data(price, news)
            
            # Step 3: News Impact Analysis (Agent 2)
            log_step("News Analysis")
            news_analysis = await self.analyze_news_impact(market_analysis, news)
            
            # Step 4: Final Recommendation (Agent 3)
            log_step("Final Recommendation")
            final_recommendation = await self.generate_final_recommendation(market_analysis, news_analysis)
            
            log_step("Analysis Complete", "All agents have completed their analysis")
            return self.format_final_response(final_recommendation)
            
        except Exception as e:
            logging.error(f"Error in analysis workflow: {str(e)}")
            raise

    def format_final_response(self, recommendation):
        """Format the final response with HTML for Telegram."""
        def format_section(text):
            lines = text.split('\n')
            formatted_lines = []
            in_list = False
            
            for line in lines:
                line = line.strip()
                if line.upper() == line and line.endswith(':'):
                    # Close previous list if exists
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                    # Add section header
                    header = line[:-1]  # Remove colon
                    emoji = self.get_section_emoji(line)
                    formatted_lines.append(f'<b>{emoji} {header}</b>')
                elif line.startswith(('•', '-', '*')):
                    # Start list if not already in one
                    if not in_list:
                        formatted_lines.append('<ul>')
                        in_list = True
                    # Add list item
                    item_text = line.replace('•', '').replace('-', '').replace('*', '').strip()
                    formatted_lines.append(f'<li>{item_text}</li>')
                elif line:
                    # Close list if exists
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                    # Regular content
                    formatted_lines.append(f'<p>{line}</p>')
            
            # Close any open list
            if in_list:
                formatted_lines.append('</ul>')
            
            return '\n'.join(formatted_lines)

        # Format the sections
        formatted_text = format_section(recommendation)
        
        # Create the complete HTML message
        html_message = f'''
<b>🤖 Bitcoin Analysis Report</b>
<pre>───────────────────────</pre>

{formatted_text}

<pre>───────────────────────</pre>
<i>Generated by Bitcoin Analysis Bot</i>
'''
        
        return html_message

    def get_section_emoji(self, section_title):
        """Get appropriate emoji for each section type."""
        emoji_map = {
            'SUMMARY:': '📊',
            'KEY POINTS:': '💡',
            'MARKET ANALYSIS:': '📈',
            'TECHNICAL ANALYSIS:': '📉',
            'NEWS ANALYSIS:': '📰',
            'RECOMMENDATION:': '✅',
            'RISK FACTORS:': '⚠️',
            'MONITORING POINTS:': '👀',
            'ANSWER:': '▶️',
            'REASONS:': '📝',
            'SUPPORTING EVIDENCE:': '📋'
        }
        return emoji_map.get(section_title, '•')

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        welcome_message = (
            "Welcome to the Bitcoin Price Analysis Bot! 🤖\n\n"
            "Available commands:\n"
            "/setthreshold <price> - Set a price threshold for alerts\n"
            "/suggestthreshold - Get AI-suggested price threshold\n"
            "/currentprice - Get current Bitcoin price\n"
            "/currentthreshold - Get current threshold setting"
        )
        await update.message.reply_text(welcome_message)

    async def set_threshold(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /setthreshold command."""
        try:
            if not context.args:
                await update.message.reply_text("Please provide a price threshold. Example: /setthreshold 50000")
                return

            new_threshold = float(context.args[0])
            self.price_threshold = new_threshold
            await update.message.reply_text(f"Price threshold set to ${new_threshold:,.2f}")
            logging.info(f"Price threshold updated to ${new_threshold:,.2f}")
        except ValueError:
            await update.message.reply_text("Please provide a valid number for the threshold.")

    async def suggest_threshold(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Use Gemini AI to suggest a price threshold based on market analysis."""
        try:
            # Get current price and 24h price change
            current_price = await self.get_bitcoin_price()
            if current_price is None:
                await update.message.reply_text("Unable to fetch current price. Please try again later.")
                return

            # Get historical data for analysis
            historical_data = await self.get_historical_data()

            # Prepare data for Gemini analysis
            price_data = {
                'current_price': current_price,
                'price_history': historical_data['prices'],
                'market_cap': historical_data['market_caps'],
                'total_volume': historical_data['total_volumes']
            }

            prompt = f"""
            Analyze the following Bitcoin market data and suggest an appropriate price threshold for alerts:
            
            Current Price: ${current_price:,.2f}
            Price History: {price_data['price_history'][-5:]}  # Last 5 price points
            Market Cap: ${price_data['market_cap'][-1][1]:,.2f}
            Volume: ${price_data['total_volume'][-1][1]:,.2f}
            
            Please format your response as follows:

            📊 Quick Summary
            [2-3 sentences about the suggested threshold]

            💡 Key Points
            • Suggested threshold price
            • Reasoning behind the suggestion
            • Risk level (conservative/aggressive)

            📈 Market Analysis
            [2-3 sentences about current market conditions]

            ⚠️ Considerations
            • Technical factors
            • Market sentiment
            • Risk factors

            💭 Recommendation
            [1-2 sentences with final recommendation]

            Keep the response concise and easy to read. Use bullet points and emojis for better readability.
            """

            response = model.generate_content(prompt)
            
            # Format the response for better readability
            formatted_response = response.text
            # Normalize line breaks
            formatted_response = formatted_response.replace('\r\n', '\n').replace('\r', '\n')
            # Remove multiple consecutive newlines
            formatted_response = re.sub(r'\n{3,}', '\n\n', formatted_response)
            # Convert bullet points
            formatted_response = formatted_response.replace('•', '•').replace('*', '•')
            # Add proper spacing for section headers
            formatted_response = re.sub(r'(📊|💡|📈|⚠️|💭)', r'\n\n\1', formatted_response)
            # Ensure bullet points are on the same line
            formatted_response = formatted_response.replace('\n•', '•')
            # Clean up any leading/trailing whitespace
            formatted_response = formatted_response.strip()
            
            await update.message.reply_text(f"AI Analysis:\n{formatted_response}")
            
            # Extract the suggested threshold from the response
            try:
                # Look for price after "threshold" or "suggested" in the response
                price_match = re.search(r'(?:threshold|suggested).*?\$([\d,]+)', formatted_response, re.IGNORECASE)
                if price_match:
                    suggested_price = float(price_match.group(1).replace(',', ''))
                    await update.message.reply_text(
                        f"Would you like to set this threshold? Reply with /setthreshold {suggested_price}"
                    )
                else:
                    await update.message.reply_text(
                        "Could not parse suggested threshold. Please set manually using /setthreshold <price>"
                    )
            except:
                await update.message.reply_text(
                    "Could not parse suggested threshold. Please set manually using /setthreshold <price>"
                )

        except Exception as e:
            logging.error(f"Error in suggest_threshold: {e}")
            await update.message.reply_text("Error generating threshold suggestion. Please try again later.")

    async def current_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /currentprice command."""
        try:
            current_price = await self.get_bitcoin_price()
            historical_data = await self.get_historical_data()
            
            if historical_data:
                # Calculate 24h price change
                prices = historical_data['prices']
                if len(prices) >= 2:
                    current = prices[-1][1]
                    previous = prices[-2][1]
                    price_change = ((current - previous) / previous * 100)
                    
                    # Get market cap and volume
                    market_cap = historical_data['market_caps'][-1][1] if historical_data['market_caps'] else 'N/A'
                    volume = historical_data['total_volumes'][-1][1] if historical_data['total_volumes'] else 'N/A'
                    
                    message = (
                        f"Current Bitcoin Price: ${current_price:,.2f}\n"
                        f"24h Change: {price_change:.2f}%\n"
                        f"Market Cap: ${market_cap:,.2f}\n"
                        f"24h Volume: ${volume:,.2f}"
                    )
                else:
                    message = f"Current Bitcoin Price: ${current_price:,.2f}"
            else:
                message = f"Current Bitcoin Price: ${current_price:,.2f}"
            await update.message.reply_text(message)
        except Exception as e:
            logging.error(f"Error in current_price command: {str(e)}")
            await update.message.reply_text(
                f"Unable to fetch current price: {str(e)}\n"
                "Please try again later."
            )

    async def current_threshold(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /currentthreshold command."""
        await update.message.reply_text(f"Current Price Threshold: ${self.price_threshold:,.2f}")

    async def send_telegram_message(self, message):
        """Send message to Telegram."""
        try:
            await self.application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")

    def analyze_news_impact(self, news_articles, price_data):
        """Analyze news impact on price using Gemini AI."""
        try:
            # Format news articles for prompt
            news_summary = "\n".join([
                f"• {article['title']}\n  Source: {article['source']}\n  URL: {article['url']}"
                for article in news_articles
            ])

            prompt = f"""
            Analyze the following Bitcoin news articles and price data to determine potential correlations:
            
            Current Market Data:
            {price_data}

            Recent News:
            {news_summary}
            
            Provide a clear and concise analysis in the following format:

            📊 Quick Summary
            A brief overview of the current Bitcoin situation based on price and news (2-3 sentences).

            💡 Key Points
            • Most significant market movements
            • Key news impacts
            • Notable trends

            📈 Market Analysis
            Brief technical analysis of price movements and volume (2-3 bullet points).

            ⚠️ Risks & Opportunities
            Risks:
            • Risk factor 1
            • Risk factor 2

            Opportunities:
            • Opportunity 1
            • Opportunity 2

            💭 Recommendation
            Clear actionable advice based on the analysis (1-2 sentences).

            Keep each section concise and focused. Use bullet points for better readability.
            """
            
            response = model.generate_content(prompt)
            
            # Enhanced formatting of the response
            formatted_response = response.text
            
            # Clean up the formatting
            formatted_response = (formatted_response
                .replace('\r\n', '\n')
                .replace('\r', '\n')
                # Add section separators
                .replace('📊', '\n═══════════════════════\n📊')
                .replace('💭', '\n═══════════════════════\n💭')
                # Ensure consistent section spacing
                .replace('💡', '\n\n💡')
                .replace('📈', '\n\n📈')
                .replace('⚠️', '\n\n⚠️')
                # Format bullet points
                .replace('•', '•')
                .replace('\n•', '\n  •')  # Indent bullet points
                # Clean up spacing
                .replace('\n\n\n', '\n\n')
                .strip())
            
            # Add header with double-line border
            formatted_response = (
                "╔════════════════════════╗\n"
                "║  Bitcoin Market Analysis  ║\n"
                "╚════════════════════════╝\n\n"
                f"{formatted_response}"
            )
            
            return formatted_response

        except Exception as e:
            logging.error(f"Error analyzing news impact: {e}")
            return "Error analyzing news impact. Please try again later."

    async def check_price_alerts(self):
        """Check if price has crossed threshold and send alerts."""
        current_price = await self.get_bitcoin_price()
        if current_price is None:
            return

        if self.last_price is not None:
            price_change = (current_price - self.last_price) / self.last_price
            if abs(price_change) >= SIGNIFICANT_PRICE_CHANGE_THRESHOLD:
                message = f"Significant Bitcoin price change detected!\n"
                message += f"Previous price: ${self.last_price:,.2f}\n"
                message += f"Current price: ${current_price:,.2f}\n"
                message += f"Change: {price_change:.2%}"
                await self.send_telegram_message(message)

        if current_price >= self.price_threshold:
            message = f"Bitcoin price has crossed the threshold!\n"
            message += f"Current price: ${current_price:,.2f}\n"
            message += f"Threshold: ${self.price_threshold:,.2f}"
            await self.send_telegram_message(message)

        self.last_price = current_price
        self.price_history.append({
            'timestamp': datetime.now(),
            'price': current_price
        })

    async def check_news(self):
        """Check for new Bitcoin news and send alerts."""
        news_articles = await self.get_bitcoin_news()
        if not news_articles:
            return

        for article in news_articles:
            if article not in self.news_history:
                message = f"New Bitcoin News:\n"
                message += f"Title: {article['title']}\n"
                message += f"Source: {article['source']}\n"
                message += f"URL: {article['url']}"
                await self.send_telegram_message(message)
                self.news_history.append(article)

        # Analyze news impact
        if len(self.price_history) > 0:
            price_data = pd.DataFrame(self.price_history)
            analysis = self.analyze_news_impact(news_articles, price_data)
            await self.send_telegram_message(f"News Impact Analysis:\n{analysis}")

    async def setup_handlers(self):
        """Set up command handlers for the bot."""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("setthreshold", self.set_threshold))
        self.application.add_handler(CommandHandler("suggestthreshold", self.suggest_threshold))
        self.application.add_handler(CommandHandler("currentprice", self.current_price))
        self.application.add_handler(CommandHandler("currentthreshold", self.current_threshold))

    async def run(self):
        """Main bot loop."""
        logging.info("Starting Bitcoin Bot...")
        
        try:
            # Initialize the application
            self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Set up command handlers
            await self.setup_handlers()
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            
            logging.info("Bot started successfully!")
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logging.error(f"Error running bot: {e}")
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            raise
        finally:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the bot
    bitcoin_bot = BitcoinBot()
    try:
        asyncio.run(bitcoin_bot.run())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Bot stopped due to error: {e}")
    finally:
        logging.info("Bot shutdown complete") 