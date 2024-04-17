from datetime import datetime, timedelta
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.db import get_character, update_character_stat

from features.games import show_games
from features.common import calculate_time_left
from data.activities import home_actions, activities

async def show_home_options(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    buttons = [
        [InlineKeyboardButton("Подробная инфа", callback_data=f"home_action:details:{user_id}")]
    ]
    buttons.extend([
        [InlineKeyboardButton(action['name'], callback_data=f"home_action:{action['id']}:{user_id}")]
        for action in home_actions
    ])
    buttons.append([InlineKeyboardButton("Закрыть", callback_data=f"profile_action:delete:{user_id}")])
    reply_markup = InlineKeyboardMarkup(buttons)

    if edit:
        await query.edit_message_text(text="Домашние занятия:", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Домашние занятия:", reply_markup=reply_markup)

async def show_home_action_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    # Start constructing the message
    details_message = "Подробная информация по домашним занятиям:\n\n"

    # Append details for each home action including effects on stats
    for action in home_actions:
        cooldown_hours = action['cooldown'].seconds // 3600  # Calculate cooldown in hours
        details_message += f"{action['name']}: {action['description']}\n"

        # Conditionally add hunger and mood effects if they are not None
        if action['hunger'] is not None and action['mood'] is not None:
            details_message += "- Статы: "
            if action['hunger'] is not None:
                hunger_effect = f"Голод: {'+' if action['hunger'] > 0 else ''}{action['hunger']}"
                details_message += f"{hunger_effect}"
            if action['mood'] is not None:
                if action['hunger'] is not None:
                    details_message += ", "
                mood_effect = f"Настроение: {'+' if action['mood'] > 0 else ''}{action['mood']}"
                details_message += f"{mood_effect}"
            details_message += "\n"

        # Additional details specific to actions like 'sleep'
        if action['id'] == 'sleep':
            additional_info = "Восстанавливает настроение до нейтрального, если оно было ниже нуля."
            details_message += f"Дополнительно: {additional_info}\n"
        
        details_message += f"- Перезарядка: {cooldown_hours} часов\n\n"

    # Define the button for going back
    buttons = [[InlineKeyboardButton("Назад", callback_data=f"home_action:back:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Update or send the message with the detailed home actions
    await query.edit_message_text(text=details_message.strip(), reply_markup=reply_markup)

async def home_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, action_id, user_id_str = query.data.split(':')
    user_id = int(user_id_str)

    buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    if user_id != query.from_user.id:
        user_mention = query.from_user.mention_html()
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"{user_mention}, вы не можете выполнить это действие.", 
                                       parse_mode='HTML', reply_markup=reply_markup)
        return

    if action_id == "details":
        # Call the function to show detailed information about home actions
        await show_home_action_details(update, context)
        return
    
    if action_id == "back":
        await show_home_options(update, context, True)
        return

    # Specific actions for gaming platforms
    if action_id in ["gaming_pc", "gaming_console"]:
        platform = "pc" if action_id == "gaming_pc" else "console"
        await show_games(update, context, platform)
        return

    character = get_character(user_id)
    current_time = datetime.now()

    action = next((act for act in home_actions if act['id'] == action_id), None)
    if not action:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Данное домашнее действие не найдено.", reply_markup=reply_markup)
        return

    last_action_time = character.get(f"last_{action_id}", datetime.min)
    cooldown_end_time = last_action_time + action['cooldown']
    time_left_str = calculate_time_left(cooldown_end_time)

    if current_time < cooldown_end_time:
        # Custom cooldown messages for specific actions
        if action_id == "sleep":
            cooldown_message = f"Вы недавно уже спали, опять поспать можно будет через: {time_left_str}."
        elif action_id == "eat_free":
            cooldown_message = f"Вы недавно уже ели, опять похавать можно будет через: {time_left_str}."
        else:
            cooldown_message = f"Это действие находится на перезарядке. {time_left_str}."
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=cooldown_message,
                                       parse_mode='HTML', reply_markup=reply_markup)
        return

    update_fields = {"$set": {f"last_{action_id}": current_time}}

    if action_id == "sleep":
        if character.get('mood', 0) < 0:
            update_fields["$set"]["mood"] = 0
            response_text = "Вы хорошо выспались и ваше настроение стало нейтральным."
        else:
            update_fields["$inc"] = {"mood": 15}
            response_text = "Вы хорошо выспались и чувствуете себя отдохнувшим."
        update_fields["$inc"] = {"hunger": action['hunger'], "exp": 5}
    elif action_id == "eat_free":
        update_fields["$inc"] = {"hunger": action['hunger'], "mood": action['mood'], "exp": 5}  # Assuming exp increase for action
        response_text = "Вы бесплатно поели дома. Сытость увеличена."
    else:
        update_fields["$inc"] = {
            "hunger": action['hunger'],
            "mood": action['mood'],
            "exp": 5  # Assuming exp increase for all actions, adjust if necessary
        }
        response_text = f"Вы успешно выполнили действие '{action['name']}'."

    update_character_stat(user_id, update_fields)
    await context.bot.send_message(chat_id=query.message.chat_id, text=response_text, parse_mode='HTML', reply_markup=reply_markup)

# async def home_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     _, action, user_id_str = query.data.split(':')
#     user_id = int(user_id_str)

#     buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
#     reply_markup = InlineKeyboardMarkup(buttons)

#     if user_id != query.from_user.id:
#         user_mention = query.from_user.mention_html()
#         await context.bot.send_message(chat_id=query.message.chat_id, 
#                                        text=f"{user_mention}, вы не можете выполнить это действие.", 
#                                        parse_mode='HTML', reply_markup=reply_markup)
#         return

#     character = get_character(user_id)
#     current_time = datetime.now()

#     if action == "details":
#         await show_home_action_details(update, context)
#         return

#     if action == "gaming_pc" or action == "gaming_console":
#         platform = "pc" if action == "gaming_pc" else "console"
#         await show_games(update, context, platform)
#         return

#     cooldowns = {
#         "eat_free": timedelta(hours=4),
#         "sleep": timedelta(hours=8),
#     }

#     last_action_time = character.get(f"last_{action}", datetime.min)
#     cooldown_end_time = last_action_time + cooldowns[action]
#     time_left_str = calculate_time_left(cooldown_end_time)

#     if current_time < cooldown_end_time:
#         await context.bot.send_message(chat_id=query.message.chat_id, 
#                                        text=f"Это действие находится на перезарядке. {time_left_str}.",
#                                        parse_mode='HTML', reply_markup=reply_markup)
#         return

#     update_fields = {"$set": {}}
#     update_fields["$set"][f"last_{action}"] = current_time
#     if action == "eat_free":
#         update_fields["$inc"] = {"hunger": 20, "exp": 5}
#         response_text = "Вы бесплатно поели дома. Сытость увеличена."
#     elif action == "sleep":
#         if character.get('mood', 0) < 0:
#             update_fields["$set"]["mood"] = 0
#             response_text = "Вы хорошо выспались и ваше настроение стало нейтральным."
#         else:
#             update_fields["$inc"] = {"hunger": -10, "mood": 15, "exp": 5}
#             response_text = "Вы хорошо выспались и чувствуете себя отдохнувшим."
#     update_character_stat(user_id, update_fields)

#     await context.bot.send_message(chat_id=query.message.chat_id, text=response_text, parse_mode='HTML', reply_markup=reply_markup)

async def show_activities_options(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id


    buttons = [[InlineKeyboardButton("Подробная инфа", callback_data=f"activities_action:details:{user_id}")]]
    buttons.extend([
        [InlineKeyboardButton(f"{activity['name']} - {activity['price']}₪", callback_data=f"activities_action:{activity['id']}:{user_id}")]
        for activity in activities
    ])
    buttons.append([InlineKeyboardButton("Закрыть", callback_data=f"profile_action:delete:{user_id}")])
    reply_markup = InlineKeyboardMarkup(buttons)

    if edit:
        await query.edit_message_text(text="Выберите активность:", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Выберите активность:", reply_markup=reply_markup)

async def show_activity_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    detailed_activities_msg = "Подробная информация о активностях:\n\n"
    for activity in activities:
        detailed_activities_msg += (
            f"{activity['name']}:\n"
            f"- Требования: Цена: {activity['price']}₪, cытость: -{activity['hunger']}\n"
            f"- Настроение: +{activity.get('mood', 'N/A')}\n"
        )
        if 'chance_of_bad_trip' in activity:
            detailed_activities_msg += (
                f"Шанс на бед трип: {activity['chance_of_bad_trip']}%\n(Настроение при бед трипе: {activity['bad_trip_mood']})\n"
            )
        detailed_activities_msg += "\n"

    buttons = [[InlineKeyboardButton("Назад", callback_data=f"activities_action:back:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(text=detailed_activities_msg, reply_markup=reply_markup)


######################################################################################################################

async def activities_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, activity_id, user_id_str = query.data.split(':')
    user_id = int(user_id_str)

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]])

    if query.from_user.id != user_id:
        user_mention = query.from_user.mention_html()
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"{user_mention}, вы не можете выполнить это действие.", 
                                       parse_mode='HTML', reply_markup=reply_markup)
        return

    if activity_id == "back":
        await show_activities_options(update, context, True)
        return

    if activity_id == "details":
        await show_activity_details(update, context)
        return

    character = get_character(user_id)
    activity = next((act for act in activities if act['id'] == activity_id), None)
    if not activity:
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text="Активность не найдена.", 
                                       reply_markup=reply_markup)
        return

    now = datetime.now()
    if 'last_activity_time' in character and now < character['last_activity_time'] + timedelta(hours=2):
        time_left_str = calculate_time_left(character['last_activity_time'] + timedelta(hours=2))
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"Вы недавно выполнили другую активность. Подождите еще {time_left_str}.", 
                                       reply_markup=reply_markup)
        return

    if character.get('money', 0) < activity['price']:
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"У вас не хватает денег. Требуется: {activity['price']}₪.",
                                       reply_markup=reply_markup)
        return

    if character.get('hunger', 100) < activity['hunger']:
        hunger_response = {
            "walk_girl": "Перед прогулкой с тян стоило бы поесть.",
            "walk_boys": "Перед прогулкой с друзьями стоило бы поесть.",
            "smoke": "Перед курением стоило бы поесть.",
            "rave": "Перед рейвом стоило бы поесть."
        }
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=hunger_response[activity_id],
                                       reply_markup=reply_markup)
        return

    update_fields = {
        "$inc": {
            "money": -activity['price'],
            "hunger": -activity['hunger'],
            "exp": 5
        },
        "$set": {
            "last_activity_time": now
        }
    }

    if activity_id == "smoke" and random.randint(1, 100) <= activity.get('chance_of_bad_trip', 0):
        update_fields["$inc"]["mood"] = activity['bad_trip_mood']
        response_text = "Вы словили бет трип. Настроение ухудшилось."
    else:
        update_fields["$inc"]["mood"] = activity['mood']
        response_texts = {
            "smoke": "Вы пиздато дунули. Настроение улучшилось.",
            "rave": "Рейв был пиздатым. Настроение значительно улучшилось.",
            "walk_girl": "Прогулка была приятной. Настроение улучшилось.",
            "walk_boys": "Вы хорошо провели время с друзьями. Настроение улучшилось."
        }
        response_text = response_texts[activity_id]

    update_character_stat(user_id, update_fields)
    await context.bot.send_message(chat_id=query.message.chat_id, text=response_text, reply_markup=reply_markup)
