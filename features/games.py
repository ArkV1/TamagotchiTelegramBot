from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.db import get_character, update_character_stat

from features.common import calculate_time_left
from data.games import pc_games, playstation_games


async def show_games(update: Update, context: ContextTypes.DEFAULT_TYPE, platform, edit=False):
    query = update.callback_query
    await query.answer()

    if(platform == "pc"):
        games = pc_games
        text = "Выберите игру на ПК:"
    elif(platform == "console"):
        games = playstation_games
        text = "Выберите игру на Playstation:"

    user_id = query.from_user.id
    games = pc_games if platform == "pc" else playstation_games

    buttons = [
        [InlineKeyboardButton("Подробная инфа", callback_data=f"game_action:{platform}:details:{user_id}")]
    ]
    buttons.extend([
        [InlineKeyboardButton(game["name"], callback_data=f"game_action:{platform}:{game['id']}:{user_id}")]
        for game in games
    ])
    buttons.append([InlineKeyboardButton("Назад", callback_data=f"game_action:{platform}:back:{user_id}")])
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_game_details(update: Update, context: ContextTypes.DEFAULT_TYPE, platform):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    games = pc_games if platform == "pc" else playstation_games
    details_message = f"Детали игр на {'ПК' if platform == 'pc' else 'PlayStation'}:\n\n"

    for game in games:
        details_message += f"{game['name']}:\n"
        stats = []
        if 'mood_effect' in game:
            if callable(game['mood_effect']):
                # Explaining the range for random mood effects
                if 'mood_range' in game:
                    min_mood, max_mood = game['mood_range']
                    stats.append(f"Настроение: от {min_mood} до {max_mood}")
                else:
                    # Default message if range is not specified
                    stats.append("Настроение: изменяется случайно")
            else:
                mood_effect = game['mood_effect']
                stats.append(f"Настроение: {'+' if mood_effect >= 0 else ''}{mood_effect}")
        if 'hunger_effect' in game:
            stats.append(f"Сытость: {'+' if game['hunger_effect'] >= 0 else ''}{game['hunger_effect']}")
        if stats:
            details_message += f"- Статы: {', '.join(stats)}\n"
        if 'options' in game:
            details_message += "Опции:\n"
            for option in game['options']:
                details_message += f"  - {option['name']}\n"
                option_stats = []
                if 'mood_effect' in option:
                    if callable(option['mood_effect']):
                        # Range display for option mood effects
                        if 'mood_range' in option:
                            min_mood, max_mood = option['mood_range']
                            option_stats.append(f"Настроение: от {min_mood} до {max_mood}")
                        else:
                            option_stats.append("Настроение: изменяется случайно")
                    else:
                        mood_effect = option['mood_effect']
                        option_stats.append(f"Настроение: {'+' if mood_effect >= 0 else ''}{mood_effect}")
                if 'hunger_effect' in option:
                    option_stats.append(f"Сытость: {'+' if option['hunger_effect'] >= 0 else ''}{option['hunger_effect']}")
                if option_stats:
                    details_message += f"    - Статы: {', '.join(option_stats)}\n"
        details_message += "\n"

    # Add a note about gameplay availability
    details_message += "Играть можно один раз каждые 2 часа.\n"

    buttons = [[InlineKeyboardButton("Назад", callback_data=f"game_action:{platform}:back:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text(text=details_message, reply_markup=reply_markup)



async def game_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from features.actions import show_home_options  # Assuming this is where show_home_options is defined

    query = update.callback_query
    await query.answer()

    # Extracting the game action data
    _, platform, action_detail, user_id_str = query.data.split(':')
    user_id = int(user_id_str)

    buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Authorization check
    if user_id != query.from_user.id:
        user_mention = query.from_user.mention_html()
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"{user_mention}, вы не можете выполнить это действие.", 
                                       parse_mode='HTML', reply_markup=reply_markup)
        return

    if action_detail == "show_games":
        await show_games(update, context, platform, True)
        return
    
    if action_detail == "details":
        await show_game_details(update, context, platform)
        return

    if action_detail == "back":
        await show_home_options(update, context, True)
        return

    character = get_character(user_id)

    now = datetime.now()
    last_game_played = character.get('last_game_played', datetime.min)
    cooldown_period = timedelta(hours=2)
    cooldown_end_time = last_game_played + cooldown_period

    if now < cooldown_end_time:
        time_left_str = calculate_time_left(cooldown_end_time)
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                       text=f"Вы недавно уже играли и устали. Подождите еще {time_left_str}.",
                                       parse_mode='HTML', reply_markup=reply_markup)
        return

    games = pc_games if platform == "pc" else playstation_games
    game_or_option_id = action_detail

    # Determine if this is a game selection or option selection
    game = next((g for g in games if g['id'] == game_or_option_id), None)

    if game:
        # Game without options logic
        if "options" not in game:
            mood_effect = game["mood_effect"]() if callable(game["mood_effect"]) else game["mood_effect"]
            update_character_stat(user_id, {"$set": {"last_game_played": now}, "$inc": {"mood": mood_effect}})
            await context.bot.send_message(chat_id=query.message.chat_id,
                                           text=f"Вы поиграли в {game['name']}. Изменение настроения: {mood_effect}.",
                                           parse_mode='HTML', reply_markup=reply_markup)
        else:
            # If the game has options, prepare to show them
            buttons = [
                [InlineKeyboardButton(option["name"], callback_data=f"game_action:{platform}:{option['id']}:{user_id}")]
                for option in game["options"]
            ]
            buttons.append([InlineKeyboardButton("Назад", callback_data=f"game_action:{platform}:show_games:{user_id}")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(text="Выберите опцию:", reply_markup=reply_markup)
    else:
        # Option selection logic
        for game in games:
            option = next((opt for opt in game.get('options', []) if opt['id'] == game_or_option_id), None)
            if option:
                mood_effect = option["mood_effect"]() if callable(option["mood_effect"]) else option["mood_effect"]
                update_character_stat(user_id, {"$set": {"last_game_played": now}, "$inc": {"mood": mood_effect}})
                await context.bot.send_message(chat_id=query.message.chat_id,
                                               text=f"Вы выбрали опцию '{option['name']}' в игре '{game['name']}'. Изменение настроения: {mood_effect}.",
                                               parse_mode='HTML', reply_markup=reply_markup)
                break
