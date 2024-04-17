from datetime import datetime

def calculate_level_from_exp(exp_points):
        # Experience requirements as defined for levels 2 to 10, and fixed afterwards.
        exp_requirements = [0, 25, 50, 100, 150, 250, 375, 500, 750, 1000]
        level = 1  # Start from level 1

        # Correcting the logic to avoid incrementing the level for 0 XP.
        for i, requirement in enumerate(exp_requirements[1:], start=2):  # Start enumeration at 2 for level 2
            if exp_points >= requirement:
                level = i
            else:
                break  # Stop if the experience points are less than the requirement for the next level.
        
        # For experience points above the highest defined threshold, calculate the level with fixed 1000 XP increments.
        if exp_points >= exp_requirements[-1]:
            additional_levels = (exp_points - exp_requirements[-1]) // 1000
            # Ensure level calculation starts correctly from the level corresponding to the last specific requirement.
            level = len(exp_requirements) + additional_levels
        
        return level

def calculate_time_left(job_end_time):
    current_time = datetime.now()
    if current_time < job_end_time:
        time_left = job_end_time - current_time
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_str_parts = []

        # Adding hours to the string if greater than 0
        if hours > 0:
            if hours % 10 == 1 and hours != 11:
                time_str_parts.append(f"{hours} час")
            elif 2 <= hours % 10 <= 4 and (hours < 10 or hours > 20):
                time_str_parts.append(f"{hours} часа")
            else:
                time_str_parts.append(f"{hours} часов")

        # Adding minutes to the string if there are any minutes
        if minutes > 0:
            if minutes % 10 == 1 and minutes != 11:
                time_str_parts.append(f"{minutes} минута")
            elif 2 <= minutes % 10 <= 4 and (minutes < 10 or minutes > 20):
                time_str_parts.append(f"{minutes} минуты")
            else:
                time_str_parts.append(f"{minutes} минут")

        # Adding seconds to the string if there are no hours and no minutes
        if hours == 0 and minutes == 0:
            if seconds % 10 == 1 and seconds != 11:
                time_str_parts.append(f"{seconds} секунда")
            elif 2 <= seconds % 10 <= 4 and (seconds < 10 or seconds > 20):
                time_str_parts.append(f"{seconds} секунды")
            else:
                time_str_parts.append(f"{seconds} секунд")

        # Joining the parts of the string considering the presence of hours, minutes, and seconds
        return ', '.join(time_str_parts)
    else:
        return None