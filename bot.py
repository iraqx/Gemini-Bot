from google import genai
from google.genai import types
import telebot
from telegramify_markdown import markdownify as md
import re
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_BOT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

bot = telebot.TeleBot(TELEGRAM_API_KEY)
chat = None
current_token = 0
client = genai.Client(api_key=GOOGLE_API_KEY)
model = "gemini-2.0-flash" # Default
tools = [
    types.Tool(google_search=types.GoogleSearch())
]
generate_content_config = types.GenerateContentConfig(
    temperature=1,
    tools=tools,
    response_mime_type="text/plain",
)
is_processing = False

@bot.message_handler(commands=["start", "new", "model", "token"])
def start(message):
    global chat, model
    if message.text == "/new":
        chat = client.chats.create(model=model, config=generate_content_config)
        bot.reply_to(message, "New chat started")
    if message.text == "/model":
        keyboard = InlineKeyboardMarkup(row_width=1)
        change_button = InlineKeyboardButton("Change", callback_data="change_model")
        keyboard.add(change_button)

        bot.send_message(
            message.chat.id, 
            md(f"Current model \n> {model}"), 
            reply_markup=keyboard, parse_mode="MarkdownV2"
        )
    if message.text == "/token":
        tokens = {model.name.replace("models/", ""): model.input_token_limit for model in client.models.list() if model.input_token_limit}
        token = tokens[model]
        bot.reply_to(message, f"{current_token} / {token}")
    if message.text == "/start":
        bot.reply_to(message, md("""
Welcome to the bot! 

You can interact with me by using the following commands:
    
   - /new: Start a new conversation
   - /model: View and change the current model
   - /token: Check your current token usage

Feel free to ask for assistance or choose the model that best fits your needs. I'm here to help!
"""), parse_mode="MarkdownV2")

@bot.callback_query_handler(func=lambda call: True)
def handle_model_selection(call):
    global model
    if call.data == "change_model":
        models = [model.name.replace("models/", "") for model in client.models.list() if re.match(r"models/gemini-(1\.[5-9]\d*|[2-9]\d*)", model.name)]
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton(model_name, callback_data=model_name) for model_name in models]
        keyboard.add(*buttons)

        bot.edit_message_text(
            "Please choose a model:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
    else:
        model = call.data
        bot.answer_callback_query(call.id, f"Model changed to {model}")
        bot.edit_message_text(
            md(f"Model changed to \n> {model}"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="MarkdownV2"
        )

@bot.message_handler(func=lambda message: True)
def generate(message):
    global chat, is_processing, current_token
    if is_processing:
        return

    is_processing = True

    try:
        if not chat:
            chat = client.chats.create(model=model, config=generate_content_config)

        k = bot.reply_to(message, text="...")
        _message = ""
        chs = ""
        for chunk in chat.send_message_stream(message.text):
            chs += str(chunk)
            try:
                if len(_message + str(chunk.text)) < 4096:
                    _message += str(chunk.text)
                    if _message != k.text and len(_message) > 10:
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=k.message_id,
                            text=md(_message),
                            parse_mode="MarkdownV2"
                        )
                else:
                    _message = ""
                    _message += str(chunk.text)
                    if len(_message) > 10:
                        k = bot.send_message(
                            chat_id=message.chat.id,
                            text=md(_message)
                        )

                time.sleep(1)

            except Exception as p:
                bot.send_message(message.chat.id, f"An error occurred: {str(p)}")
            except genai.errors.ClientError as e:
                if e.status_code == 429:
                    error_details = json.loads(e.response)
                    retry_delay = error_details["details"][1]["retryDelay"]
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=k.message_id,
                        text=f"Rate limit exceeded. Please retry after {retry_delay} seconds.",
                        parse_mode="MarkdownV2"
                    )
                    time.sleep(int(retry_delay))
                    bot.send_message(
                        chat_id=message.chat.id,
                        text="Retrying now, please wait..."
                    )
                    return
            except telebot.apihelper.ApiException as e:
                if e.result == "Too Many Requests":
                    retry_after = int(e.parameters["retry_after"])
                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=k.message_id,
                        text=f"Too many requests. Please retry after {retry_after} seconds.",
                        parse_mode="MarkdownV2"
                    )
                    time.sleep(retry_after)
                    bot.send_message(
                        chat_id=message.chat.id,
                        text="Retrying now, please wait..."
                    )
                    return
    finally:
        current_token = re.findall(r"total_token_count=(\d+)", str(chs))[-1]
        is_processing = False

bot.infinity_polling()
