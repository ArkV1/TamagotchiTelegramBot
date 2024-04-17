from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from db.db import get_character, update_character_stat
from data.store_items import food_store, mood_store, darknet_store



async def show_store_options(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Place "Еда" and "Настроение" buttons on the same row
    buttons = [
        [
            InlineKeyboardButton("Супермаркет", callback_data=f"store_action:food:{user_id}"),
            InlineKeyboardButton("Алкоголь", callback_data=f"store_action:mood:{user_id}")
        ],
        [
            InlineKeyboardButton("Darknet", callback_data=f"store_action:darknet:{user_id}")
        ]
    ]
    buttons.append([InlineKeyboardButton("Закрыть", callback_data=f"profile_action:delete:{user_id}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)

    if edit:
        await query.edit_message_text(text="Выберите какой магазин посетить:", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Выберите какой магазин посетить:", reply_markup=reply_markup)



async def store_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Extract the action scope, specific action, and user_id from the callback query
    _, specific_action, action_user_id = query.data.split(':')
    action_user_id = int(action_user_id)  # Convert to int for comparison
    
    # ID of the user who pressed the button
    pressing_user_id = query.from_user.id

    # Check if the user who clicked the button is the intended user
    if pressing_user_id != action_user_id:
        user_mention = query.from_user.mention_html()
        message_text = f"{user_mention}, вы не можете выполнить это действие."
        await context.bot.send_message(chat_id=query.message.chat_id, text=message_text, parse_mode='HTML')
        return

    # Proceed with the specific store action after security checks
    if specific_action == "food":
        await show_food_items(update, context)  
    elif specific_action == "food_details":
        await show_food_details(update, context)
    elif specific_action == "mood":
        await show_mood_items(update, context) 
    elif specific_action == "mood_details":
        await show_mood_details(update, context)
    elif specific_action == "darknet":
        await show_darknet_items(update, context)
    elif specific_action == "darknet_details":
        await show_darknet_details(update, context)
    else:
        await query.edit_message_text(text="Неизвестное действие в магазине.")

async def show_food_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Initialize the buttons list with the "Подробная инфа" button at the top
    buttons = [[InlineKeyboardButton("Подробная инфа", callback_data=f"store_action:food_details:{user_id}")]]
    # Add food items to the list
    buttons.extend([[InlineKeyboardButton(f"{item['name']} - {item['price']}₪", callback_data=f"buy_item:food:{item['name']}:{user_id}")]
                    for item in food_store])
    # Finally, add the "Назад" button at the bottom
    buttons.append([InlineKeyboardButton("Назад", callback_data=f"profile_action:stores:{user_id}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(text="Выберите еду для покупки:", reply_markup=reply_markup)

async def show_food_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    # Build detailed food stats message
    message_text = "Подробная информация о еде:\n"
    for item in food_store:
        message_text += f"{item['name']}: Цена - {item['price']}₪\nСытость - {item['hunger']}, Настроение - {item['mood']}\n"
    
    # Back button to return to the food selection
    buttons = [[InlineKeyboardButton("Назад", callback_data=f"store_action:food:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(text=message_text, reply_markup=reply_markup)

async def show_mood_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    buttons = [[InlineKeyboardButton("Подробная инфа", callback_data=f"store_action:mood_details:{user_id}")]]
    buttons.extend([[InlineKeyboardButton(item["name"] + f" - {item['price']}₪", callback_data=f"buy_mood:{item['name']}:{user_id}")] for item in mood_store])
    buttons.append([InlineKeyboardButton("Назад", callback_data=f"profile_action:stores:{user_id}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(text="Выберите алкоголь для покупки:", reply_markup=reply_markup)


async def show_mood_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    message_text = "Подробная информация об алкоголе:\n"
    for item in mood_store:
        message_text += f"{item['name']}: Цена - {item['price']}₪\nНастроение - {item['mood']}\n"
    
    buttons = [[InlineKeyboardButton("Назад", callback_data=f"store_action:mood:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(text=message_text, reply_markup=reply_markup)

async def show_darknet_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    buttons = [[InlineKeyboardButton("Подробная инфа", callback_data=f"store_action:darknet_details:{user_id}")]]
    buttons.extend([[InlineKeyboardButton(item["name"] + f" - {item['price']}₪", callback_data=f"buy_darknet:{item['name']}:{user_id}")] for item in darknet_store])
    buttons.append([InlineKeyboardButton("Назад", callback_data=f"profile_action:stores:{user_id}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(text="Выберите товар из Darknet:", reply_markup=reply_markup)

async def show_darknet_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    message_text = "Подробная информация о товарах из Darknet:\n"
    for item in darknet_store:
        message_text += f"{item['name']}: Цена - {item['price']}₪\nНастроение - {item['mood']}\n"
    
    buttons = [[InlineKeyboardButton("Назад", callback_data=f"store_action:darknet:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await query.edit_message_text(text=message_text, reply_markup=reply_markup)


async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item_category: str, item_name: str, user_id: int):
    query = update.callback_query
    # Fetch the character and item details
    character = get_character(user_id)
    if item_category == 'food':
        item = next((item for item in food_store if item['name'] == item_name), None)
    elif item_category == 'mood':
        item = next((item for item in mood_store if item['name'] == item_name), None)
    elif item_category == 'darknet':
        item = next((item for item in darknet_store if item['name'] == item_name), None)
    # Add logic for other categories as needed

    user_mention = query.from_user.mention_html()

    buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    if not character or not item:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{user_mention}, произошла ошибка при покупке.", parse_mode='HTML', reply_markup=reply_markup)
        return

    # Check if the character has enough money
    if character['money'] < item['price']:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{user_mention}, недостаточно средств для покупки.", parse_mode='HTML', reply_markup=reply_markup)
        return

    # Calculate incremental changes
    money_change = -item['price']
    hunger_change = item.get('hunger', 0)
    mood_change = item.get('mood', 0)

    # Prepare update operations
    update_operations = {
        "$inc": {
            "money": money_change,
            "hunger": min(character.get('hunger', 0) + hunger_change, 100) - character.get('hunger', 0),  # Ensure hunger does not exceed 100
            "mood": min(character.get('mood', 0) + mood_change, 100) - character.get('mood', 0)  # Ensure mood does not exceed 100
        }
    }

    # Update character stats in the database
    update_character_stat(user_id, update_operations)

    buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Notify the user of the successful purchase with a new message
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Покупка успешна:\n{item['name']} за {item['price']}₪.", reply_markup=reply_markup)

async def buy_item_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, category, item_name, action_user_id = query.data.split(':')
    user_id = int(action_user_id)

    # Getting the mention for the user who attempted the action
    user_mention = query.from_user.mention_html()

    if query.from_user.id != user_id:
        # Now including the user mention in the message
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"{user_mention}, вы не можете выполнить это действие.", 
                                       parse_mode='HTML')
        return

    # Proceed with the buy_item function if the user is authorized
    await buy_item(update, context, category, item_name, user_id)
