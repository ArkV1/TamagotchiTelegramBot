from datetime import datetime, timedelta
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext, JobQueue
from data.jobs import jobs
from db.db import get_character, update_character_stat

from features.common import calculate_level_from_exp, calculate_time_left

async def show_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    query = update.callback_query
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    character = get_character(user_id)

    if not character:
        await context.bot.send_message(chat_id=chat_id, text="У вас нет Трояна. Пожалуйста, заспаунте Трояна.")
        return
     
    # If not busy, proceed to show eligible jobs
    current_level = calculate_level_from_exp(character.get('exp', 0))
    eligible_jobs = [job for job in jobs if job["level_required"] <= current_level]

    # Prepend the "Details" button at the top of the buttons list
    buttons = [[InlineKeyboardButton("Подробная инфа", callback_data=f"jobs_action:all_jobs_details:{user_id}")]]
    # Append other job buttons below
    buttons += [[InlineKeyboardButton(job["name"], callback_data=f"job:{job['id']}:{user_id}")] for job in eligible_jobs]
    buttons.append([InlineKeyboardButton("Закрыть", callback_data=f"profile_action:delete:{user_id}")])

    reply_markup = InlineKeyboardMarkup(buttons)

    if edit:
        await query.edit_message_text(text="Выберите работу:", reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Выберите работу:", reply_markup=reply_markup)

async def show_all_job_details(update: Update, context: ContextTypes.DEFAULT_TYPE, jobs):
    user_id = update.effective_user.id

    detailed_jobs_msg = "Подробная информация о работах:\n\n"
    for job in jobs:  # Loop through all available jobs
        detailed_jobs_msg += (f"{job['name']} - "
                      f"{job['description']}\n"
                      f"- Требования: Уровень {job['level_required']}, "
                      f"настроение: -{job['mood_cost']}, сытость: -{job['hunger_cost']}\n"
                      f"- Заработок: {job['earnings']}₪, "
                      f"продолжительность: {job['durationInMinutes']} минут\n\n")

    buttons = [[InlineKeyboardButton("Назад", callback_data=f"profile_action:jobs:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    query = update.callback_query
    if len(detailed_jobs_msg) > 4096:
        detailed_jobs_msg = detailed_jobs_msg[:4093] + "..."
    await query.edit_message_text(text=detailed_jobs_msg, reply_markup=reply_markup)

async def job_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Splitting the callback data to identify the action and extracting parameters
    data_parts = query.data.split(':')
    action = data_parts[0]
    user_id = int(data_parts[2])

    
    # Early user ID verification for actions that require it
    if action in ["job", "job_details"]:
        job_id = int(data_parts[1])
        
        # Verify if the action's user_id matches the query's user_id
        if user_id != query.from_user.id:
            # Notify unauthorized user without editing the original message
            unauthorized_user_mention = query.from_user.mention_html()
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"{unauthorized_user_mention}, вы не можете выполнить это действие.", parse_mode='HTML')
            return  # Stop processing since the user is not authorized

    character = get_character(user_id)
    buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Handle authorized actions
    if action == "jobs_action" and data_parts[1] == "all_jobs_details":
        await show_all_job_details(update, context, jobs)
    elif action == "job":
        # Replicate logic for accepting a job, assuming the existence of `assign_job_to_character`
        success, assigned_job = await assign_job_to_character(query.message.chat_id, user_id, job_id, context)
        if success:
            job_end_time = datetime.now() + timedelta(minutes=assigned_job['durationInMinutes'])
            time_left_str = calculate_time_left(job_end_time)
            confirmation_text = f"Вы устроились на работу '{assigned_job['name']}'. Эта работа длится {time_left_str}."
            img_file_names = assigned_job.get("file_names", [])
            if img_file_names:  # If there's an image to send
                img_file_name = random.choice(img_file_names)  # Choose a random image if available
                image_path = f'./assets/images/jobs/{img_file_name}' if img_file_name else None
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(chat_id=query.message.chat_id, photo=photo, caption=confirmation_text, reply_markup=reply_markup)
            else:
                # If no image, just send the confirmation text
                await context.bot.send_message(chat_id=query.message.chat_id, text=confirmation_text, reply_markup=reply_markup)
        # else:
        #     await context.bot.send_message(chat_id=query.message.chat_id, text="Не получилось устроиться на работу.", reply_markup=reply_markup)
    else:
        # Handle unexpected action
        await query.edit_message_text(text="Неизвестное действие.")

async def job_completion_callback(context: CallbackContext):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    user_id = job_data["user_id"]
    earnings = job_data["earnings"]

    # Assuming you have a way to retrieve the user's Telegram username or mention by their ID
    user = await context.bot.get_chat(user_id)
    if user.username:
        mention = f"@{user.username}"
    else:
        # If no username, use the first name with HTML mention
        mention = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'

    # Complete the job and apply the payout
    update_character_stat(user_id, {"$unset": {"current_job_id": "", "job_start_time": ""}, "$inc": {"money": earnings, "exp": 10}})

    # Notify the user with their mention
    completion_message = (
        f"{mention}, Cмена закончилась.\n"
        f"Деньги зачислены на счет.\n\n"
        f"Троян заработал: {earnings}₪"
    )
    await context.bot.send_message(chat_id=chat_id, text=completion_message, parse_mode='HTML')

async def assign_job_to_character(chat_id: int, user_id: int, job_id: int, context: CallbackContext):
    buttons = [[InlineKeyboardButton("Понял, принял", callback_data=f"profile_action:delete:{user_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    character = get_character(user_id)

    job = next((job for job in jobs if job["id"] == job_id), None)
    if job is None:
        print("Такой работы не существует...", reply_markup=reply_markup)
        return False, None
    
    if is_job_in_progress(character):
        currentJob = next((job for job in jobs if job["id"] == character["current_job_id"]), None)
        if currentJob is None:
            print("Такой работы не существует...", reply_markup=reply_markup)
            return False, None
        # If the job's end time is in the future, inform the user accordingly with the time left
        job_start_time = character["job_start_time"]
        job_end_time = calculate_job_end_time(job_start_time, currentJob["durationInMinutes"])
        time_left_str = calculate_time_left(job_end_time)
        await context.bot.send_message(chat_id=chat_id, text=f"Ваш Троян уже на работе.\nДо конца смены: {time_left_str}.", reply_markup=reply_markup)
        return False, None

    # Check if the character has enough hunger to start the job
    if character.get('hunger', 0) < job["hunger_cost"] and character.get('mood', 0) < job["mood_cost"]:
        # Not enough hunger and mood to start the job
        await context.bot.send_message(chat_id=chat_id, text="Перед работой стоило бы поесть и отдохнуть.", reply_markup=reply_markup)
        return False, None
    if character.get('hunger', 0) < job["hunger_cost"]:
        # Not enough hunger to start the job
        await context.bot.send_message(chat_id=chat_id, text="Перед работой стоило бы поесть.", reply_markup=reply_markup)
        return False, None
    if character.get('mood', 0) < job["mood_cost"]:
        # Not enough hunger to start the job
        await context.bot.send_message(chat_id=chat_id, text="Перед работой стоило бы отдохнуть.", reply_markup=reply_markup)
        return False, None

    job_start_time = datetime.now()

    # Deduct hunger points for starting the job
    update_character_stat(user_id, {
        "$inc": {
            "hunger": -job["hunger_cost"],
            "mood": -job["mood_cost"]
        },
        "$set": {
            "current_job_id": job_id,
            "job_start_time": job_start_time,
        }
    })

    context.job_queue.run_once(
        job_completion_callback,
        job["durationInMinutes"] * 60,
        data={
            "chat_id": chat_id,
            "user_id": user_id,
            "job_id": job_id,
            "earnings": job["earnings"]
        }
    )

    return True, job


def calculate_job_end_time(job_start_time, duration_in_minutes):
    """Calculate and return job's end time based on start time and duration."""
    return job_start_time + timedelta(minutes=duration_in_minutes)

def is_job_in_progress(character):
    """Check if the character is currently busy with a job."""
    if "current_job_id" in character and "job_start_time" in character:
        current_job_id = character["current_job_id"]
        job_start_time = character["job_start_time"]
        # Find the job to get its duration
        job = next((job for job in jobs if job["id"] == current_job_id), None)
        if job:
            job_end_time = calculate_job_end_time(job_start_time, job["durationInMinutes"])
            return datetime.now() < job_end_time
    return False