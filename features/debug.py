from telegram import Update, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ContextTypes
from data.jobs import jobs
from db.db import update_character_stat, get_character
from features.character import show_profile

async def close_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send a message with a request to remove the keyboard
    await update.message.reply_text(
        "Reply keyboard closed.",
        reply_markup=ReplyKeyboardRemove(selective=True)
    )

async def set_health(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the command includes the health value
    if context.args and context.args[0].isdigit():
        new_health = int(context.args[0])
        # Ensure the health value is within the acceptable range
        new_health = max(0, min(100, new_health))
        
        # Update the character's health. Assuming `update_character_stat` is a function you have
        # that updates a character's attributes based on unique_id.
        # Uncomment and adjust the following line according to your actual update function:
        update_character_stat(user_id, {"$set": {"health": new_health}})
        
        await context.bot.send_message(chat_id=chat_id, text=f"Health set to {new_health}.")
        await show_profile(update, context)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please specify a valid health value between 0 and 100.")

async def set_hunger(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the command includes the health value
    if context.args and context.args[0].isdigit():
        new_hunger = int(context.args[0])
        # Ensure the health value is within the acceptable range
        # new_hunger = max(0, min(100, new_hunger))
        
        # Update the character's health. Assuming `update_character_stat` is a function you have
        # that updates a character's attributes based on unique_id.
        # Uncomment and adjust the following line according to your actual update function:
        update_character_stat(user_id, {"$set": {"hunger": new_hunger}})
        
        await context.bot.send_message(chat_id=chat_id, text=f"Hunger set to {new_hunger}.")
        await show_profile(update, context)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please specify a valid health value between 0 and 100.")


async def set_mood(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the command includes the health value
    if context.args and context.args[0].isdigit():
        new_mood = int(context.args[0])
        # Ensure the health value is within the acceptable range
        # new_health = max(0, min(100, new_health))
        
        # Update the character's health. Assuming `update_character_stat` is a function you have
        # that updates a character's attributes based on unique_id.
        # Uncomment and adjust the following line according to your actual update function:
        update_character_stat(user_id, {"$set": {"mood": new_mood}})
        
        await context.bot.send_message(chat_id=chat_id, text=f"Mood set to {new_mood}.")
        await show_profile(update, context)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please specify a valid health value between 0 and 100.")

async def set_exp(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the command includes the exp value
    if context.args and context.args[0].isdigit():
        new_exp = int(context.args[0])
        # Ensure the exp value is positive
        new_exp = max(0, new_exp)
        
        # Update the character's exp. Assuming `update_character_stat` is a function you have
        # that updates a character's attributes based on unique_id.
        # The following line is adjusted to fit with your actual update function:
        update_character_stat(user_id, {"$set": {"exp": new_exp}})
        
        await context.bot.send_message(chat_id=chat_id, text=f"Experience set to {new_exp}.")
        await show_profile(update, context)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please specify a valid experience value.")

async def set_money(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the command includes the money value
    if context.args and context.args[0].isdigit():
        new_money = int(context.args[0])
        # Ensure the money value is non-negative
        new_money = max(0, new_money)

        # Update the character's money
        update_character_stat(user_id, {"$set": {"money": new_money}})

        await context.bot.send_message(chat_id=chat_id, text=f"Money set to {new_money}.")
        await show_profile(update, context)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Please specify a valid money value.")


async def end_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    character = get_character(user_id)

    # Check if the character is currently engaged in a job
    if "current_job_id" in character and "job_start_time" in character:
        job_id = character["current_job_id"]
        job = next((job for job in jobs if job["id"] == job_id), None)
        
        if job:
            # End the job prematurely and update character stats
            earnings = job["earnings"]
            update_character_stat(user_id, {
                "$unset": {"current_job_id": "", "job_start_time": ""},
                "$inc": {"money": earnings},
            })
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Работа была преждевременно завершена. Деньги зачислены на ваш счет.")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка: работа не найдена.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Сейчас вы не на работе.")

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Retrieve the character information
    character = get_character(user_id)

    # Check if the character has a 'last_game_played' field indicating an ongoing game session
    if 'last_game_played' in character:
        # Remove or reset the 'last_game_played' field to end the game session
        update_character_stat(user_id, {"$unset": {"last_game_played": ""}})

        await context.bot.send_message(chat_id=chat_id, text="Игровая сессия была успешно завершена. Можете начать новую игру.")
    else:
        await context.bot.send_message(chat_id=chat_id, text="На данный момент игровая сессия не обнаружена.")

async def end_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    character = get_character(user_id)

    # Check if the character is currently engaged in an activity
    if "last_activity_time" in character:
        # End the activity prematurely and reset necessary fields
        update_character_stat(user_id, {"$unset": {"last_activity_time": ""}})

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Активность была преждевременно завершена.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="На данный момент активность не обнаружена.")
