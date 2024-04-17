import asyncio
import platform
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler, CommandHandler, 
                          ContextTypes, MessageHandler, filters)
import re

# Import the configuration and logging utilities
from utils.config import Config
from utils.logging import setup_logging

# Additional imports for your handlers
from features.character import show_profile, action_callback_handler, handle_create_character, handle_character_creation_callback
from features.actions import home_action_callback_handler, activities_action_callback_handler
from features.jobs import show_jobs, job_callback_handler
from features.store import store_action_callback_handler, buy_item_callback_handler
from features.games import game_action_callback_handler
from features.debug import close_keyboard, set_health, set_hunger, set_mood, set_exp, set_money, end_job, end_game, end_activity

# Setup logging
logger = setup_logging()

# Use Config class for the TOKEN
TOKEN = Config.TOKEN

# Fix for Windows Async
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text='Доступные текстовые команды:\n'
                                        '"Мой троян" - Показать профиль вашего трояна.\n'
                                        '"Троян работяга" - Показать доступные работы.\n')

if __name__ == '__main__':
    # Bot application setup
    application = ApplicationBuilder().token(TOKEN).read_timeout(10).write_timeout(10).connect_timeout(10).build()

    # Command handlers
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    close_keyboard_handler = CommandHandler('close_keyboard', close_keyboard)

    # Debug command handlers
    health_handler = CommandHandler('set_health', set_health)
    hunger_handler = CommandHandler('set_hunger', set_hunger)
    mood_handler = CommandHandler('set_mood', set_mood)
    exp_handler = CommandHandler('set_exp', set_exp)
    money_handler = CommandHandler('set_money', set_money)
    end_job_handler = CommandHandler('end_job', end_job)
    end_game_handler = CommandHandler('end_game', end_game)
    end_activity_handler = CommandHandler('end_activity', end_activity)

    # Message handlers
    create_character_handler = MessageHandler(filters.Regex(re.compile('^заспаунить трояна$', re.IGNORECASE)), handle_create_character)
    profile_handler = MessageHandler(filters.Regex(re.compile('^мой троян$', re.IGNORECASE)), show_profile)
    work_handler = MessageHandler(filters.Regex(re.compile('^троян работяга$', re.IGNORECASE)), show_jobs)

    # Callback query handlers
    reset_character_confirmation_handler = CallbackQueryHandler(handle_character_creation_callback, pattern='^(confirm_create|cancel_create):')
    action_handler = CallbackQueryHandler(action_callback_handler, pattern='^profile_action:')
    home_action_handler = CallbackQueryHandler(home_action_callback_handler, pattern='^home_action:')
    store_action_handler = CallbackQueryHandler(store_action_callback_handler, pattern='^store_action:')
    buy_item_handler = CallbackQueryHandler(buy_item_callback_handler, pattern='^buy_item:')
    job_handler = CallbackQueryHandler(job_callback_handler, pattern='^(job:|jobs_action:)')
    activity_handler = CallbackQueryHandler(activities_action_callback_handler, pattern='^activities_action:')
    game_handler = CallbackQueryHandler(game_action_callback_handler, pattern='^game_action:')

    # Registering all handlers
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    # Debug handlers
    # DO NOT REMOVE
    application.add_handler(close_keyboard_handler)
    # Debug handlers
    # TO BE REMOVED
    # application.add_handler(health_handler)
    # application.add_handler(hunger_handler)
    # application.add_handler(mood_handler)
    # application.add_handler(exp_handler)
    # application.add_handler(money_handler)
    # application.add_handler(end_job_handler)
    # application.add_handler(end_game_handler)
    # application.add_handler(end_activity_handler)
    # Message handlers
    application.add_handler(create_character_handler)
    application.add_handler(reset_character_confirmation_handler)
    application.add_handler(profile_handler)
    application.add_handler(action_handler)
    application.add_handler(home_action_handler)
    application.add_handler(store_action_handler)
    application.add_handler(buy_item_handler)
    application.add_handler(work_handler)
    application.add_handler(job_handler)
    application.add_handler(activity_handler)
    application.add_handler(game_handler)

    # Run the bot
    application.run_polling()
