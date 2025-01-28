# File: dexbot.py
import os
import yaml
import requests
import sqlalchemy as db
from telegram import Update, Bot
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ApplicationBuilder,
    ContextTypes
)

class TelegramBot:
    """Telegram integration layer for notifications and trading"""
    
    def __init__(self, config: dict):
        self.config = config['telegram']
        self.bot = Bot(token=self.config['bot_token'])
        self.application = ApplicationBuilder().token(self.config['bot_token']).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("buy", self.buy))
        self.application.add_handler(CommandHandler("sell", self.sell))
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        await update.message.re_text(
            "🚀 DexBot Trading System\n\n"
            "Available commands:\n"
            "/buy [token] [amount] - Execute buy order\n"
            "/sell [token] [amount] - Execute sell order\n"
            "/alerts [on/off] - Toggle price alerts"
        )

    async def buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle buy commands via BonkBot"""
        try:
            _, token, amount = update.message.text.split()
            response = self._execute_trade(action='buy', token=token, amount=float(amount))
            await update.message.re_text(f"✅ Buy order executed:\n{response}")
        except Exception as e:
            await update.message.re_text(f"❌ Trade failed: {str(e)}")

    async def sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle sell commands via BonkBot"""
        try:
            _, token, amount = update.message.text.split()
            response = self._execute_trade(action='sell', token=token, amount=float(amount))
            await update.message.re_text(f"✅ Sell order executed:\n{response}")
        except Exception as e:
            await update.message.re_text(f"❌ Trade failed: {str(e)}")

    def _execute_trade(self, action: str, token: str, amount: float) -> dict:
        """Execute trade through BonkBot's API"""
        return requests.post(
            self.config['bonkbot_api'],
            json={
                'action': action,
                'token': token,
                'amount': amount,
                'api_key': self.config['bonkbot_key']
            },
            timeout=10
        ).json()

    async def send_alert(self, message: str):
        """Send notifications to configured channel"""
        await self.bot.send_message(
            chat_id=self.config['channel_id'],
            text=message,
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """General message handler"""
        await update.message.re_text("Command not recognized. Use /help for available commands")

    def run(self):
        """Start the Telegram bot"""
        self.application.run_polling()

class DexBot:
    """Main trading bot with integrated Telegram support"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.tg_bot = TelegramBot(self.config)
        # Initialize other components from previous code
        # ... (previous initialization code)

    def _load_config(self, path: str) -> dict:
        """Load and validate configuration"""
        with open(path) as f:
            config = yaml.safe_load(f)
        
        required_keys = {'telegram', 'apis', 'blacklists', 'thresholds'}
        if not required_keys.issubset(config.keys()):
            raise ValueError("Invalid configuration file")
            
        return config

    async def _log_event(self, pair_record, event_type: str, data: Dict):
        """Enhanced logger with Telegram notifications"""
        # Original logging
        event_data = {
            'pair_id': pair_record.id,
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now()
        }
        self.session.execute(db.insert(self.events).values(**event_data))
        self.session.commit()
        
        # Send Telegram alert
        message = self._format_alert_message(event_type, data)
        await self.tg_bot.send_alert(message)

    def _format_alert_message(self, event_type: str, data: dict) -> str:
        """Convert event data to human-readable message"""
        templates = {
            'rug_pull_alert': "🚨 *Rug Pull Alert*\nToken: {symbol}\nLiquidity Drop: {drop}%",
            'pump_alert': "📈 *Pump Detected*\nToken: {symbol}\nPrice Change: {change}%",
            'buy': "✅ *Buy Executed*\nToken: {token}\nAmount: {amount}",
            'sell': "📉 *Sell Executed*\nToken: {token}\nAmount: {amount}"
        }
        return templates[event_type].format(**data)

    def run(self):
        """Start all components"""
        # Start Telegram bot in background
        import threading
        tg_thread = threading.Thread(target=self.tg_bot.run)
        tg_thread.start()
        
        # Start main trading loop
        self._main_loop()

if __name__ == "__main__":
    bot = DexBot()
    bot.run()
