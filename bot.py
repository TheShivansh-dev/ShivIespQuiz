# Token and Bot Username
#TOKEN: Final = '7673671830:AAFaDzia9GXrXAz86UEFwzkXGB7OUEFb3xM'
#BOT_USERNAME: Final = '@slizyy_bot'
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
TOKEN: Final = '7673671830:AAFaDzia9GXrXAz86UEFwzkXGB7OUEFb3xM'
BOT_USERNAME: Final = '@slizyy_bot'
ALLOWED_GROUP_IDS = [-1001817635995, -1002114430690]
EXCEL_FILE = 'SYNO5.xlsx'



# Global state variables

quiz_state = {}
correct_users = defaultdict(int)  # Tracks correct answers per user
selected_poll_count = 0 
selected_quizscore_count=0
active_poll=1 # Number of polls user requested
answers_received = defaultdict(int)  # Tracks how many answers have been received for each user
is_quiz_active = False  # New variable to track if a quiz is active
chat_id = None  # Current chat ID for the quiz
selected_time_limit = 10  # Default time limit
unanswered_poll = 0
cancel_active = False
display_chat=0
Quiz_grammar_type =''

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
            options = [row["option1"], row["option2"], row["option3"], row["option4"]]
            random.shuffle(options) 
            poll = {
                "question": row["question"],
                "options": options,
                "correct_answer": row["answer"],
                "meaning": row.get("meaning", "No meaning provided")  # Ensure meaning is loaded
            }
            polls.append(poll)
            
        return polls
    except Exception as e:
        print(e)

async def start_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global is_quiz_active, correct_users, chat_id, unanswered_poll,cancel_active,selected_quizscore_count
        cancel_active = False
        
        reset_used_srnos()
        chat_id = update.message.chat.id
        if chat_id not in ALLOWED_GROUP_IDS:
            try:
                await update.message.reply_text("To Start This Quiz In Your Chat or Group Talk to My Sizzling Owner @V_ale_n_cia and say thanks to me in later")
            except (BadRequest, Forbidden, TimedOut) as e:
                await update.message.chat.send_message("To Start This Quiz In Your Chat or Group Talk to My Sizzling Owner @V_ale_n_cia and say thanks to me in later")
            return
        # Check if a quiz is already active
        if is_quiz_active:
            try:
                await update.message.chat.send_message("A quiz is already running. Please wait for it to finish before starting a new one. or use /cancelquiz")
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
                
            return

        is_quiz_active = True  # Set to True when a new quiz starts
        quiz_state = {}
        selected_quizscore_count=0
        
        correct_users.clear()  # Reset scores at the beginning of each new quiz

        difficulty_keyboard = [
            [InlineKeyboardButton("NDA's English Grammar", callback_data='type_NDA')],
            [InlineKeyboardButton("Random English Grammar", callback_data='type_BASIC')],
        ]
        reply_markup = InlineKeyboardMarkup(difficulty_keyboard)
        try:
            await update.message.chat.send_message('Select the Quiz type:', reply_markup=reply_markup)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
            

async def handle_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        username = query.from_user.username or query.from_user.first_name

        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return

        await query.answer()
        await query.answer()
        difficulty_message = ''

        if query.data == 'type_NDA':
            selected_button_text = f"@{username} selected NDA \n Please wait..."
            try:
                await query.edit_message_text(text=selected_button_text)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
                
            difficulty_keyboard = [
                [InlineKeyboardButton("Synonyms", callback_data='difficulty_synonyms_nda')],
                [InlineKeyboardButton("Active-passive", callback_data='difficulty_acitvepassive_nda')],
                [InlineKeyboardButton("Fill in the Blanks", callback_data='difficulty_fillblank_nda')],
                [InlineKeyboardButton("Idiom-Phrase", callback_data='difficulty_idiomphrase_nda')],
            ]
            

            reply_markup = InlineKeyboardMarkup(difficulty_keyboard)
            try:
                await query.message.chat.send_message('NDA Selected \n Select the Grammar Quiz type:', reply_markup=reply_markup)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
        elif query.data == 'type_BASIC':
            selected_button_text = f"@{username} Selected Basic English Grammar\n Please wait..."
            try:
                await query.edit_message_text(text=selected_button_text)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            difficulty_keyboard = [
                [InlineKeyboardButton("Synonyms", callback_data='difficulty_synonyms')],
                [InlineKeyboardButton("Antonyms", callback_data='difficulty_antonyms')],
                [InlineKeyboardButton("Spelling Correction", callback_data='difficulty_spellcorr')],
                [InlineKeyboardButton("Sentence Correction", callback_data='difficulty_sentcorr')],
            ]
            reply_markup = InlineKeyboardMarkup(difficulty_keyboard)
            
            try:
                await query.message.chat.send_message('Basic Grammar Selected \n Select the Grammar Quiz type:', reply_markup=reply_markup)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
        elif query.data == 'type_AFCAT':
            selected_button_text = f"@{username} Selected AFCAT English Grammar\n Please wait..."
            try:
                await query.edit_message_text(text=selected_button_text)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            difficulty_keyboard = [
                #[InlineKeyboardButton("Synonyms", callback_data='difficulty_synonyms')],
                #[InlineKeyboardButton("Antonyms", callback_data='difficulty_antonyms')],
                [InlineKeyboardButton("Spelling Correction", callback_data='difficulty_spellcorr')],
                #[InlineKeyboardButton("Sentence Correction", callback_data='difficulty_sentcorr')],
            ]
            reply_markup = InlineKeyboardMarkup(difficulty_keyboard)
            
            try:
                await query.message.chat.send_message('AFCAT Grammar Selected \n Select the Grammar Quiz type:', reply_markup=reply_markup)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
        elif query.data == 'type_CGL':
            selected_button_text = f"@{username} Selected SSC CGL English Grammar\n Please wait..."
            try:
                await query.edit_message_text(text=selected_button_text)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            difficulty_keyboard = [
                #[InlineKeyboardButton("Synonyms", callback_data='difficulty_synonyms')],
                [InlineKeyboardButton("Antonyms", callback_data='difficulty_antonyms')],
                #[InlineKeyboardButton("Spelling Correction", callback_data='difficulty_spellcorr')],
                #[InlineKeyboardButton("Sentence Correction", callback_data='difficulty_sentcorr')],
            ]
            reply_markup = InlineKeyboardMarkup(difficulty_keyboard)
            
            try:
                await query.message.chat.send_message('SSC CGL Grammar Selected \n Select the Grammar Quiz type:', reply_markup=reply_markup)
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
        
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
          
# Handle difficulty selection
async def handle_difficulty_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global EXCEL_FILE, Quiz_grammar_type
        query = update.callback_query
        username = query.from_user.username or query.from_user.first_name

        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return

        await query.answer()
        difficulty_message = ''

        if query.data == 'difficulty_synonyms':
            EXCEL_FILE = 'SYNO5.xlsx'
            difficulty_message = "Synonyms"
        elif query.data == 'difficulty_antonyms':
            EXCEL_FILE = 'Antonyms5.xlsx'
            difficulty_message = "Antonyms"
        elif query.data == 'difficulty_spellcorr':
            EXCEL_FILE = 'spellCorrection4.xlsx'
            difficulty_message = "Spelling Correction"
        elif query.data == 'difficulty_sentcorr':
            EXCEL_FILE = 'sentenceCorr4.xlsx'
            difficulty_message = "Sentence Correction"
        #==========================For NDA==============================
        elif query.data == 'difficulty_synonyms_nda':
            EXCEL_FILE = 'NDA_Synonyms1.xlsx'
            difficulty_message = "Synonyms"
        elif query.data == 'difficulty_acitvepassive_nda':
            EXCEL_FILE = 'NDA_active_passive_voice1.xlsx'
            difficulty_message = "Active passive Voice"
        elif query.data == 'difficulty_fillblank_nda':
            EXCEL_FILE = 'NDA_fillblank1.xlsx'
            difficulty_message = "Fill in the blanks"
        elif query.data == 'difficulty_idiomphrase_nda':
            EXCEL_FILE = 'NDA_idiom_phrase1.xlsx'
            difficulty_message = "Idiom Phrase"

        # Edit the message to indicate selection and remove other buttons
        Quiz_grammar_type = difficulty_message
        selected_button_text = f"@{username} Chooses the {difficulty_message} For this round. Please wait... \n It Is Mandatory To Vote On Last Quiz"
        try:
            await query.edit_message_text(text=selected_button_text)
        except (BadRequest, Forbidden, TimedOut) as e:
            print(f"Error canceling the quiz: {e}")
            
            

        # Proceed with time limit selection
        time_keyboard = [
            [InlineKeyboardButton("10 Seconds", callback_data='time_10')],
            [InlineKeyboardButton("15 Seconds", callback_data='time_15')],
            [InlineKeyboardButton("20 Seconds", callback_data='time_20')],
            [InlineKeyboardButton("30 Seconds", callback_data='time_30')],
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
        username = query.from_user.username or query.from_user.first_name

        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return
          
        await query.answer()

        # Map callback data to actual time values
        time_mapping = {
            'time_10': 3,
            'time_15': 15,
            'time_20': 20,
            'time_25': 30
        }
        selected_time_limit = time_mapping.get(query.data, 10)
        selected_time_text = f"@{username} selected {selected_time_limit} second To complete one quiz. "

        # Edit the message to indicate time selection and remove other buttons
        try:
            await query.edit_message_text(text=selected_time_text)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
                

        # Round selection buttons
        keyboard = [
            [InlineKeyboardButton("15 Words", callback_data='15')],
            [InlineKeyboardButton("25 Words", callback_data='25')],
            [InlineKeyboardButton("35 Words", callback_data='35')],
            [InlineKeyboardButton("50 Words", callback_data='50')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.chat.send_message(f"{selected_time_text}. How many rounds?", reply_markup=reply_markup)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
            
async def cancel_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if cancel_active:
            return None

        global is_quiz_active, quiz_state, correct_users
        msg_id = update.message.chat.id
        if msg_id not in ALLOWED_GROUP_IDS:
            try:
                await update.message.reply_text("To Start This Quiz In Your Chat or Group Talk to My Sizzling Owner @V_ale_n_cia and say thanks to me in later")
            except (BadRequest, Forbidden, TimedOut) as e:
                await update.message.chat.send_message("To Start This Quiz In Your Chat or Group Talk to My Sizzling Owner @V_ale_n_cia and say thanks to me in later")
            return
        # Check if the quiz is active
        chat_id = update.message.chat.id
        if not is_quiz_active:
            try:
                await update.message.chat.send_message("No quiz is currently active. \n To start This Quiz Write or Click /startquiz")
            except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            return
        
        # Reset global variables related to the quiz
        is_quiz_active = False
        quiz_state.clear()
        

        # Notify users that the quiz has been canceled
        try:
            await update.message.chat.send_message("The quiz has been canceled and reset. \n To start This Quiz Again Write or Click /startquiz")
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
    except (BadRequest, Forbidden, TimedOut) as e:
                print(e)
# Display quiz results

# Handle button click and start quizzes
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global selected_poll_count,active_poll,cancel_active
        query = update.callback_query
        username = query.from_user.username or query.from_user.first_name
      
        # If quiz is not active, ignore this input
        if not is_quiz_active:
            await query.answer("Please start a new quiz with /startquiz or cancel with /cancelquiz")
            return

        selected_poll_count = 2 #int(query.data)
        active_poll = selected_poll_count
        selected_rounds_text = f"@{username} selected {selected_poll_count} rounds. Starting the quiz..."

        # Edit the message to indicate round selection and remove other buttons
        try:
            await query.edit_message_text(text=selected_rounds_text)
        except (BadRequest, Forbidden, TimedOut) as e:
                print(f"Error canceling the quiz: {e}")
            

        cancel_active = True
        selected_polls = load_quiz_data(EXCEL_FILE,selected_poll_count) 
        selected_polls.append({
            'question': "Do You Want The Result of The Quiz",
            'options': ["yes", "of course", "why not", "yupp"],
            'correct_answer': "yes",
            'meaning': "To Show the result it is mandatory to Click on the Last poll \n Result Will Be Shown within 15 seconds"
        })
        
        
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
                "response_count": 0, 
                "users": [], 
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
        print("enter here 1")
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

            
            return

        # If the poll stops successfully, proceed to get the meaning and other actions
        poll_id = poll_message.poll.id
        if poll_id not in quiz_state:
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

final_poll_responses = {}

# Handle poll answers
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global final_poll_responses,display_chat,selected_quizscore_count
        
        answer: PollAnswer = update.poll_answer
        poll_id = answer.poll_id
        user_id = answer.user.id
        username = answer.user.username or answer.user.first_name or str(user_id)
        #username = answer.user.username  # Get the username of the user
        selected_options = answer.option_ids
        
        # Check if poll ID exists in quiz_state
        if poll_id not in quiz_state:
            return
        
        # Get the quiz data for the poll
        quiz_data = quiz_state[poll_id]
        correct_answer = quiz_data["correct_answer"]
        options = quiz_data["options"]
        curr_poll = quiz_data["poll_number"]
        display_chat = quiz_data["chat_id"]
        quiz_data["response_count"] += 1

        # Get the user's selected answer
        selected_answer = options[selected_options[0]]  # Assuming single choice

        # Store the user's response temporarily (no scoring yet)
        quiz_data["responses"][user_id] = selected_answer
        
        # Track correct answers
        if selected_answer == correct_answer:
            if curr_poll == selected_poll_count+1:
                 print("skip this part")
            else:
                correct_users[username] += 1
                
        if user_id not in quiz_data["users"]:
            quiz_data["users"].append(user_id)
        # If it's the last poll, track user responses specifically for this poll
        if curr_poll == selected_poll_count+1:
            print("equal equal",selected_quizscore_count)
            await asyncio.sleep(5)
            if selected_quizscore_count ==0:
                 print("equal equal 2",selected_quizscore_count)
                 await calculate_scores(update, context)
                 final_poll_responses = {}
                 selected_quizscore_count =1
        
    except (BadRequest, Forbidden, TimedOut) as e:
        print(e)

# Function to calculate scores
async def calculate_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Check if there are any responses in `correct_users` dictionary to display results
        await display_results(update, context)
        
    except (BadRequest, Forbidden, TimedOut) as e:
        print(e)

# Display quiz results, even if only partial or no responses are available
async def display_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_quiz_active,Quiz_grammar_type
    cancel_active = False
    
    if display_chat:
        chatid = display_chat 
    else:
        chat_id = chat_id

    # Check if there are any scores to display
    try:
        result_message = "🎉 Quiz Results: 🥳🥳🥳🥳\n In "+Quiz_grammar_type+" Out Of "+ str(selected_poll_count) + "\n Here are the top scorers of This Round:\n\n"
        
        
        # Sort by the number of correct answers and display each username with their score
        sorted_results = sorted(correct_users.items(), key=lambda x: x[1], reverse=True)
        
        top_10_results = sorted_results[:10]
        
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
        result_message = result_message + "\n To start This Quiz Again Write or Click /startquiz"
        # Send the results message to the chat
        try:
            await context.bot.send_message(chat_id=chatid, text=result_message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    except Exception as e:
        print(f"Error sending message: {e}")

    # Reset quiz active state
    is_quiz_active = False

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "If you need any kind of help or have suggestions, please discuss with my owner From Description"
    )
    await update.message.chat.send_message(help_message)


def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('startquiz', start_game_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_difficulty_selection, pattern='^difficulty_'))
    application.add_handler(CallbackQueryHandler(handle_type_selection, pattern='^type_'))
    application.add_handler(CallbackQueryHandler(handle_time_selection, pattern='^time_'))
    application.add_handler(CallbackQueryHandler(handle_button_click, pattern=r'^\d+$'))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    application.add_handler(CommandHandler('cancelquiz', cancel_quiz_command))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
