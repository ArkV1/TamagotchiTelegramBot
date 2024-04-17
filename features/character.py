import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.db import get_character, create_character
from features.actions import show_activities_options, show_home_options
from features.jobs import show_jobs
from features.store import show_store_options
from features.common import calculate_level_from_exp
from data.characters import troyan_list

def choose_random_troyan(troyan_list):
    return random.choice(troyan_list)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    buttons = [
    [InlineKeyboardButton("Дом", callback_data=f"profile_action:home:{user_id}"), 
    InlineKeyboardButton("Магазины", callback_data=f"profile_action:store:{user_id}")],
    [InlineKeyboardButton("Работа", callback_data=f"profile_action:work:{user_id}"), 
    InlineKeyboardButton("Активности", callback_data=f"profile_action:activities:{user_id}")],
    [InlineKeyboardButton("Обновить", callback_data=f"profile_action:refresh:{user_id}"),
    InlineKeyboardButton("Закрыть", callback_data=f"profile_action:delete:{user_id}")]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    character = get_character(user_id)  # Adjust get_pet to fetch data using unique_pet_id
    
    # Function to determine health status
    def determine_health_status(health):
        if health == 0:
            return 'Нуждаюсь в реанимации'
        elif health > 0 and health <= 20:
            return 'Умираю'
        elif health > 20 and health <= 40:
            return 'Хуевит чета'
        elif health > 40 and health <= 60:
            return "Ну такое"
        elif health > 60 and health <= 80:
            return 'Живой'
        elif health > 80 and health <= 100:
            return 'Пиздато все'

    if character:
        # Assuming 'name' refers to the troyan's name and you have a matching troyan in your list
        troyan_name = character.get('name')
        # Find the troyan's image file name from the troyan_list
        troyan_file_name = next((troyan['file_name'] for troyan in troyan_list if troyan['name'] == troyan_name), None)
        image_path = f'./assets/images/characters/{troyan_file_name}'
        exp = character.get('exp')
        level = calculate_level_from_exp(exp)
        health = character.get('health')
        health_status = determine_health_status(health)
        status_message = (f"🕵️‍♂️Имя: {troyan_name}\n"
                          f"⭐Уровень: {level} ({exp})\n"
                          f"🍔Сытость: {character.get('hunger', 100)}\n"
                          f"❤Состояние: {health_status} ({health}) \n"
                          f"💰Шекели: {character.get('money', 0)}\n"
                          f"🤡Настроение: {character.get('mood', 'Happy')}")
        # Send the photo with the profile text as caption
        if troyan_file_name:
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=status_message, reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=chat_id, text="No image found for this troyan.", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text='У вас нет трояна. Создайте его с помощью команды "Заспаунить трояна"!')


async def action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Extract the action type, specific action, and user_id from the callback query
    action_type, specific_action, action_user_id = query.data.split(':')
    action_user_id = int(action_user_id)  # Convert to int for comparison
    
    # Verify action type to ensure it's a profile action
    if action_type != "profile_action":
        await query.edit_message_text(text="Неизвестное действие.")
        return

    # ID of the user who pressed the button
    pressing_user_id = query.from_user.id

    # Check if the user who clicked the button is the intended user
    # if query.from_user.id != action_user_id:
    #     user_mention = query.from_user.mention_html()
    #     message_text = f"{user_mention}, вы не можете выполнить это действие."
    #     await context.bot.send_message(chat_id=query.message.chat_id, text=message_text, parse_mode='HTML')
    #     return

    # Handle the specific action
    if specific_action == "home":
        await show_home_options(update, context)
    elif specific_action == "activities":
        await show_activities_options(update, context)
    elif specific_action == "work":
        await show_jobs(update, context)
    elif specific_action == "jobs":
        await show_jobs(update, context, True)
    elif specific_action == "store":
        await show_store_options(update, context)  # This function needs to be implemented to show store options
    elif specific_action == "stores":
        await show_store_options(update, context, True) 
    elif specific_action == "refresh":
        if query.from_user.id != action_user_id:
            user_mention = query.from_user.mention_html()
            message_text = f"{user_mention}, вы не можете выполнить это действие."
            await context.bot.send_message(chat_id=query.message.chat_id, text=message_text, parse_mode='HTML')
            return
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        await show_profile(update, context)
    elif specific_action == "delete":
        if query.from_user.id != action_user_id:
            user_mention = query.from_user.mention_html()
            message_text = f"{user_mention}, вы не можете выполнить это действие."
            await context.bot.send_message(chat_id=query.message.chat_id, text=message_text, parse_mode='HTML')
            return
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Неизвестное действие.")


async def handle_create_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if the character already exists
    character = get_character(user_id)
    if character:
        # Character exists, ask for confirmation
        buttons = [[
        InlineKeyboardButton(text="🗑️Выкинуть трояна", callback_data=f'confirm_create:{user_id}'),
        InlineKeyboardButton(text="⛔️Отмена", callback_data=f'cancel_create:{user_id}')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("У вас уже есть троян, выкинуть его?", reply_markup=reply_markup)
    else:
        selected_troyan = random.choice(troyan_list)
        # No character exists, proceed to create
        create_character(user_id, selected_troyan['name'])
        await update.message.reply_text("Троян создан!")
        await show_profile(update, context)

async def handle_character_creation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Parse the callback data to extract action and user ID
    action, action_user_id = query.data.split(':')
    action_user_id = action_user_id  # Convert to int for comparison

    # ID of the user who clicked the button
    callback_user_id = query.from_user.id

    # Verify if the action user ID matches the callback user ID
    if callback_user_id != int(action_user_id):
        if query.from_user.username:
            mention = f"@{query.from_user.username}"
        else:
            # Use HTML to mention the user by ID if they don't have a username
            mention = f'<a href="tg://user?id={callback_user_id}">пользователь</a>'
        
        # Send a message directly to the chat, mentioning the user
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Извините, {mention}, вы не можете управлять этими кнопками. Они предназначены для другого пользователя.",
                                       parse_mode='HTML')  # Ensure to use HTML parse mode for mentions without username
        return  # Return early to avoid processing the button action

    # Proceed based on the action
    if action == 'confirm_create':
        selected_troyan = random.choice(troyan_list)
        create_character(int(action_user_id), selected_troyan['name'])
        # Optionally, edit the original message or send a new one to indicate the action has been taken
        await query.edit_message_text(text="Троян пересоздан!")
        await show_profile(update, context)  # Assuming this shows the profile to the user
    elif action == 'cancel_create':
        # Optionally, edit the original message or send a new one to indicate the action has been cancelled
        await query.edit_message_text(text="Создание нового трояна отменено.")

