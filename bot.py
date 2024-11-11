# Token and Bot Username
#TOKEN: Final = '7256768556:AAGUO6gN-jkyrbceHUkxXaC8yaK1kLEMta0'
#BOT_USERNAME: Final = '@quizall_bot'
#TOKEN: Final = '7007935023:AAENkGaklw6LMJA_sfhVZhnoAgIjW4lDTBc'
#BOT_USERNAME: Final = '@Grovieee_bot'
#ALLOWED_GROUP_IDS = [-1001817635995, -1002114430690]

import os
import random
import pandas as pd
import openpyxl
from typing import Final
from telegram import Update, PollAnswer, Poll, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, PollAnswerHandler, CallbackQueryHandler, ContextTypes
from collections import defaultdict
import asyncio
import time
from telegram.error import Forbidden,BadRequest, TimedOut

# Bot configuration
TOKEN: Final = '7256768556:AAGUO6gN-jkyrbceHUkxXaC8yaK1kLEMta0'
BOT_USERNAME: Final = '@quizall_bot'
ALLOWED_GROUP_IDS = [-1001817635995, -1002114430690]
EXCEL_FILE = 'synonyms_quiz.xlsx'



# Global state variables

quiz_state = {}
correct_users = defaultdict(int)  # Tracks correct answers per user
selected_poll_count = 0  # Number of polls user requested
answers_received = defaultdict(int)  # Tracks how many answers have been received for each user
is_quiz_active = False  # New variable to track if a quiz is active
chat_id = None  # Current chat ID for the quiz
selected_time_limit = 10  # Default time limit
unanswered_poll = 0

# Load quiz data from Excel
used_srnos = set()
def reset_used_srnos():
    global used_srnos
    used_srnos.clear()
def load_quiz_data(file_path, selected_poll_count):
    global used_srnos
    try:
        df = pd.read_excel(file_path)
        
        # Trim extra spaces in each column where cells are strings
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Filter out rows that have already been selected based on `srno`
        unique_rows = df[~df['srno'].isin(used_srnos)]
        
        # If there are fewer unique rows than requested polls, adjust to available rows
        if len(unique_rows) < selected_poll_count:
            print("Not enough unique rows available.")
            selected_poll_count = len(unique_rows)
        
        # Select a random sample of unique rows
        selected_rows = unique_rows.sample(n=selected_poll_count)
        
        # Update used_srnos with newly selected rows
        used_srnos.update(selected_rows['srno'].tolist())
        
        # Process selected rows into polls
        polls = []
        for _, row in selected_rows.iterrows():
            poll = {
                "question": row["qus"],
                "options": [row["option1"], row["option2"], row["option3"], row["option4"]],
                "correct_answer": row["answer"],
                "meaning": row.get("meaning", "No meaning provided")  # Ensure meaning is loaded
            }
            polls.append(poll)
            
        return polls
    except Exception as e:
        print(e)

async def start_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global is_quiz_active, correct_users, chat_id, unanswered_poll
        reset_used_srnos()
        # Check if a quiz is already active
        if is_quiz_active:
            try:
                await update.message.chat.send_message("A quiz is already running. Please wait for it to finish before starting a new one. or use /cancelquiz")
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
                
            return

        is_quiz_active = True  # Set to True when a new quiz starts
        chat_id = update.message.chat.id
        correct_users.clear()  # Reset scores at the beginning of each new quiz

        difficulty_keyboard = [
            [InlineKeyboardButton("Synonyms", callback_data='difficulty_synonyms')],
            [InlineKeyboardButton("Antonyms", callback_data='difficulty_antonyms')],
        ]
        reply_markup = InlineKeyboardMarkup(difficulty_keyboard)
        try:
            await update.message.chat.send_message('Select the type:', reply_markup=reply_markup)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
            

# Handle difficulty selection
async def handle_difficulty_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global EXCEL_FILE
        query = update.callback_query

        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return

        await query.answer()
        difficulty_message = ''

        if query.data == 'difficulty_synonyms':
            EXCEL_FILE = 'synonyms_quiz.xlsx'
            difficulty_message = "Synonyms selected"
        elif query.data == 'difficulty_antonyms':
            EXCEL_FILE = 'antonyms_quiz.xlsx'
            difficulty_message = "Antonyms selected"

        # Edit the message to indicate selection and remove other buttons
        selected_button_text = f"{difficulty_message}. Please wait..."
        try:
            await query.edit_message_text(text=selected_button_text)
        except (BadRequest, Forbidden, TimedOut) as e:
            print(f"Error canceling the quiz: {e}")
            

        # Proceed with time limit selection
        time_keyboard = [
            [InlineKeyboardButton("10 Seconds", callback_data='time_10')],
            [InlineKeyboardButton("15 Seconds", callback_data='time_15')],
            [InlineKeyboardButton("20 Seconds", callback_data='time_20')],
            [InlineKeyboardButton("25 Seconds", callback_data='time_25')],
        ]
        reply_markup = InlineKeyboardMarkup(time_keyboard)
        try:
            await query.message.chat.send_message(f"{difficulty_message}. Select the time limit for each poll:", reply_markup=reply_markup)
        except (BadRequest, Forbidden, TimedOut) as e:
            print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
        


# Handle time selection
async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global selected_time_limit
        query = update.callback_query

        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return

        await query.answer()

        # Map callback data to actual time values
        time_mapping = {
            'time_10': 10,
            'time_15': 15,
            'time_20': 20,
            'time_25': 25
        }
        selected_time_limit = time_mapping.get(query.data, 10)
        selected_time_text = f"Time limit set to {selected_time_limit} seconds."

        # Edit the message to indicate time selection and remove other buttons
        try:
            await query.edit_message_text(text=selected_time_text)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
                

        # Round selection buttons
        keyboard = [
            [InlineKeyboardButton("2 Words", callback_data='2')],
            [InlineKeyboardButton("5 Words", callback_data='5')],
            [InlineKeyboardButton("7 Words", callback_data='7')],
            [InlineKeyboardButton("9 Words", callback_data='9')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.chat.send_message(f"{selected_time_text}. How many rounds?", reply_markup=reply_markup)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
            


# Handle button click and start quizzes
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global selected_poll_count
        query = update.callback_query

        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return

        selected_poll_count = int(query.data)
        selected_rounds_text = f"{selected_poll_count} rounds selected. Starting the quiz..."

        # Edit the message to indicate round selection and remove other buttons
        try:
            await query.edit_message_text(text=selected_rounds_text)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            

        
        selected_polls = load_quiz_data(EXCEL_FILE,selected_poll_count) 
        
        
        for i, poll in enumerate(selected_polls):
            try:
                poll_message = await context.bot.send_poll(
                chat_id=chat_id, 
                question=f"{i+1}/{selected_poll_count}: {poll['question']}",
                options=poll['options'],
                is_anonymous=False,
                allows_multiple_answers=False,
                type=Poll.QUIZ,
                correct_option_id=poll['options'].index(poll['correct_answer'])
                )
            except (BadRequest, Forbidden, TimedOut) as e:
                print(e)

            # Store the poll details in quiz_state
            quiz_state[poll_message.poll.id] = {
                "chat_id": chat_id,
                "question": poll["question"],
                "correct_answer": poll["correct_answer"],
                "options": poll["options"],
                "meaning": poll["meaning"], 
                "responses": {},
                "poll_number": i + 1,
                "expiry_time": time.time() + selected_time_limit,
                "poll_message": poll_message,
            }

            # Start countdown and close poll
            await countdown_and_close_poll(poll_message, selected_time_limit, context)
            await asyncio.sleep(1)
    except (BadRequest, Forbidden, TimedOut) as e:
        print(e) 

# Countdown and close poll after time expires, with sending meaning
async def countdown_and_close_poll(poll_message, countdown_time, context):
    try:
        # Wait for the countdown time to pass
        await asyncio.sleep(countdown_time)
        
        try:
            # Stop the poll after the time limit expires
            await poll_message.stop_poll()
        except Forbidden:
            # If the bot was kicked from the group, reset the quiz state for the chat
            chat_id = poll_message.chat.id
            global is_quiz_active
            is_quiz_active = False  # Mark the quiz as inactive
            quiz_state.clear()  # Clear the quiz state
            correct_users.clear()  # Reset user scores

            # Notify users that the bot was kicked and quiz is reset
            try:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text="The bot was kicked from the group. The quiz has been canceled and reset. You can start a new quiz after re-adding the bot."
                )
            except Exception as e:
                print(f"Error sending message: {e}")

            print(f"Bot was kicked from the group {chat_id}. The quiz has been reset.")
            return

        # If the poll stops successfully, proceed to get the meaning and other actions
        poll_id = poll_message.poll.id
        if poll_id not in quiz_state:
            print(f"Poll with ID {poll_id} not found in quiz state.")
            return

        # Get the quiz data for this poll
        quiz_data = quiz_state[poll_id]
        meaning = quiz_data["meaning"]  # Retrieve the meaning from quiz data
        
        # Send the meaning of the word after the poll ends
        try:
            await context.bot.send_message(chat_id=quiz_data["chat_id"], text=f"Meaning: {meaning}")
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
                
        
        # Add a small delay before proceeding to the next poll
        await asyncio.sleep(1)
    except (BadRequest, Forbidden, TimedOut) as e:
        print(e)

# Handle poll answers
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print("enter here")
        answer: PollAnswer = update.poll_answer
        poll_id = answer.poll_id
        user_id = answer.user.id
        username = answer.user.username  # Get the username of the user
        selected_options = answer.option_ids
        # Check if poll ID exists in quiz_state
        print("enter here 2",answer)
        if poll_id not in quiz_state:
            return

        # Get the quiz data for the poll
        quiz_data = quiz_state[poll_id]
        correct_answer = quiz_data["correct_answer"]
        options = quiz_data["options"]
        
        # Get the user's selected answer
        selected_answer = options[selected_options[0]]  # Assuming single choice
        print("selected answer this",selected_answer)

        # Store the user's response temporarily (no scoring yet)
        quiz_data["responses"][user_id] = selected_answer

        # Track correct answers after user selects the answer, but do not send immediate feedback
        if selected_answer == correct_answer:
            correct_users[username] += 1
        
        # Only calculate scores after the last poll
        #if quiz_data["poll_number"] == selected_poll_count:
        await calculate_scores(update, context)
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
# Function to calculate scores

async def cancel_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global is_quiz_active, quiz_state, correct_users

        # Check if the quiz is active
        if not is_quiz_active:
            try:
                await update.message.chat.send_message("No quiz is currently active.")
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            return

        # Reset global variables related to the quiz
        is_quiz_active = False
        quiz_state.clear()
        correct_users.clear()

        # Notify users that the quiz has been canceled
        try:
            await update.message.chat.send_message("The quiz has been canceled and reset.")
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
# Display quiz results
# Function to calculate scores
async def calculate_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Check if there are any responses in `correct_users` dictionary to display results
        
        await display_results(update, context)
        
    except (BadRequest, Forbidden, TimedOut) as e:
        print(e)

# Display quiz results, even if only partial or no responses are available
async def display_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_quiz_active

    # Check if there are any scores to display
    try:
        result_message = "Quiz Results: 🥳🥳🥳🥳\n"
        # Sort by the number of correct answers and display each username with their score
        sorted_results = sorted(correct_users.items(), key=lambda x: x[1], reverse=True)
        
        top_10_results = sorted_results[:10]
        print(top_10_results)
        if not top_10_results:
            result_message = "No scores received. No one answered correctly."
        else:
            p = 1
            for username, score in top_10_results:
                if p == 1:
                    result_message += f"🏆)- @{username}: {score}\n"
                elif p == 2:
                    result_message += f"🥈)- @{username}: {score}\n"
                elif p == 3:
                    result_message += f"🥉)- @{username}: {score}\n"
                else:
                    result_message += f"🧌{p})- @{username}: {score}\n"
                p += 1

        # Send the results message to the chat
        try:
            await context.bot.send_message(chat_id=chat_id, text=result_message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    except Exception as e:
        print(f"Error sending message: {e}")

    # Reset quiz active state
    is_quiz_active = False

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('startquiz', start_game_command))
    application.add_handler(CallbackQueryHandler(handle_difficulty_selection, pattern='^difficulty_'))
    application.add_handler(CallbackQueryHandler(handle_time_selection, pattern='^time_'))
    application.add_handler(CallbackQueryHandler(handle_button_click, pattern=r'^\d+$'))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    application.add_handler(CommandHandler('cancelquiz', cancel_quiz_command))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
