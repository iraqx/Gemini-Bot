# Telegram Bot with gemini-api

## Features

- **Model Selection**: Change and choose from multiple GenAI models.
- **Content Generation**: Interact with the bot to generate content based on the user's input.
- **Token Management**: Check the current token usage and available tokens for API calls.

## Requirements

- Python 3.8 or higher
- Telegram Bot Token (obtainable from [BotFather](https://core.telegram.org/bots#botfather))
- gemini-api key from [aistudio](https://aistudio.google.com/apikey)

## Setup & Installation

1. Clone the repository:
2. 
```bash
git clone https://github.com/iraqx/Gemini-Bot/
cd Gemini-Bot
```

2. Create a `.env` file or rename `.env.sample` to `.env` and fill in the following information:

   ```bash
   TELEGRAM_BOT_API_KEY=<Your_Telegram_Bot_Token>
   GOOGLE_API_KEY=<Your_GenAI_API_Key>
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the bot:

   ```bash
   python bot.py
   ```

## Commands

- `/start`: Start the bot.
- `/new`: Begin a new conversation with gemini (gemini-2.0-flash default).
- `/model`: View and select a different model for content generation.
- `/token`: Check the current token usage and limit.

## Error Handling

The bot includes error handling for:

- **Rate Limits:** If the API rate limit is exceeded, the bot will notify the user and retry after the appropriate delay.
- **General Errors:** If any general exceptions occur during message processing, the bot will handle them and notify the user.
